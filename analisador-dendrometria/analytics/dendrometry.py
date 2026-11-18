"""Cálculos dendrométricos: DAP, alturas, área seccional, volumes, rankings e
distribuição diamétrica.

Política única de elegibilidade de DAP (aplicada a TODOS os indicadores de DAP):
  elegível ⇔ registro identificável (Parcela + Árvore válidos)
            ∧ status do DAP = MEDIDO (número finito, > 0)
            ∧ medição não duplicada (Parcela + Árvore + Data)
            ∧ (DAP ≤ 300 cm  ∨  opção explícita "incluir extremos")
O limite de 300 cm é REGRA LEGADA NÃO VALIDADA METODOLOGICAMENTE.
"""
from __future__ import annotations

import math
from collections import Counter

import numpy as np
import pandas as pd

from .canonicalization import HEIGHT_COLUMNS, LABEL, natural_key
from .observations import extract_stems
from .quality import DAP_LIMITE_LEGADO_CM, MED_EXTREMO, MED_MEDIDO
from .results import (
    BLOQ_METODOLOGIA,
    INDISPONIVEL,
    TOLERANCIAS,
    VALIDO,
    VALIDO_RESSALVA,
    Indicator,
    Metodologia,
    bloqueado,
    cobertura,
)

QUARTIL_METODO = "linear"  # Hyndman & Fan tipo 7 (padrão do NumPy e do Excel QUARTIL.INC)

# Equação de Spurr — Jorge (1982), Mata Atlântica do norte do ES e sul da BA
# (referência: Formulas_Dendrometricas_PTMC_Camila.docx)
SPURR_B0 = 0.106531813
SPURR_B1 = 5.3372e-5


# ------------------------------------------------------------ fórmulas
def area_seccional_m2(dap_cm: float) -> float:
    """g = π · DAP² / 40000  (DAP em cm → g em m²)."""
    return math.pi * dap_cm * dap_cm / 40000.0


def volume_cilindrico_m3(dap_cm: float, altura_m: float) -> float:
    """v = g · h (cilindro, sem fator de forma)."""
    return area_seccional_m2(dap_cm) * altura_m


def volume_spurr_m3(dap_cm: float, hc_m: float) -> float:
    """Vc = b0 + b1 · DAP² · HC (Spurr; coeficientes de Jorge, 1982)."""
    return SPURR_B0 + SPURR_B1 * dap_cm * dap_cm * hc_m


def mean(xs: list[float]) -> float:
    return math.fsum(xs) / len(xs)


def sample_std(xs: list[float]) -> float:
    """Desvio-padrão amostral (n−1) pelo algoritmo de duas passagens (estável)."""
    m = mean(xs)
    return math.sqrt(math.fsum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def quantile(xs: list[float], q: float) -> float:
    return float(np.quantile(np.asarray(xs, dtype=float), q, method=QUARTIL_METODO))


# ------------------------------------------------------------ elegibilidade
def potential(df: pd.DataFrame) -> pd.DataFrame:
    """Registros que poderiam ter medição: identificáveis e não anotação de parcela."""
    if df.empty:
        return df
    return df[df["identificavel"] & ~df["anotacao_parcela"]]


def dap_eligibility(df: pd.DataFrame, incluir_extremos: bool = False) -> pd.DataFrame:
    pot = potential(df).copy()
    reasons = []
    for st, mot, dupm in zip(pot["dap_cm_status"], pot["dap_cm_motivo"], pot["n_registros_medicao"]):
        if dupm is not None and not pd.isna(dupm) and dupm > 1:
            reasons.append("duplicidade Parcela + Árvore + Data (requer revisão)")
        elif st == MED_MEDIDO:
            reasons.append("")
        elif st == MED_EXTREMO:
            reasons.append("" if incluir_extremos else
                           f"DAP > {DAP_LIMITE_LEGADO_CM:g} cm — elegibilidade bloqueada até decisão metodológica")
        else:
            reasons.append(f"DAP {st.lower()}: {mot}" if mot else f"DAP {st.lower()}")
    pot["dap_elegivel"] = [r == "" for r in reasons]
    pot["dap_motivo_exclusao"] = reasons
    return pot


def height_eligibility(df: pd.DataFrame, col: str) -> pd.DataFrame:
    pot = potential(df).copy()
    reasons = []
    for st, mot, dupm in zip(pot[f"{col}_status"], pot[f"{col}_motivo"], pot["n_registros_medicao"]):
        if dupm is not None and not pd.isna(dupm) and dupm > 1:
            reasons.append("duplicidade Parcela + Árvore + Data (requer revisão)")
        elif st == MED_MEDIDO:
            reasons.append("")
        else:
            reasons.append(f"{LABEL[col].split(' ')[0]} {st.lower()}: {mot}" if mot else st.lower())
    pot[f"{col}_elegivel"] = [r == "" for r in reasons]
    pot[f"{col}_motivo_exclusao"] = reasons
    return pot


def _reasons(series: pd.Series) -> dict[str, int]:
    return dict(sorted(Counter(r for r in series if r).items(), key=lambda kv: -kv[1]))


# ------------------------------------------------------------ indicadores descritivos
def _describe(prefix: str, variavel: str, unidade: str, values: list[float], potencial_n: int,
              motivos: dict[str, int], tol_key: str, obs_extra: list[str], filtrado: bool,
              rotulo_media: str) -> list[Indicator]:
    n = len(values)
    excl = potencial_n - n
    cov = cobertura(n, potencial_n)
    status = VALIDO_RESSALVA if obs_extra else VALIDO
    den = f"{n} valores elegíveis de {potencial_n} registros potenciais"
    tol = TOLERANCIAS[tol_key]
    base = dict(unidade=unidade, denominador=den, quantidade_potencial=potencial_n, quantidade_elegivel=n,
                quantidade_excluida=excl, motivos_exclusao=motivos, cobertura=cov, filtrado=filtrado,
                tolerancia=f"atol={tol.atol:g}, rtol={tol.rtol:g}")

    def ind(id_, nome, fn, formula, minimo=1, tol_override=None, unidade_override=None, extra=None):
        obs_ = list(obs_extra) + (extra or [])
        kw = dict(base)
        if tol_override:
            t = TOLERANCIAS[tol_override]
            kw["tolerancia"] = f"atol={t.atol:g}, rtol={t.rtol:g}"
        if unidade_override is not None:
            kw["unidade"] = unidade_override
        if n < minimo:
            return Indicator(id=id_, nome=nome, valor=None, status=INDISPONIVEL, formula=formula,
                             observacoes=[f"Requer ao menos {minimo} valor(es) elegível(is); há {n}."] + obs_, **kw)
        try:
            v = fn()
        except ZeroDivisionError:
            return Indicator(id=id_, nome=nome, valor=None, status=INDISPONIVEL, formula=formula,
                             observacoes=["Divisão por zero (média igual a zero)."] + obs_, **kw)
        return Indicator(id=id_, nome=nome, valor=v, status=status, formula=formula, observacoes=obs_, **kw)

    def cv():
        m = mean(values)
        if m == 0:
            raise ZeroDivisionError
        return sample_std(values) / m * 100.0

    return [
        ind(f"{prefix}_n", f"Contagem de {variavel} elegíveis", lambda: n, "n = nº de valores elegíveis", minimo=0,
            tol_override="contagem", unidade_override="valores"),
        ind(f"{prefix}_media", rotulo_media, lambda: mean(values), "x̄ = Σxᵢ / n (soma compensada, math.fsum)"),
        ind(f"{prefix}_mediana", f"Mediana de {variavel}", lambda: quantile(values, 0.5),
            "valor central da amostra ordenada"),
        ind(f"{prefix}_min", f"Mínimo de {variavel}", lambda: min(values), "min(xᵢ)"),
        ind(f"{prefix}_max", f"Máximo de {variavel}", lambda: max(values), "max(xᵢ)"),
        ind(f"{prefix}_q1", f"1º quartil de {variavel}", lambda: quantile(values, 0.25),
            "Q1, interpolação linear (Hyndman & Fan tipo 7)"),
        ind(f"{prefix}_q3", f"3º quartil de {variavel}", lambda: quantile(values, 0.75),
            "Q3, interpolação linear (Hyndman & Fan tipo 7)"),
        ind(f"{prefix}_dp", f"Desvio-padrão amostral de {variavel}", lambda: sample_std(values),
            "s = √[Σ(xᵢ − x̄)² / (n − 1)] (duas passagens)", minimo=2, tol_override="dispersao"),
        ind(f"{prefix}_cv", f"Coeficiente de variação de {variavel}", cv, "CV = s / x̄ × 100", minimo=2,
            tol_override="dispersao", unidade_override="%"),
    ]


def dap_indicators(df: pd.DataFrame, incluir_extremos: bool = False, filtrado: bool = False) -> list[Indicator]:
    el = dap_eligibility(df, incluir_extremos)
    vals = el.loc[el["dap_elegivel"], "dap_cm"].astype(float).tolist()
    obs_extra = []
    n_ext = int((el["dap_cm_status"] == MED_EXTREMO).sum()) if len(el) else 0
    if n_ext:
        obs_extra.append(
            f"{n_ext} DAP(s) > {DAP_LIMITE_LEGADO_CM:g} cm (regra legada não validada) "
            + ("INCLUÍDO(S) por opção explícita." if incluir_extremos else "fora do cálculo até decisão metodológica.")
        )
    return _describe("dap", "DAP", "cm", vals, len(el), _reasons(el["dap_motivo_exclusao"]), "dap_cm",
                     obs_extra, filtrado, "Média aritmética do DAP")


def height_indicators(df: pd.DataFrame, filtrado: bool = False) -> dict[str, list[Indicator]]:
    out = {}
    for col in HEIGHT_COLUMNS:
        var = LABEL[col].split(" ")[0]
        if potential(df).empty or (df[f"{col}_status"] == "NÃO COLETADO").all():
            out[col] = [bloqueado(f"{col}_media", f"Média de {var}", "m", "Coluna não mapeada no arquivo.",
                                  status=INDISPONIVEL, filtrado=filtrado)]
            continue
        el = height_eligibility(df, col)
        vals = el.loc[el[f"{col}_elegivel"], col].astype(float).tolist()
        rot = "Altura total média (HT)" if col == "ht_m" else f"Média de {var}"
        n_ext = int((el[f"{col}_status"] == MED_EXTREMO).sum())
        extra = [f"{n_ext} valor(es) de {var} acima do limite físico de 120 m (maior árvore viva medida ≈ 116 m), fora do cálculo até revisão."] \
            if n_ext else []
        inds = _describe(col.replace("_m", ""), var, "m", vals, len(el), _reasons(el[f"{col}_motivo_exclusao"]),
                         "altura_m", extra, filtrado, rot)
        aus = int((el[f"{col}_status"] == "AUSENTE").sum())
        inds.append(Indicator(
            id=f"{col}_ausentes", nome=f"{var} ausentes", valor=aus, unidade="registros",
            denominador=f"{aus} de {len(el)} registros potenciais", quantidade_potencial=len(el),
            quantidade_elegivel=len(vals), quantidade_excluida=len(el) - len(vals),
            cobertura=cobertura(len(vals), len(el)), formula="contagem de status AUSENTE", filtrado=filtrado,
        ))
        out[col] = inds
    return out


def crown_table(df: pd.DataFrame) -> pd.DataFrame:
    """Copa por indivíduo: comprimento = HT − HESGCOPA; proporção = comprimento / HT.

    HESGCOPA = altura do solo até o início da copa; HT = altura do solo até o ápice
    (definições do projeto, referencias/WhatsApp Image 2026-11-17 17.35.09).
    Só entram indivíduos com os dois valores elegíveis e 0 ≤ HESGCOPA ≤ HT; nada é corrigido.
    """
    ht = height_eligibility(df, "ht_m")
    hc = height_eligibility(df, "hesgcopa_m")
    t = ht[["ht_m", "ht_m_elegivel", "ht_m_motivo_exclusao"]].copy()
    t["hesgcopa_m"] = hc["hesgcopa_m"]
    t["hesgcopa_elegivel"] = hc["hesgcopa_m_elegivel"]
    t["hesgcopa_motivo"] = hc["hesgcopa_m_motivo_exclusao"]
    ok = t["ht_m_elegivel"] & t["hesgcopa_elegivel"]
    t["copa_elegivel"] = False
    t["copa_motivo_exclusao"] = ""
    t["comprimento_copa_m"] = float("nan")
    t["proporcao_copa"] = float("nan")
    for i in t.index:
        if not ok[i]:
            faltas = [m for m in (t.at[i, "ht_m_motivo_exclusao"], t.at[i, "hesgcopa_motivo"]) if m]
            t.at[i, "copa_motivo_exclusao"] = "; ".join(faltas) or "HT ou HESGCOPA indisponível"
        elif t.at[i, "hesgcopa_m"] > t.at[i, "ht_m"] or t.at[i, "ht_m"] <= 0:
            t.at[i, "copa_motivo_exclusao"] = "HESGCOPA maior que HT (incoerente; requer revisão)"
        else:
            c = float(t.at[i, "ht_m"]) - float(t.at[i, "hesgcopa_m"])
            t.at[i, "copa_elegivel"] = True
            t.at[i, "comprimento_copa_m"] = c
            t.at[i, "proporcao_copa"] = c / float(t.at[i, "ht_m"]) * 100.0
    return t


def crown_indicators(df: pd.DataFrame, filtrado: bool = False) -> list[Indicator]:
    if potential(df).empty or (df["ht_m_status"] == "NÃO COLETADO").all() \
            or (df["hesgcopa_m_status"] == "NÃO COLETADO").all():
        return [bloqueado("copa_comprimento_media", "Comprimento médio de copa", "m",
                          "Requer as colunas HT e HESGCOPA mapeadas.", status=INDISPONIVEL, filtrado=filtrado)]
    t = crown_table(df)
    el = t[t["copa_elegivel"]]
    n, pot = len(el), len(t)
    ress = ["Comprimento de copa = HT − HESGCOPA (início da copa até o ápice). A nota (*) da definição de "
            "HESGCOPA não foi fornecida; indicador descritivo, sem decisão sobre critério de copa."]
    base = dict(denominador=f"{n} indivíduos com HT e HESGCOPA elegíveis de {pot} potenciais",
                quantidade_potencial=pot, quantidade_elegivel=n, quantidade_excluida=pot - n,
                motivos_exclusao=_reasons(t["copa_motivo_exclusao"]), cobertura=cobertura(n, pot),
                filtrado=filtrado, status=VALIDO_RESSALVA, observacoes=ress)
    if n == 0:
        return [Indicator(id="copa_comprimento_media", nome="Comprimento médio de copa", valor=None, unidade="m",
                          formula="média de (HT − HESGCOPA)", **{**base, "status": INDISPONIVEL})]
    return [
        Indicator(id="copa_comprimento_media", nome="Comprimento médio de copa", valor=mean(el["comprimento_copa_m"].tolist()),
                  unidade="m", formula="média de (HT − HESGCOPA)", **base),
        Indicator(id="copa_proporcao_media", nome="Proporção média de copa", valor=mean(el["proporcao_copa"].tolist()),
                  unidade="%", formula="média de (HT − HESGCOPA) / HT × 100", **base),
    ]


# ------------------------------------------------------------ área seccional (basal)
def individual_table(df: pd.DataFrame, incluir_extremos: bool = False) -> pd.DataFrame:
    """Tabela por registro de indivíduo com g, volumes e elegibilidades."""
    el = dap_eligibility(df, incluir_extremos)
    for col in HEIGHT_COLUMNS:
        h = height_eligibility(df, col)
        el[f"{col}_elegivel"] = h[f"{col}_elegivel"].values
        el[f"{col}_motivo_exclusao"] = h[f"{col}_motivo_exclusao"].values
    el["g_m2"] = [area_seccional_m2(d) if ok else np.nan for d, ok in zip(el["dap_cm"], el["dap_elegivel"])]
    el["v_cil_m3"] = [volume_cilindrico_m3(d, h) if a and b else np.nan
                      for d, h, a, b in zip(el["dap_cm"], el["ht_m"], el["dap_elegivel"], el["ht_m_elegivel"])]
    el["v_spurr_m3"] = [volume_spurr_m3(d, h) if a and b else np.nan
                        for d, h, a, b in zip(el["dap_cm"], el["hc_m"], el["dap_elegivel"], el["hc_m_elegivel"])]
    _multifuste(el)
    return el


MF_EXTRAIDO = "FUSTES EXTRAÍDOS"
MF_REVISAO = "REVISÃO HUMANA"


def dap_equivalente_cm(fustes: list[float]) -> float:
    """Diâmetro do fuste único de mesma área seccional: d_eq = √(Σ dᵢ²) (Stewart & Salazar, 1992)."""
    return math.sqrt(math.fsum(d * d for d in fustes))


def _multifuste(el: pd.DataFrame) -> None:
    """Regra de Finger (1992), adotada no Manual de Dendrometria da CEPLAC: tronco bifurcado abaixo de
    1,30 m tem cada fuste medido como se fosse uma árvore. A área seccional do indivíduo é a soma das
    áreas dos fustes (gᵢ = Σ π·dⱼ²/40000) e o DAP equivalente é √(Σ dⱼ²).
    Só usa fustes extraídos por padrão estrutural (quantidade declarada = valores listados)."""
    st, mot, fus, deq, gm = [], [], [], [], []
    cols = zip(el["observacao"], el.get("mencao_multifuste", pd.Series(False, index=el.index)),
               el.get("obs_lista_diametros", pd.Series(False, index=el.index)), el["dap_cm"], el["dap_cm_status"],
               el["dap_cm_motivo"], el["n_registros_medicao"], el.get("mencao_morte", pd.Series(False, index=el.index)),
               el["dap_elegivel"])
    for obs_, men, lista, dap, dst, dmot, dupm, morte, dap_ok in cols:
        if not (men or lista):
            st.append(""); mot.append(""); fus.append(None); deq.append(np.nan); gm.append(np.nan)
            continue
        f = extract_stems(obs_)
        motivo = f.motivo
        ok = f.diametros_cm is not None
        if ok and dupm is not None and not pd.isna(dupm) and dupm > 1:
            ok, motivo = False, "duplicidade Parcela + Árvore + Data (requer revisão)"
        if ok and morte:
            ok, motivo = False, "observação menciona morte (estado vital requer revisão)"
        if ok and dst == MED_MEDIDO and not any(abs(dap - d) <= 0.05 for d in f.diametros_cm):
            ok, motivo = False, (f"DAP da coluna ({dap:g} cm) não corresponde a nenhum fuste listado "
                                 f"({', '.join(f'{d:g}' for d in f.diametros_cm)}) — revisão humana")
        if ok:
            st.append(MF_EXTRAIDO); mot.append(motivo); fus.append(f.diametros_cm)
            deq.append(dap_equivalente_cm(f.diametros_cm))
            gm.append(math.fsum(area_seccional_m2(d) for d in f.diametros_cm))
        else:
            if dap_ok:
                motivo += "; mantido o DAP da coluna (fuste único)"
            st.append(MF_REVISAO); mot.append(motivo); fus.append(f.diametros_cm)
            deq.append(np.nan); gm.append(np.nan)
    el["multifuste_status"] = st
    el["multifuste_motivo"] = mot
    el["fustes_cm"] = fus
    el["dap_equivalente_cm"] = deq
    el["g_multifuste_m2"] = gm
    # Área seccional do indivíduo incluindo multifustes: Σg dos fustes quando extraídos; senão g do DAP elegível.
    el["g_individuo_m2"] = [m if not pd.isna(m) else (g if ok else np.nan)
                            for m, g, ok in zip(el["g_multifuste_m2"], el["g_m2"], el["dap_elegivel"])]


def multifuste_table(df: pd.DataFrame, incluir_extremos: bool = False) -> pd.DataFrame:
    el = individual_table(df, incluir_extremos)
    if el.empty:
        return pd.DataFrame()
    sub = el[el["multifuste_status"] != ""]
    if sub.empty:
        return pd.DataFrame()
    out = pd.DataFrame({
        "linha": sub["_linha"], "parcela": sub["parcela"], "árvore": sub["arvore"], "espécie": sub["especie"],
        "DAP (coluna, original)": sub["dap_cm_orig"].map(lambda v: "" if v is None or v != v else str(v)),
        "situação": sub["multifuste_status"], "motivo": sub["multifuste_motivo"],
        "fustes (cm)": sub["fustes_cm"].map(lambda v: "" if v is None else "; ".join(f"{d:g}" for d in v)),
        "nº de fustes": sub["fustes_cm"].map(lambda v: len(v) if v else None),
        "DAP equivalente (cm)": sub["dap_equivalente_cm"], "Σ g dos fustes (m²)": sub["g_multifuste_m2"],
        "observação (original)": sub["observacao"],
    })
    return out.sort_values("linha").reset_index(drop=True)


def multifuste_indicator(df: pd.DataFrame, incluir_extremos: bool = False, filtrado: bool = False) -> Indicator:
    el = individual_table(df, incluir_extremos)
    formula = "G' = Σ gᵢ ;  gᵢ = Σⱼ π·dᵢⱼ²/40000 (multifuste)  ou  π·DAPᵢ²/40000 (fuste único)"
    if el.empty:
        return bloqueado("g_total_multifuste", "Área basal total incluindo multifustes", "m²", "Sem registros.",
                         status=INDISPONIVEL, formula=formula, filtrado=filtrado)
    gi = el["g_individuo_m2"].dropna().tolist()
    pot, n = len(el), len(gi)
    n_mf = int((el["multifuste_status"] == MF_EXTRAIDO).sum())
    n_rev = int((el["multifuste_status"] == MF_REVISAO).sum())
    motivos = Counter(r for r, g in zip(el["dap_motivo_exclusao"], el["g_individuo_m2"]) if pd.isna(g) and r)
    tol = TOLERANCIAS["area_basal_m2"]
    if n == 0:
        return bloqueado("g_total_multifuste", "Área basal total incluindo multifustes", "m²", "Nenhum indivíduo elegível.",
                         status=INDISPONIVEL, formula=formula, filtrado=filtrado)
    return Indicator(
        id="g_total_multifuste", nome="Área basal total incluindo multifustes", valor=math.fsum(gi), unidade="m²",
        denominador=f"{n} indivíduos elegíveis de {pot} potenciais ({n_mf} multifustes com fustes extraídos)",
        quantidade_potencial=pot, quantidade_elegivel=n, quantidade_excluida=pot - n,
        motivos_exclusao=dict(motivos.most_common()), cobertura=cobertura(n, pot), status=VALIDO_RESSALVA,
        formula=formula, filtrado=filtrado, tolerancia=f"atol={tol.atol:g}, rtol={tol.rtol:g}",
        versao_metodologica="Finger (1992) via Manual CEPLAC; Stewart & Salazar (1992)",
        observacoes=[f"Regra de Finger (1992), adotada no Manual de Dendrometria da CEPLAC: fustes bifurcados abaixo "
                     f"de 1,30 m são medidos separadamente; a área seccional do indivíduo é a soma das áreas dos fustes.",
                     f"{n_mf} indivíduos com fustes extraídos da observação por padrão estrutural "
                     f"(quantidade declarada = valores listados); {n_rev} indícios de multifuste ficaram para revisão humana.",
                     "Complementa — não substitui — a 'Área basal total (G)', que usa apenas o DAP da coluna."])



def parcelas_inventariadas(df: pd.DataFrame) -> list:
    """Parcelas identificadas: registros identificáveis ou anotações de parcela (ex.: 'NÃO TEM ÁRVORES')."""
    if df.empty:
        return []
    m = (df["parcela"].notna() & ~df["_bloqueante"]) | df["anotacao_parcela"]
    return sorted(df.loc[m, "parcela"].dropna().unique(), key=natural_key)


def _g_por_hectare(df: pd.DataFrame, el: pd.DataFrame, met: Metodologia | None, filtrado: bool,
                   common: dict) -> list[Indicator]:
    formula = "ABₕₐ = G / A ;  A = Σ aⱼ (ha) ;  F = 1 / aⱼ"
    if met is None or met.area_parcela is None:
        return [bloqueado("g_ha", "Área basal por hectare", "m²/ha",
                          "Sem área da parcela, unidade de área, desenho amostral e fator de expansão. "
                          "Fórmula de referência (ABha = G / A) documentada, mas não aplicável. "
                          "Informe área e desenho amostral em Parâmetros para liberar.",
                          formula=formula, filtrado=filtrado)]
    if not met.desenho_amostral.strip():
        return [bloqueado("g_ha", "Área basal por hectare", "m²/ha",
                          "Área da parcela informada, mas o desenho amostral não foi descrito. "
                          "A extrapolação por hectare pressupõe amostragem adequada e área conhecida.",
                          formula=formula, filtrado=filtrado)]
    parcelas = parcelas_inventariadas(df)
    if not parcelas:
        return [bloqueado("g_ha", "Área basal por hectare", "m²/ha", "Nenhuma parcela identificada.",
                          status=INDISPONIVEL, formula=formula, filtrado=filtrado)]
    areas = {p: met.area_ha(p) for p in parcelas}
    com_area = [p for p, a in areas.items() if a is not None]
    sem_area = [p for p, a in areas.items() if a is None]
    if not com_area:
        return [bloqueado("g_ha", "Área basal por hectare", "m²/ha",
                          "Nenhuma parcela do arquivo tem área informada ou válida (> 0). Nenhum valor é assumido.",
                          formula=formula, filtrado=filtrado)]
    # Parcelas sem área ficam fora do numerador E do denominador (G e A sobre o mesmo conjunto).
    a_total = math.fsum(areas[p] for p in com_area)
    sel = el["parcela"].isin(com_area) & el["dap_elegivel"]
    g = math.fsum(el.loc[sel, "g_m2"].tolist())
    pot = int(el["parcela"].isin(com_area).sum())
    n_el = int(sel.sum())
    cov = cobertura(n_el, pot)
    notas = [f"Área e desenho amostral (fonte: {met.fonte}): {met.desenho_amostral.strip()}",
             f"A = soma das áreas de {len(com_area)} parcelas (inclusive as anotadas sem árvores).",
             "Indivíduos sem DAP elegível não contribuem para G: o valor por hectare é um limite inferior"
             + (f" (cobertura de DAP nessas parcelas {cov * 100:.1f}%)." if cov is not None else ".")]
    motivos = dict(common["motivos_exclusao"])
    if sem_area:
        notas.append(f"{len(sem_area)} parcela(s) sem área conhecida excluída(s) de G e de A: "
                     + ", ".join(map(str, sem_area[:15])) + ("…" if len(sem_area) > 15 else "") + ".")
        motivos = {f"parcela sem área conhecida ({len(sem_area)} parcelas)":
                   int((~el["parcela"].isin(com_area)).sum()), **motivos}
    if met.sensibilidade_m2:
        alt = "; ".join(f"{m2:g} m² → {g / (len(com_area) * m2 / 10000.0):.2f}".replace(".", ",") + " m²/ha"
                        for m2 in met.sensibilidade_m2)
        notas.append("Sensibilidade à convenção de área (mesmas parcelas e mesmo G): " + alt +
                     ". 100 m² = polígono entre as árvores externas (área citada por Barazetti et al., 2011); "
                     "196 m² = área útil acrescida do corredor de 4 m entre parcelas. Adotada a área útil "
                     "(nº de plantas × espaçamento), convenção de experimentos de plantio. Confirmar em campo.")
        notas.append("Parcelas pequenas (≈ 0,014 ha) com árvores de grande porte geram valores por parcela muito "
                     "altos (efeito de borda: copas e raízes ocupam corredores); interpretar o valor por parcela com cautela.")
    tol = TOLERANCIAS["area_basal_m2"]
    a_txt = f"{a_total:.6g}".replace(".", ",")
    fonte = "literatura" if met.fonte.startswith("literatura") else "decisão do usuário (execução)"
    kw = {**common, "denominador": f"A = {a_txt} ha em {len(com_area)} parcelas; "
                                     f"{n_el} DAPs elegíveis de {pot} potenciais nessas parcelas",
          "quantidade_elegivel": n_el, "quantidade_excluida": common["quantidade_potencial"] - n_el,
          "cobertura": cov, "motivos_exclusao": motivos,
          "tolerancia": f"atol={tol.atol:g}, rtol={tol.rtol:g}", "versao_metodologica": fonte}
    return [
        Indicator(id="area_amostrada", nome="Área das parcelas com área conhecida (A)", valor=a_total, unidade="ha",
                  formula="A = Σ aⱼ", status=VALIDO_RESSALVA,
                  observacoes=[f"Soma das áreas de {len(com_area)} parcelas."], **kw),
        Indicator(id="g_ha", nome="Área basal por hectare", valor=g / a_total, unidade="m²/ha", formula=formula,
                  status=VALIDO_RESSALVA, observacoes=notas, **kw),
    ]


def _dg(el: pd.DataFrame, filtrado: bool, common: dict) -> Indicator:
    """Diâmetro quadrático médio: diâmetro da árvore de área seccional média.
    Definição padrão da literatura (Finger, 1992; Soares, Paula Neto & Souza, 2011;
    Machado & Figueiredo Filho, 2006). Calculado sobre a mesma política de elegibilidade do DAP."""
    formula = "dg = √(Σ DAPᵢ² / n) = √(40000 · Ḡ / π)"
    d = el.loc[el["dap_elegivel"], "dap_cm"].tolist()
    tol = TOLERANCIAS["dap_cm"]
    return Indicator(id="dg", nome="Diâmetro quadrático médio (dg)", valor=math.sqrt(math.fsum(x * x for x in d) / len(d)),
                     unidade="cm", formula=formula, status=VALIDO,
                     observacoes=["Definição da literatura: diâmetro da árvore de área seccional média "
                                  "(Finger, 1992; Soares, Paula Neto & Souza, 2011).",
                                  "Não equivale à média aritmética do DAP (dg ≥ média aritmética). Qual dos dois será o "
                                  "'diâmetro médio' de referência do projeto permanece decisão M5 da equipe."],
                     **{**common, "tolerancia": f"atol={tol.atol:g}, rtol={tol.rtol:g}",
                        "versao_metodologica": "literatura (Finger, 1992; Soares et al., 2011)"})


def basal_area_indicators(df: pd.DataFrame, incluir_extremos: bool = False, filtrado: bool = False,
                          metodologia: Metodologia | None = None) -> list[Indicator]:
    el = individual_table(df, incluir_extremos)
    g = el.loc[el["dap_elegivel"], "g_m2"].tolist()
    n, pot = len(g), len(el)
    motivos = _reasons(el["dap_motivo_exclusao"])
    cov = cobertura(n, pot)
    tol = TOLERANCIAS["area_basal_m2"]
    common = dict(denominador=f"{n} indivíduos elegíveis de {pot} potenciais", quantidade_potencial=pot,
                  quantidade_elegivel=n, quantidade_excluida=pot - n, motivos_exclusao=motivos, cobertura=cov,
                  filtrado=filtrado, tolerancia=f"atol={tol.atol:g}, rtol={tol.rtol:g}")
    obs_ = ["Área seccional à altura do peito (g); a soma é a área basal absoluta da amostra (não por hectare)."]
    if n == 0:
        st = dict(status=INDISPONIVEL, valor=None)
        return [Indicator(id="g_total", nome="Área basal total (G)", unidade="m²", formula="G = Σ gᵢ",
                          observacoes=["Nenhum DAP elegível."], **st, **common),
                Indicator(id="g_media", nome="Área basal média por indivíduo elegível", unidade="m²",
                          formula="Ḡ = G / n", observacoes=["Nenhum DAP elegível."], **st, **common),
                Indicator(id="g_max", nome="Maior área basal individual", unidade="m²", formula="max(gᵢ)",
                          observacoes=["Nenhum DAP elegível."], **st, **common),
                *(_g_por_hectare(df, el, metodologia, filtrado, common)
                  if metodologia is None or not metodologia.por_hectare_informado else
                  [bloqueado("g_ha", "Área basal por hectare", "m²/ha", "Nenhum DAP elegível.",
                             status=INDISPONIVEL, filtrado=filtrado)]),
                bloqueado("dg", "Diâmetro quadrático médio (dg)", "cm", "Nenhum DAP elegível.", status=INDISPONIVEL,
                          filtrado=filtrado)]
    return [
        Indicator(id="g_total", nome="Área basal total (G)", valor=math.fsum(g), unidade="m²",
                  formula="G = Σ gᵢ ;  gᵢ = π · DAPᵢ² / 40000", observacoes=obs_, **common),
        Indicator(id="g_media", nome="Área basal média por indivíduo elegível", valor=math.fsum(g) / n, unidade="m²",
                  formula="Ḡ = G / n", **common),
        Indicator(id="g_max", nome="Maior área basal individual", valor=max(g), unidade="m²", formula="max(gᵢ)",
                  **common),
        *_g_por_hectare(df, el, metodologia, filtrado, common),
        _dg(el, filtrado, common),
    ]


def volume_indicators(df: pd.DataFrame, incluir_extremos: bool = False, filtrado: bool = False) -> list[Indicator]:
    el = individual_table(df, incluir_extremos)
    pot = len(el)
    tol = TOLERANCIAS["volume_m3"]
    out = []
    for id_, nome, col, req, formula, notas in (
        ("v_cil_total", "Volume cilíndrico total (g × HT)", "v_cil_m3", "ht_m_elegivel",
         "v = gᵢ · HTᵢ ;  V = Σ v",
         ["Volume de cilindro, sem fator de forma — informado como cilíndrico (orientação do áudio de 17/11/2026)."]),
        ("v_spurr_total", "Volume comercial — equação de Spurr (Jorge, 1982)", "v_spurr_m3", "hc_m_elegivel",
         "Vc = 0,106531813 + 5,3372·10⁻⁵ · DAP² · HC",
         ["Coeficientes regionais (Mata Atlântica norte ES / sul BA). Calculado só quando há HC.",
          "Faixa de DAP do ajuste não informada na referência: árvores pequenas podem ser superestimadas "
          "(o intercepto b₀ ≈ 0,1065 m³ domina)."]),
    ):
        vals = el.loc[el[col].notna(), col].tolist()
        n = len(vals)
        motivos = Counter()
        for a, b, ra, rb in zip(el["dap_elegivel"], el[req], el["dap_motivo_exclusao"],
                                el[req.replace("_elegivel", "_motivo_exclusao")]):
            if not a:
                motivos[ra] += 1
            elif not b:
                motivos[rb or "altura não elegível"] += 1
        kw = dict(unidade="m³", denominador=f"{n} indivíduos com DAP e altura elegíveis de {pot} potenciais",
                  quantidade_potencial=pot, quantidade_elegivel=n, quantidade_excluida=pot - n,
                  motivos_exclusao=dict(motivos.most_common()), cobertura=cobertura(n, pot), formula=formula,
                  filtrado=filtrado, tolerancia=f"atol={tol.atol:g}, rtol={tol.rtol:g}",
                  versao_metodologica="ref-PTMC-Camila + áudio 2026-11-17")
        if n == 0:
            out.append(Indicator(id=id_, nome=nome, valor=None, status=INDISPONIVEL, observacoes=notas, **kw))
        else:
            out.append(Indicator(id=id_, nome=nome, valor=math.fsum(vals), status=VALIDO_RESSALVA,
                                 observacoes=notas, **kw))
    return out


# ------------------------------------------------------------ agrupamentos
def group_table(df: pd.DataFrame, by: str, incluir_extremos: bool = False) -> pd.DataFrame:
    el = individual_table(df, incluir_extremos)
    if el.empty:
        return pd.DataFrame()
    el = el[el[by].notna()]
    rows = []
    for key, g in el.groupby(by, sort=False):
        d = g.loc[g["dap_elegivel"], "dap_cm"].tolist()
        h = g.loc[g["ht_m_elegivel"], "ht_m"].tolist()
        gg = g.loc[g["dap_elegivel"], "g_m2"].tolist()
        rows.append({
            by: key,
            "registros": len(g),
            "indivíduos": g["individuo_id"].nunique(),
            "DAPs elegíveis": len(d),
            "DAPs excluídos": len(g) - len(d),
            "cobertura DAP (%)": len(d) / len(g) * 100 if len(g) else None,
            "média aritmética DAP (cm)": mean(d) if d else None,
            "mediana DAP (cm)": quantile(d, 0.5) if d else None,
            "HT elegíveis": len(h),
            "altura total média HT (m)": mean(h) if h else None,
            "área basal G (m²)": math.fsum(gg) if gg else None,
        })
    out = pd.DataFrame(rows)
    return out.sort_values(by, key=lambda s: s.map(natural_key)).reset_index(drop=True)


# ------------------------------------------------------------ rankings
def ranking(df: pd.DataFrame, criterio: str, top: int = 10, incluir_extremos: bool = False) -> pd.DataFrame:
    el = individual_table(df, incluir_extremos)
    spec = {
        "dap": ("dap_cm", "dap_elegivel", "cm", "Maiores DAPs"),
        "ht": ("ht_m", "ht_m_elegivel", "m", "Maiores alturas totais (HT)"),
        "g": ("g_m2", "dap_elegivel", "m²", "Maiores áreas basais individuais"),
    }[criterio]
    col, flag, unit, _ = spec
    sub = el[el[flag] & el[col].notna()].copy()
    if sub.empty:
        return pd.DataFrame()
    sub["_k"] = [natural_key(p) + natural_key(a) + (ln,) for p, a, ln in zip(sub["parcela"], sub["arvore"], sub["_linha"])]
    sub = sub.sort_values([col, "_k"], ascending=[False, True])
    sub["posição"] = sub[col].rank(method="min", ascending=False).astype(int)
    sub = sub[sub["posição"] <= top]
    sub["empate"] = sub.duplicated(col, keep=False)
    return pd.DataFrame({
        "posição": sub["posição"], "parcela": sub["parcela"], "árvore": sub["arvore"],
        "espécie": sub["especie"], "data da medição": sub["data_medicao"], "valor": sub[col],
        "unidade": unit, "empate": sub["empate"].map({True: "sim", False: ""}),
        "advertências de qualidade": sub["motivos"], "linha de origem": sub["_linha"],
    }).reset_index(drop=True)


# ------------------------------------------------------------ distribuição diamétrica
def diameter_distribution(df: pd.DataFrame, largura_cm: float, inicio_cm: float = 0.0,
                          incluir_extremos: bool = False) -> tuple[pd.DataFrame, dict]:
    """Classes [a, b) fechadas à esquerda e abertas à direita: um valor igual a
    um limite pertence à classe que COMEÇA nele. Sem lacunas nem sobreposição.

    Exploratória: não é classificação metodológica oficial.
    """
    if not (largura_cm > 0 and math.isfinite(largura_cm)):
        raise ValueError("Largura de classe deve ser positiva.")
    el = dap_eligibility(df, incluir_extremos)
    vals = el.loc[el["dap_elegivel"], "dap_cm"].astype(float).to_numpy()
    info = {"n_elegivel": int(len(vals)), "n_potencial": int(len(el)),
            "n_excluido": int(len(el) - len(vals)), "motivos": _reasons(el["dap_motivo_exclusao"]),
            "largura_cm": largura_cm, "regra": "classes [limite inferior, limite superior) — fechadas à esquerda"}
    if len(vals) == 0:
        return pd.DataFrame(columns=["classe", "limite inferior (cm)", "limite superior (cm)", "centro (cm)",
                                     "frequência absoluta", "frequência relativa (%)"]), info
    lo = min(inicio_cm, math.floor(vals.min() / largura_cm) * largura_cm)
    k_max = int(math.floor((vals.max() - lo) / largura_cm))
    idx = np.floor((vals - lo) / largura_cm).astype(int)
    counts = np.bincount(idx, minlength=k_max + 1)
    rows = []
    for k, c in enumerate(counts):
        a, b = lo + k * largura_cm, lo + (k + 1) * largura_cm
        rows.append({"classe": f"[{a:g} ; {b:g})", "limite inferior (cm)": a, "limite superior (cm)": b,
                     "centro (cm)": (a + b) / 2, "frequência absoluta": int(c),
                     "frequência relativa (%)": c / len(vals) * 100})
    tab = pd.DataFrame(rows)
    assert int(tab["frequência absoluta"].sum()) == len(vals)
    return tab, info
