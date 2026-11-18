"""Inventário: contagens gerais, parcelas, espécies, indivíduos, mortalidade e
replantio. Distingue rigorosamente linhas, registros, indivíduos, medições,
espécies e parcelas.
"""
from __future__ import annotations

import math

import pandas as pd

from . import dendrometry as dd
from .canonicalization import natural_key
from .ingestion import ImportMetadata
from .quality import (
    MED_MEDIDO,
    REG_INCONCLUSIVO,
    REG_INVALIDO,
    REG_RESSALVA,
    REG_VALIDO,
    campaign_summary,
)
from .results import (
    TOLERANCIAS,
    BLOQ_METODOLOGIA,
    BLOQ_QUALIDADE,
    BLOQ_QUALIDADE_OU_METODOLOGIA,
    INDISPONIVEL,
    VALIDO,
    VALIDO_RESSALVA,
    Indicator,
    Metodologia,
    bloqueado,
    cobertura,
)


def _count(id_, nome, valor, unidade, denominador, pot=None, el=None, exc=None, obs=None, filtrado=False,
           cov=None, formula="contagem", status=VALIDO, motivos=None) -> Indicator:
    return Indicator(id=id_, nome=nome, valor=valor, unidade=unidade, denominador=denominador,
                     quantidade_potencial=pot, quantidade_elegivel=el, quantidade_excluida=exc,
                     cobertura=cov, observacoes=obs or [], filtrado=filtrado, formula=formula,
                     status=status, motivos_exclusao=motivos or {}, tolerancia="exata")


def general_indicators(df: pd.DataFrame, issues: pd.DataFrame, meta: ImportMetadata | None,
                       incluir_extremos: bool = False, filtrado: bool = False) -> list[Indicator]:
    n = len(df)
    st = df["status_registro"].value_counts() if n else pd.Series(dtype=int)
    pot = dd.potential(df)
    ident = df[df["identificavel"] & ~df["anotacao_parcela"]] if n else df
    parcelas = dd.parcelas_inventariadas(df)
    especies = ident["especie"].dropna().unique() if n else []
    med = ident["medicao_id"].dropna().unique() if n else []
    dap_el = dd.dap_eligibility(df, incluir_extremos) if n else pd.DataFrame()
    ht_el = dd.height_eligibility(df, "ht_m") if n else pd.DataFrame()
    n_dap = int(dap_el["dap_elegivel"].sum()) if n else 0
    n_ht = int(ht_el["ht_m_elegivel"].sum()) if n else 0
    dap_aus = int((pot["dap_cm_status"] == "AUSENTE").sum()) if n else 0
    dap_inv = int((pot["dap_cm_status"] == "INVÁLIDO").sum()) if n else 0
    dup_med = int((df["n_registros_medicao"] > 1).sum()) if n else 0
    dup_ind = int(df.loc[df["n_registros_individuo"] > 1, "individuo_id"].nunique()) if n else 0
    camp = campaign_summary(df) if n else {"possiveis_campanhas": 0}
    rev = int(df["obs_revisao"].sum()) if n else 0
    n_obs = int(df["observacao"].notna().sum()) if n else 0
    linhas = meta.linhas_fisicas if meta else None
    nao_id = sum(1 for s in especies if s.lower().startswith(("não identificad", "nao identificad")))
    reg_txt = f"{n} registros interpretados"
    out = [
        _count("linhas_importadas", "Total de linhas importadas (físicas, incl. cabeçalho e vazias)", linhas, "linhas",
               f"arquivo: {meta.nome_arquivo}" if meta else "—",
               obs=[f"{meta.linhas_vazias_ignoradas} linhas vazias ignoradas; {meta.registros_interpretados} registros interpretados."] if meta else [],
               status=VALIDO if meta else INDISPONIVEL),
        _count("registros_validos", "Registros válidos", int(st.get(REG_VALIDO, 0)), "registros", reg_txt, n,
               cov=cobertura(int(st.get(REG_VALIDO, 0)), n), filtrado=filtrado),
        _count("registros_ressalva", "Registros válidos com ressalva", int(st.get(REG_RESSALVA, 0)), "registros",
               reg_txt, n, cov=cobertura(int(st.get(REG_RESSALVA, 0)), n), filtrado=filtrado),
        _count("registros_invalidos", "Registros inválidos", int(st.get(REG_INVALIDO, 0)), "registros", reg_txt, n,
               cov=cobertura(int(st.get(REG_INVALIDO, 0)), n), filtrado=filtrado),
        _count("registros_inconclusivos", "Registros inconclusivos", int(st.get(REG_INCONCLUSIVO, 0)), "registros",
               reg_txt, n, cov=cobertura(int(st.get(REG_INCONCLUSIVO, 0)), n), filtrado=filtrado),
        _count("parcelas", "Parcelas identificadas", len(parcelas), "parcelas",
               "valores distintos de Parcela em registros identificáveis ou anotações de parcela", filtrado=filtrado,
               obs=["Identificadores preservados como texto: '7' e '07' seriam parcelas distintas."]),
        _count("individuos", "Indivíduos únicos identificáveis", int(ident["individuo_id"].nunique()) if n else 0,
               "indivíduos", f"pares Parcela + Árvore distintos em {len(ident)} registros identificáveis",
               len(ident), filtrado=filtrado, formula="nº de pares distintos (Parcela, Árvore)"),
        _count("especies", "Espécies identificadas (riqueza observada)", len(especies), "táxons",
               "valores distintos de Nome Comum (sem espaço externo) em registros identificáveis", filtrado=filtrado,
               status=VALIDO_RESSALVA if nao_id else VALIDO,
               obs=([f"Inclui {nao_id} rótulo(s) 'Não identificada' contados como táxons distintos."] if nao_id else [])
               + ["Variações de grafia não são unificadas (ver Qualidade)."]),
        _count("medicoes", "Medições dendrométricas", len(med), "medições",
               "chaves Parcela + Árvore + Data Medição distintas", len(ident),
               exc=len(ident) - int(ident["medicao_id"].notna().sum()) if n else 0,
               obs=["Registros sem data de medição não formam chave de medição (identidade inconclusiva)."],
               filtrado=filtrado),
        _count("cobertura_dap", "Cobertura de DAP", None if not len(dap_el) else n_dap / len(dap_el) * 100, "%",
               f"{n_dap} DAPs elegíveis de {len(dap_el)} registros potenciais", len(dap_el), n_dap,
               len(dap_el) - n_dap, cov=cobertura(n_dap, len(dap_el)), filtrado=filtrado,
               motivos=dd._reasons(dap_el["dap_motivo_exclusao"]) if n else {},
               formula="DAPs elegíveis / registros potenciais × 100",
               status=VALIDO if len(dap_el) else INDISPONIVEL),
        _count("cobertura_ht", "Cobertura de altura total (HT)", None if not len(ht_el) else n_ht / len(ht_el) * 100,
               "%", f"{n_ht} HT elegíveis de {len(ht_el)} registros potenciais", len(ht_el), n_ht,
               len(ht_el) - n_ht, cov=cobertura(n_ht, len(ht_el)), filtrado=filtrado,
               motivos=dd._reasons(ht_el["ht_m_motivo_exclusao"]) if n else {},
               formula="HT elegíveis / registros potenciais × 100",
               status=VALIDO if len(ht_el) else INDISPONIVEL),
        _count("dap_ausentes", "DAPs ausentes", dap_aus, "registros", f"de {len(pot)} registros potenciais",
               len(pot), filtrado=filtrado,
               obs=["Ausência sem justificativa. DAP vazio com menção de morte ou multifuste é contado como NÃO APLICÁVEL."]),
        _count("dap_invalidos", "DAPs inválidos", dap_inv, "registros", f"de {len(pot)} registros potenciais",
               len(pot), filtrado=filtrado, obs=["Datas, textos, negativos ou não finitos na coluna DAP."]),
        _count("duplicidades", "Duplicidades de medição (Parcela + Árvore + Data)", dup_med, "registros",
               f"de {n} registros", n, filtrado=filtrado,
               obs=[f"Indivíduos com mais de um registro (qualquer data): {dup_ind}."]),
        _count("campanhas", "Possíveis campanhas", camp["possiveis_campanhas"], "campanhas",
               "máximo de datas distintas por indivíduo", filtrado=filtrado, status=VALIDO_RESSALVA,
               obs=["Estimativa: cada data é um dia de campo; campanha = rodada de remedição do mesmo indivíduo."]
               + ([f"Período: {camp['primeira_data']:%d/%m/%Y} a {camp['ultima_data']:%d/%m/%Y} "
                   f"({camp['datas_distintas']} datas distintas)."] if camp.get("primeira_data") else [])),
        _count("obs_revisao", "Observações que exigem revisão", rev, "registros",
               f"de {n_obs} registros com observação preenchida", n_obs, filtrado=filtrado,
               obs=["Menções potenciais detectadas por termos; não são ocorrências confirmadas."]),
    ]
    return out


# ------------------------------------------------------------ parcelas
def plot_table(df: pd.DataFrame, incluir_extremos: bool = False, metodologia: Metodologia | None = None) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    base = dd.group_table(df, "parcela", incluir_extremos)
    rows = []
    for p, g in df[df["parcela"].notna()].groupby("parcela"):
        ok = g[g["identificavel"] & ~g["anotacao_parcela"]]
        warn = sorted({c for m in g["motivos"] for c in m.split("; ") if c})
        rows.append({
            "parcela": p,
            "espécies": "; ".join(sorted(ok["especie"].dropna().unique())),
            "riqueza observada": ok["especie"].dropna().nunique(),
            "medições ausentes (DAP)": int((ok["dap_cm_status"] == "AUSENTE").sum()),
            "registros inválidos": int((g["status_registro"] == REG_INVALIDO).sum()),
            "anotação de parcela": "; ".join(str(x) for x in g.loc[g["anotacao_parcela"], "arvore_orig"]),
            "advertências": "; ".join(warn),
        })
    extra = pd.DataFrame(rows)
    if base.empty:
        out = extra
    else:
        out = extra.merge(base, on="parcela", how="left")
    out = out.sort_values("parcela", key=lambda s: s.map(natural_key)).reset_index(drop=True)
    if metodologia is not None and metodologia.por_hectare_informado:
        # G/ha por parcela só quando o usuário informou área e desenho amostral; parcela sem área → vazio.
        areas = out["parcela"].map(metodologia.area_ha)
        g = out["área basal G (m²)"] if "área basal G (m²)" in out else pd.Series(None, index=out.index)
        out["área da parcela (ha)"] = areas
        out["área basal G (m²/ha)"] = [gv / a if a and gv is not None and not pd.isna(gv) else None
                                       for gv, a in zip(g, areas)]
        if metodologia.fonte.startswith("literatura") and "indivíduos" in out:
            # Desenho publicado: 36 plantas por parcela. Excesso é sinalizado, nunca corrigido.
            out["advertências"] = [
                (w + "; " if w else "") + f"{int(n)} indivíduos: acima das 36 plantas do desenho publicado"
                if a and n == n and n > 36 else w
                for w, n, a in zip(out["advertências"], out["indivíduos"], areas)]
    cols = ["parcela", "indivíduos", "registros", "espécies", "riqueza observada", "DAPs elegíveis",
            "média aritmética DAP (cm)", "mediana DAP (cm)", "altura total média HT (m)", "área basal G (m²)",
            "área da parcela (ha)", "área basal G (m²/ha)", "medições ausentes (DAP)", "registros inválidos", "cobertura DAP (%)", "anotação de parcela",
            "advertências"]
    return out[[c for c in cols if c in out.columns]]


# ------------------------------------------------------------ espécies
def species_table(df: pd.DataFrame, incluir_extremos: bool = False) -> pd.DataFrame:
    ident = dd.potential(df)
    if ident.empty:
        return pd.DataFrame()
    base = dd.group_table(df, "especie", incluir_extremos)
    occ = ident[ident["especie"].notna()].groupby("especie").agg(
        **{"Abundância por indivíduos únicos": ("individuo_id", "nunique"),
           "Ocorrência em parcelas": ("parcela", "nunique")}).reset_index()
    total_ind = ident.loc[ident["especie"].notna(), "individuo_id"].nunique()
    n_parc_total = len(dd.parcelas_inventariadas(df))  # P: todas as unidades amostrais, inclusive sem árvores
    occ["Densidade relativa DR (%)"] = occ["Abundância por indivíduos únicos"] / total_ind * 100
    occ["Frequência absoluta FA (%)"] = occ["Ocorrência em parcelas"] / n_parc_total * 100 if n_parc_total else None
    soma_fa = occ["Frequência absoluta FA (%)"].sum() if n_parc_total else 0
    occ["Frequência relativa FR (%)"] = occ["Frequência absoluta FA (%)"] / soma_fa * 100 if soma_fa else None
    out = occ.merge(base.drop(columns=["registros", "indivíduos"]), on="especie", how="left")
    g_tot = out["área basal G (m²)"].sum(skipna=True)
    gcol = pd.to_numeric(out["área basal G (m²)"], errors="coerce")
    out["Dominância relativa DoR (%)"] = gcol / g_tot * 100 if g_tot else float("nan")
    # Espécie sem área basal medida: DoR desconhecida (não zero) → VI indisponível.
    out["Valor de importância VI (0–300)"] = out["Densidade relativa DR (%)"] + \
        out["Dominância relativa DoR (%)"] + out["Frequência relativa FR (%)"]
    out = out.rename(columns={"especie": "espécie"})
    return out.sort_values(["Abundância por indivíduos únicos", "espécie"], ascending=[False, True]).reset_index(drop=True)


# ------------------------------------------------------------ diversidade (literatura)
def diversity_indicators(df: pd.DataFrame, filtrado: bool = False) -> list[Indicator]:
    """Shannon (H', ln), equabilidade de Pielou (J') e Simpson (1 − D, sem reposição).

    Brower & Zar (1984); Magurran (2004); Mueller-Dombois & Ellenberg (1974). nᵢ = indivíduos únicos
    (Parcela + Árvore) da espécie i; N = Σ nᵢ; S = espécies com nᵢ > 0. Logaritmo natural (nats/indivíduo),
    convenção predominante nos levantamentos florestais brasileiros.
    """
    ident = dd.potential(df)
    sub = ident[ident["especie"].notna()] if len(ident) else ident
    counts = sub.groupby("especie")["individuo_id"].nunique() if len(sub) else pd.Series(dtype=int)
    counts = counts[counts > 0]
    N, S = int(counts.sum()), int(len(counts))
    pot = int(ident["individuo_id"].nunique()) if len(ident) else 0
    nao_id = sum(1 for e in counts.index if e.lower().startswith(("não identificad", "nao identificad")))
    n_morte = int(sub.loc[sub["mencao_morte"], "individuo_id"].nunique()) if len(sub) and "mencao_morte" in sub else 0
    ressalvas = [
        "Arboreto plantado (parcelas monoespecíficas com o mesmo número de mudas por espécie): os índices descrevem a "
        "coleção atual registrada, não a diversidade de uma comunidade natural.",
        "Rótulos 'Não identificada N' contados como morfoespécies distintas" + (f" ({nao_id})." if nao_id else "."),
        "Variações de grafia de nomes comuns não são unificadas (ver Qualidade): podem inflar S.",
    ] + ([f"Inclui {n_morte} indivíduo(s) com menção de morte na observação (estado vital não estruturado)."]
         if n_morte else [])
    den = f"N = {N} indivíduos únicos com espécie; S = {S} espécies"
    tol = TOLERANCIAS["indice"]
    kw = dict(denominador=den, quantidade_potencial=pot, quantidade_elegivel=N, quantidade_excluida=pot - N,
              cobertura=cobertura(N, pot), filtrado=filtrado, tolerancia=f"atol={tol.atol:g}, rtol={tol.rtol:g}",
              versao_metodologica="literatura (Brower & Zar, 1984; Magurran, 2004)", observacoes=ressalvas)
    if N == 0:
        return [bloqueado(i, n, u, "Nenhum indivíduo com espécie.", status=INDISPONIVEL, filtrado=filtrado)
                for i, n, u in (("shannon", "Índice de Shannon (H')", "nats/indivíduo"),
                                ("pielou", "Equabilidade de Pielou (J')", "adimensional"),
                                ("simpson", "Índice de Simpson (1 − D)", "adimensional"))]
    p = [n / N for n in counts]
    H = -math.fsum(pi * math.log(pi) for pi in p)
    out = [Indicator(id="shannon", nome="Índice de Shannon (H')", valor=H, unidade="nats/indivíduo",
                     formula="H' = −Σ pᵢ · ln pᵢ ;  pᵢ = nᵢ / N", status=VALIDO_RESSALVA, **kw)]
    if S >= 2:
        out.append(Indicator(id="pielou", nome="Equabilidade de Pielou (J')", valor=H / math.log(S), unidade="adimensional",
                             formula="J' = H' / ln S", status=VALIDO_RESSALVA, **kw))
    else:
        out.append(bloqueado("pielou", "Equabilidade de Pielou (J')", "adimensional",
                             "Indefinida com S < 2 (ln 1 = 0).", status=INDISPONIVEL, formula="J' = H' / ln S",
                             filtrado=filtrado))
    if N >= 2:
        D = math.fsum(n * (n - 1) for n in counts) / (N * (N - 1))
        out.append(Indicator(id="simpson", nome="Índice de Simpson (1 − D)", valor=1 - D, unidade="adimensional",
                             formula="D = Σ nᵢ(nᵢ − 1) / [N(N − 1)] ;  índice = 1 − D", status=VALIDO_RESSALVA, **kw))
    else:
        out.append(bloqueado("simpson", "Índice de Simpson (1 − D)", "adimensional", "Indefinido com N < 2.",
                             status=INDISPONIVEL, filtrado=filtrado))
    return out


# ------------------------------------------------------------ indivíduos
def individuals_table(df: pd.DataFrame, incluir_extremos: bool = False) -> pd.DataFrame:
    el = dd.individual_table(df, incluir_extremos)
    if el.empty:
        return pd.DataFrame()
    cols = {
        "individuo_id": "indivíduo", "parcela": "parcela", "arvore": "árvore", "especie": "espécie",
        "data_medicao": "data da medição", "dap_cm": "DAP (cm)", "dap_cm_status": "status DAP",
        "dap_elegivel": "DAP elegível", "dap_motivo_exclusao": "motivo exclusão DAP",
        "hesg_m": "HESG (m)", "hesgcopa_m": "HESGCOPA (m)", "hc_m": "HC (m)", "ht_m": "HT (m)",
        "ht_m_status": "status HT", "g_m2": "g (m²)", "v_cil_m3": "volume cilíndrico (m³)",
        "v_spurr_m3": "volume Spurr (m³)", "n_registros_individuo": "medições do indivíduo",
        "status_registro": "status do registro", "motivos": "diagnósticos", "observacao": "observação",
        "_linha": "linha de origem",
    }
    out = el[list(cols)].rename(columns=cols)
    out["_k"] = [natural_key(p) + natural_key(a) for p, a in zip(out["parcela"], out["árvore"])]
    return out.sort_values(["_k", "data da medição"]).drop(columns="_k").reset_index(drop=True)


# ------------------------------------------------------------ mortalidade e sobrevivência
VITAL_VIVO = {"vivo", "viva"}
VITAL_MORTO = {"morto", "morta"}
VITAL_NAO_LOCALIZADO = {"nao localizado", "nao localizada"}
VITAL_NAO_AVALIADO = {"nao avaliado", "nao avaliada"}


def mortality(df: pd.DataFrame, implantados: dict[str, int] | int | None, ativo: bool = True,
              filtrado: bool = False) -> tuple[list[Indicator], pd.DataFrame]:
    formula = ("Mortalidade (%) = mortos / implantados × 100 ;  Sobrevivência (%) = vivos / implantados × 100 ;  "
               "sem registro = implantados − (vivos + mortos + não localizados + não avaliados) — NÃO é mortalidade")
    if not ativo or implantados is None:
        return [bloqueado("mortalidade", "Mortalidade", "%", "Cálculo desativado pelo usuário.",
                          status=INDISPONIVEL, formula=formula, filtrado=filtrado)], pd.DataFrame()
    ident = dd.potential(df)
    vital = ident["estado_vital"] if "estado_vital" in ident else pd.Series(dtype=object)
    if vital.isna().all():
        motivo = ("O arquivo não possui estado vital estruturado (coluna 'Estado vital' com vivo / morto / "
                  "não localizado / não avaliado). Menções de 'MORTA' em Observação são texto livre e não "
                  "sustentam o cálculo. '36 − registros' nunca é usado como número de mortos.")
        return [bloqueado("mortalidade", "Mortalidade", "%", motivo, status=BLOQ_QUALIDADE_OU_METODOLOGIA,
                          formula=formula, filtrado=filtrado),
                bloqueado("sobrevivencia", "Sobrevivência", "%", motivo, status=BLOQ_QUALIDADE_OU_METODOLOGIA,
                          formula=formula, filtrado=filtrado)], pd.DataFrame()
    rows = []
    for p, g in ident.groupby("parcela"):
        imp = implantados.get(p) if isinstance(implantados, dict) else implantados
        v = g.drop_duplicates("individuo_id")["estado_vital"]
        vivos = int(v.isin(VITAL_VIVO).sum())
        mortos = int(v.isin(VITAL_MORTO).sum())
        nl = int(v.isin(VITAL_NAO_LOCALIZADO).sum())
        na = int(v.isin(VITAL_NAO_AVALIADO).sum())
        outros = int(len(v) - vivos - mortos - nl - na)
        row = {"parcela": p, "implantados": imp, "vivos": vivos, "mortos": mortos, "não localizados": nl,
               "não avaliados": na, "estado não reconhecido": outros}
        if imp is None or imp <= 0:
            row.update({"sem registro": None, "mortalidade (%)": None, "sobrevivência (%)": None,
                        "status": INDISPONIVEL, "nota": "denominador não informado"})
        elif len(v) > imp:
            row.update({"sem registro": None, "mortalidade (%)": None, "sobrevivência (%)": None,
                        "status": BLOQ_QUALIDADE, "nota": f"{len(v)} indivíduos registrados > {imp} implantados"})
        else:
            sem = imp - (vivos + mortos + nl + na + outros)
            row.update({"sem registro": sem, "mortalidade (%)": mortos / imp * 100,
                        "sobrevivência (%)": vivos / imp * 100,
                        "status": VALIDO if sem == 0 and nl == 0 and na == 0 and outros == 0 else VALIDO_RESSALVA,
                        "nota": "" if sem == 0 else f"{sem} sem registro (não contados como mortos)"})
        rows.append(row)
    tab = pd.DataFrame(rows).sort_values("parcela", key=lambda s: s.map(natural_key))
    ok = tab[tab["status"].isin([VALIDO, VALIDO_RESSALVA])]
    imp_tot = int(ok["implantados"].sum()) if len(ok) else 0
    excl = len(tab) - len(ok)
    common = dict(unidade="%", denominador=f"{imp_tot} implantados em {len(ok)} parcelas elegíveis",
                  quantidade_potencial=len(tab), quantidade_elegivel=len(ok), quantidade_excluida=excl,
                  motivos_exclusao=tab.loc[~tab.index.isin(ok.index), "nota"].value_counts().to_dict(),
                  cobertura=cobertura(len(ok), len(tab)), formula=formula, filtrado=filtrado,
                  observacoes=["Denominador configurável (padrão 36 por parcela) — não é verdade universal."])
    if imp_tot == 0:
        return [Indicator(id="mortalidade", nome="Mortalidade", valor=None, status=INDISPONIVEL, **common)], tab
    st = VALIDO if (ok["status"] == VALIDO).all() else VALIDO_RESSALVA
    return [
        Indicator(id="mortalidade", nome="Mortalidade", valor=ok["mortos"].sum() / imp_tot * 100, status=st, **common),
        Indicator(id="sobrevivencia", nome="Sobrevivência", valor=ok["vivos"].sum() / imp_tot * 100, status=st, **common),
    ], tab


# ------------------------------------------------------------ replantio
def replanting(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    lim = ["Não se infere espécie original, espécie substituta, se é a mesma espécie nem impacto na sobrevivência."]
    if df.empty or (df["replantio_status"] == "NÃO COLETADO").all():
        return pd.DataFrame(), ["Coluna Replantio ausente no arquivo."] + lim
    sub = df[df["replantio_orig"].notna() & (df["replantio_orig"].astype(str).str.strip() != "")]
    if sub.empty:
        return pd.DataFrame(), ["Nenhum registro com indicação de replantio (coluna vazia em todos os registros)."] + lim
    tab = pd.DataFrame({"parcela": sub["parcela"], "árvore": sub["arvore"], "espécie atual": sub["especie"],
                        "replantio (original)": sub["replantio_orig"].astype(str),
                        "data de replantio": sub["replantio"], "status da data": sub["replantio_status"],
                        "linha": sub["_linha"]})
    return tab.reset_index(drop=True), lim


# ------------------------------------------------------------ itens bloqueados (metodologia)
PENDENTES = [
    ("Indicador composto de saúde", "Escala e interpretação não definidas (M12); fitossanidade fora deste arquivo."),
    ("Dano leve / dano severo", "Não há coleta de gradação de dano (D6 / M2)."),
    ("Classificação definitiva do povoamento", "Limiares sem origem documentada (M13)."),
    ("Diâmetro médio de referência do projeto", "dg e média aritmética são calculados e definidos pela literatura; "
     "qual deles será o 'diâmetro médio' oficial do projeto é decisão M5 da equipe."),
    ("Multifuste sem padrão estrutural", "Indícios de multifuste cujos fustes não podem ser extraídos sem ambiguidade "
     "(números por extenso, listas sem quantidade declarada, contagem divergente, DAP da coluna diferente dos fustes): "
     "revisão humana. Os extraíveis seguem a regra de Finger (1992)."),
    ("Mortalidade baseada apenas em registros ausentes", "Ausência de registro não é morte."),
    ("Mortalidade / sobrevivência", "O desenho (36 plantas por parcela) é documentado na literatura, mas o arquivo não "
     "tem estado vital estruturado (vivo / morto / não localizado / não avaliado). Dado ausente, não lacuna de método."),
    ("Intensidade de serrapilheira", "Sem escala definida (M10)."),
    ("Ocorrência confirmada de fauna", "Texto livre gera apenas menções potenciais."),
    ("Nota (*) da definição de HESGCOPA", "A imagem de definições das siglas traz um asterisco sem a nota "
     "correspondente. Comprimento e proporção de copa são calculados pela definição fornecida, com ressalva."),
]
