"""Validação, diagnóstico e classificação de cada registro.

Produz:
- ``records``: tabela canônica (valor original + valor normalizado + status
  por campo + status do registro);
- ``issues``: um diagnóstico por ocorrência, com linha, célula, valor
  original, severidade e classe de recuperação.

Nenhum valor original é alterado. Nenhum valor inválido é corrigido.
"""
from __future__ import annotations

import datetime as dt
import re
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import observations as obs
from .canonicalization import (
    HEIGHT_COLUMNS,
    LABEL,
    ColumnMapping,
    fold,
    natural_key,
    parse_date,
    parse_id,
    parse_number,
)
from .ingestion import Cell, RawTable

# Estados de registro
REG_VALIDO = "VÁLIDO"
REG_RESSALVA = "VÁLIDO COM RESSALVA"
REG_INVALIDO = "INVÁLIDO"
REG_INCONCLUSIVO = "INCONCLUSIVO"
ESTADOS_REGISTRO = (REG_VALIDO, REG_RESSALVA, REG_INVALIDO, REG_INCONCLUSIVO)

# Severidade
BLOQUEANTE = "BLOQUEANTE"
ADVERTENCIA = "ADVERTÊNCIA"
INFORMATIVO = "INFORMATIVO"

# Classes de recuperação (seção 9)
REC_AUTO = "Recuperável automaticamente (regra determinística)"
REC_HUMANA = "Recuperável somente com revisão humana"
REC_IRRECUPERAVEL = "Irrecuperável sem a fonte original"
REC_ADVERTENCIA = "Válido com advertência"
REC_VALIDO = "Válido"

# Estados de medição (seção 13)
MED_MEDIDO = "MEDIDO"
MED_AUSENTE = "AUSENTE"
MED_INVALIDO = "INVÁLIDO"
MED_NA = "NÃO APLICÁVEL"
MED_EXTREMO = "EXTREMO"
MED_REVISAO = "PENDENTE DE REVISÃO"

# REGRA LEGADA NÃO VALIDADA METODOLOGICAMENTE (código antigo do app: 0 < DAP ≤ 300).
DAP_LIMITE_LEGADO_CM = 300.0

# Limite físico para alturas, fundamentado na literatura: a maior árvore viva já
# medida (Hyperion, Sequoia sempervirens) tem 115,92 m (116,07 m em 2019). Acima de
# 120 m o valor é fisicamente implausível: EXTREMO (preservado, não inválido) e fora
# dos cálculos até revisão humana.
ALTURA_LIMITE_PLAUSIBILIDADE_M = 120.0
# Faixa de números seriais de data do Excel (1982–2119) usada só como PISTA.
SERIAL_DATA_FAIXA = (30000, 80000)

_SEM_ARVORES = re.compile(r"n[aã]o\s+tem", re.IGNORECASE)


@dataclass
class QualityResult:
    records: pd.DataFrame
    issues: pd.DataFrame
    mapping: ColumnMapping
    species_variants: list[list[str]] = field(default_factory=list)


class _Issues:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, idx: int, line: int, coord: str, campo: str, codigo: str, descricao: str,
            severidade: str, recuperacao: str, original, impacto: str = "") -> None:
        self.rows.append({
            "registro": idx, "linha": line, "célula": coord, "campo": campo, "código": codigo,
            "descrição": descricao, "severidade": severidade, "recuperação": recuperacao,
            "valor original": "" if original is None else str(original), "impacto": impacto,
        })


def _cell(row_cells: list[Cell], cmap: ColumnMapping, cid: str) -> Cell:
    idx = cmap.mapping.get(cid)
    if idx is None or idx >= len(row_cells):
        return Cell(None, "vazio", "", "")
    return row_cells[idx]


def _measure(cell: Cell, campo: str, is_dap: bool, iss: _Issues, idx: int, line: int,
             obs_text: str | None, obs_pos: set[str]) -> tuple[float, str, str, str | None]:
    """Retorna (valor, status, motivo, pista) para uma coluna numérica."""
    p = parse_number(cell)
    label = LABEL[campo]
    nome = "DAP" if is_dap else label.split(" ")[0]
    if p.trimmed and p.status == "NUMERO":
        iss.add(idx, line, cell.coord, label, "ESPACO_EXTERNO", f"{nome} com espaço externo removido.",
                INFORMATIVO, REC_AUTO, p.original)
    if p.status == "NUMERO":
        v = p.value
        if v < 0:
            iss.add(idx, line, cell.coord, label, f"{'DAP' if is_dap else 'ALTURA'}_NEGATIVO",
                    f"{nome} negativo.", ADVERTENCIA, REC_IRRECUPERAVEL, p.original, f"{nome} excluído dos cálculos")
            return np.nan, MED_INVALIDO, "valor negativo", None
        if v == 0:
            iss.add(idx, line, cell.coord, label, f"{'DAP' if is_dap else 'ALTURA'}_ZERO",
                    f"{nome} igual a zero (valor explícito).", ADVERTENCIA, REC_HUMANA, p.original,
                    f"{nome} excluído dos cálculos até revisão")
            return 0.0, MED_REVISAO, "valor zero (pendente de revisão)", None
        serial_hint = None
        if SERIAL_DATA_FAIXA[0] <= v <= SERIAL_DATA_FAIXA[1] and float(v).is_integer():
            d = dt.date(1899, 12, 30) + dt.timedelta(days=int(v))
            serial_hint = f"{d.day}.{d.month}"
            iss.add(idx, line, cell.coord, label, "POSSIVEL_SERIAL_DATA",
                    f"{nome} = {v:g}: compatível com número serial de data ({d:%d/%m/%Y}, exibiria '{serial_hint}' "
                    "em formato d.m). Valor preservado, não reconstruído.", ADVERTENCIA, REC_HUMANA, p.original)
        if not is_dap and v > ALTURA_LIMITE_PLAUSIBILIDADE_M:
            iss.add(idx, line, cell.coord, label, "ALTURA_EXTREMA",
                    f"{nome} acima de {ALTURA_LIMITE_PLAUSIBILIDADE_M:g} m (limite físico: maior árvore viva medida ≈ 116 m). Valor preservado.",
                    ADVERTENCIA, REC_HUMANA, p.original, f"{nome} fora dos cálculos até revisão")
            return v, MED_EXTREMO, f"{nome} > {ALTURA_LIMITE_PLAUSIBILIDADE_M:g} m (pendente de revisão)", serial_hint
        if is_dap and v > DAP_LIMITE_LEGADO_CM:
            iss.add(idx, line, cell.coord, label, "DAP_EXTREMO",
                    f"DAP acima de {DAP_LIMITE_LEGADO_CM:g} cm (regra legada não validada). Valor preservado.",
                    ADVERTENCIA, REC_ADVERTENCIA, p.original, "elegibilidade depende de opção explícita")
            return v, MED_EXTREMO, f"DAP > {DAP_LIMITE_LEGADO_CM:g} cm (regra legada)", serial_hint
        if is_dap and ("morte" in obs_pos):
            iss.add(idx, line, cell.coord, label, "DAP_COM_MENCAO_MORTE",
                    "DAP numérico, mas a observação menciona morte. Estado vital requer revisão.",
                    ADVERTENCIA, REC_HUMANA, obs_text)
        return v, MED_MEDIDO, "", None
    if p.status == "AUSENTE":
        if is_dap and "morte" in obs_pos:
            return np.nan, MED_NA, "observação menciona morte (estado vital requer revisão)", None
        if is_dap and ("múltiplos fustes" in obs_pos or "bifurcação" in obs_pos or obs.has_diameter_list(obs_text)):
            iss.add(idx, line, cell.coord, label, "DAP_NAO_MENSURAVEL",
                    "DAP vazio e observação com indício de multifuste/lista de diâmetros. Fustes tratados pela "
                    "regra de Finger (1992) somente quando extraíveis por padrão estrutural (ver Multifustes).",
                    ADVERTENCIA, REC_HUMANA, obs_text, "DAP excluído dos cálculos")
            return np.nan, MED_NA, "multifuste: DAP de fuste único não aplicável (ver Multifustes)", None
        if is_dap:
            iss.add(idx, line, cell.coord, label, "DAP_AUSENTE", "DAP ausente.", ADVERTENCIA,
                    REC_IRRECUPERAVEL, None, "DAP excluído dos cálculos")
        return np.nan, MED_AUSENTE, "valor ausente", None
    if p.status == "DATA":
        hint = p.display_hint
        iss.add(idx, line, cell.coord, label, f"{'DAP' if is_dap else 'ALTURA'}_DATA",
                f"{nome} armazenado como data pela planilha. Valor original não reconstruído "
                f"(texto exibido na planilha: '{hint}', apenas como pista para revisão).",
                ADVERTENCIA, REC_HUMANA, p.original, f"{nome} excluído dos cálculos")
        return np.nan, MED_INVALIDO, "valor interpretado como data", hint
    if p.status == "TEXTO":
        if "morte" in {m.categoria for m in obs.find_mentions(p.normalized) if not m.negada}:
            iss.add(idx, line, cell.coord, label, f"{'DAP' if is_dap else 'ALTURA'}_ESTADO_VITAL",
                    f"Texto de estado vital na coluna {nome}. Valor preservado; requer revisão do estado vital.",
                    ADVERTENCIA, REC_HUMANA, p.original, f"{nome} excluído dos cálculos")
            return np.nan, MED_REVISAO, "texto de estado vital na coluna", None
        iss.add(idx, line, cell.coord, label, f"{'DAP' if is_dap else 'ALTURA'}_TEXTUAL",
                f"{nome} textual (não numérico).", ADVERTENCIA, REC_HUMANA, p.original, f"{nome} excluído dos cálculos")
        return np.nan, MED_INVALIDO, "valor textual", None
    iss.add(idx, line, cell.coord, label, f"{'DAP' if is_dap else 'ALTURA'}_INVALIDO",
            f"{nome} inválido ({p.status}).", ADVERTENCIA, REC_IRRECUPERAVEL, p.original, f"{nome} excluído")
    return np.nan, MED_INVALIDO, f"valor inválido ({p.status.lower()})", None


def _species_key(s: str) -> str:
    return " ".join(fold(s).replace("-", " ").split())


def build_records(raw: RawTable, cmap: ColumnMapping) -> QualityResult:
    if not cmap.is_safe:
        raise ValueError("Mapeamento de colunas inseguro: resolva colunas obrigatórias ausentes ou ambíguas.")
    iss = _Issues()
    out: list[dict] = []
    n_headers = len(raw.headers)
    for idx, row in enumerate(raw.rows):
        line = row.line
        rec: dict = {"_registro": idx, "_linha": line, "_linha_fim": row.line_end}
        blocking = False

        # ---- estrutura
        if row.extra:
            iss.add(idx, line, row.extra[0].coord, "(estrutura)", "COLUNAS_EXCEDENTES",
                    f"Valores além das {n_headers} colunas do cabeçalho: possível linha deslocada.",
                    BLOQUEANTE, REC_HUMANA, "; ".join(str(c.value) for c in row.extra), "registro excluído")
            blocking = True
        elif row.n_fields > n_headers:
            iss.add(idx, line, row.cells[0].coord if row.cells else "", "(estrutura)", "QTD_COLUNAS_INCORRETA",
                    f"Registro com {row.n_fields} campos; cabeçalho possui {n_headers}: possível linha deslocada "
                    "(ex.: vírgula decimal sem aspas).", BLOQUEANTE, REC_HUMANA, "", "registro excluído")
            blocking = True
        filled = [c for c in row.cells if not c.is_empty]
        if row.n_fields < n_headers:
            if len(filled) == 1 and row.n_fields <= 2 and filled[0].kind == "texto" \
                    and parse_number(filled[0]).status == "TEXTO":
                iss.add(idx, line, filled[0].coord, "(estrutura)", "OBSERVACAO_FRAGMENTADA",
                        "Linha com um único campo textual: possível fragmento de observação multilinha sem aspas. "
                        "Sem evidência estrutural determinística para recompor.",
                        BLOQUEANTE, REC_HUMANA, filled[0].value, "registro excluído")
            else:
                iss.add(idx, line, row.cells[0].coord if row.cells else "", "(estrutura)", "QTD_COLUNAS_INCORRETA",
                        f"Registro com {row.n_fields} campos; cabeçalho possui {n_headers}.",
                        BLOQUEANTE, REC_HUMANA, "", "registro excluído")
            blocking = True

        # ---- observação (lida primeiro: alimenta a interpretação de DAP vazio)
        oc = _cell(row.cells, cmap, "observacao")
        obs_text = None if oc.is_empty else str(oc.value)
        mencoes = obs.find_mentions(obs_text)
        pos = obs.positive_categories(mencoes)
        rec["observacao"] = obs_text
        rec["obs_termos"] = "; ".join(sorted({m.categoria + (" (negada)" if m.negada else "") for m in mencoes}))
        rec["obs_lista_diametros"] = obs.has_diameter_list(obs_text)
        rec["mencao_morte"] = "morte" in pos
        rec["mencao_multifuste"] = bool(pos & {"múltiplos fustes", "bifurcação"}) or rec["obs_lista_diametros"]
        rec["mencao_tombamento"] = "tombamento" in pos
        rec["mencao_rebrotacao"] = "rebrotação" in pos
        rec["mencao_quebra"] = "quebra" in pos
        rec["obs_revisao"] = bool(mencoes) or rec["obs_lista_diametros"] or obs.has_species_doubt(obs_text)

        # ---- identificadores
        for cid in ("parcela", "arvore"):
            c = _cell(row.cells, cmap, cid)
            p = parse_id(c)
            rec[cid] = p.value
            rec[f"{cid}_orig"] = c.value
            rec[f"{cid}_tipo"] = p.status
            nome = LABEL[cid]
            code = "PARCELA" if cid == "parcela" else "ARVORE"
            if p.trimmed and p.value is not None:
                iss.add(idx, line, c.coord, nome, "ESPACO_EXTERNO", f"{nome} com espaço externo removido.",
                        INFORMATIVO, REC_AUTO, c.value)
            if p.status == "AUSENTE":
                iss.add(idx, line, c.coord, nome, f"{code}_AUSENTE", f"{nome} ausente.", BLOQUEANTE,
                        REC_IRRECUPERAVEL, None, "registro não identificável; excluído")
                blocking = True
            elif p.status == "CODIGO":
                iss.add(idx, line, c.coord, nome, f"{code}_NAO_NUMERICA",
                        f"{nome} não numérica (código alfanumérico preservado: '{p.value}').",
                        ADVERTENCIA, REC_ADVERTENCIA, c.value)
            elif p.status in ("TEXTO_LIVRE", "INVALIDO"):
                if cid == "arvore" and isinstance(c.value, str) and _SEM_ARVORES.search(c.value):
                    iss.add(idx, line, c.coord, nome, "ANOTACAO_PARCELA",
                            "Anotação de parcela na coluna Árvore (ex.: 'NÃO TEM ÁRVORES'). "
                            "Não é um indivíduo; não é tratada como mortalidade.",
                            BLOQUEANTE, REC_HUMANA, c.value, "registro excluído das análises de indivíduo")
                else:
                    iss.add(idx, line, c.coord, nome, f"{code}_NAO_NUMERICA",
                            f"{nome} não numérica (texto livre).", BLOQUEANTE, REC_HUMANA, c.value,
                            "registro não identificável; excluído")
                blocking = True
        rec["anotacao_parcela"] = rec["arvore_tipo"] in ("TEXTO_LIVRE",) and isinstance(rec["arvore_orig"], str) \
            and bool(_SEM_ARVORES.search(rec["arvore_orig"]))

        # ---- espécie
        c = _cell(row.cells, cmap, "especie")
        sp = None if c.is_empty or str(c.value).strip() == "" else str(c.value).strip()
        rec["especie"] = sp
        rec["especie_orig"] = c.value
        if sp is None and not rec["anotacao_parcela"]:
            iss.add(idx, line, c.coord, LABEL["especie"], "ESPECIE_AUSENTE", "Espécie (Nome Comum) ausente.",
                    ADVERTENCIA, REC_IRRECUPERAVEL, None, "excluído das análises por espécie")
        elif sp is not None and re.match(r"^n[aã]o identificad", fold(sp)):
            iss.add(idx, line, c.coord, LABEL["especie"], "ESPECIE_NAO_IDENTIFICADA",
                    "Táxon não identificado (rótulo de morfoespécie); contado como táxon distinto na riqueza observada.",
                    INFORMATIVO, REC_ADVERTENCIA, sp)
        if sp is not None and obs.has_species_doubt(obs_text):
            iss.add(idx, line, oc.coord, LABEL["observacao"], "ESPECIE_DUVIDA",
                    "Observação indica dúvida de identificação da espécie.", INFORMATIVO, REC_HUMANA, obs_text)

        # ---- datas
        for cid in ("plantio", "replantio", "data_medicao"):
            c = _cell(row.cells, cmap, cid)
            p = parse_date(c)
            rec[cid] = p.value
            rec[f"{cid}_orig"] = c.value
            rec[f"{cid}_status"] = p.status if cid in cmap.mapping else "NÃO COLETADO"
            if cid != "data_medicao":
                if p.status in ("INVALIDA", "SERIAL"):
                    iss.add(idx, line, c.coord, LABEL[cid], f"{cid.upper()}_INVALIDA",
                            f"{LABEL[cid]} inválida ou número serial não convertido.", ADVERTENCIA, REC_HUMANA, c.value)
                continue
            if rec["anotacao_parcela"]:
                continue
            if p.status == "AUSENTE":
                iss.add(idx, line, c.coord, LABEL[cid], "DATA_AUSENTE",
                        "Data de medição ausente: identidade da medição inconclusiva.", ADVERTENCIA,
                        REC_IRRECUPERAVEL, None, "registro INCONCLUSIVO")
            elif p.status == "INVALIDA":
                iss.add(idx, line, c.coord, LABEL[cid], "DATA_INVALIDA", "Data de medição inválida.",
                        ADVERTENCIA, REC_HUMANA, c.value, "registro INCONCLUSIVO")
            elif p.status == "SERIAL":
                iss.add(idx, line, c.coord, LABEL[cid], "DATA_SERIAL",
                        "Número na coluna de data: não convertido sem decisão explícita.", ADVERTENCIA,
                        REC_HUMANA, c.value, "registro INCONCLUSIVO")
        if rec["plantio"] and rec["data_medicao"] and rec["data_medicao"] < rec["plantio"]:
            iss.add(idx, line, _cell(row.cells, cmap, "data_medicao").coord, LABEL["data_medicao"],
                    "DATA_ANTERIOR_PLANTIO", "Data de medição anterior ao plantio.", ADVERTENCIA, REC_HUMANA,
                    rec["data_medicao_orig"])

        # ---- medições
        for cid in ("dap_cm",) + HEIGHT_COLUMNS:
            c = _cell(row.cells, cmap, cid)
            if cid not in cmap.mapping:
                rec[cid], rec[f"{cid}_status"], rec[f"{cid}_motivo"], rec[f"{cid}_pista"] = np.nan, "NÃO COLETADO", "coluna não mapeada", None
                rec[f"{cid}_orig"] = None
                rec[f"{cid}_tipo_origem"] = None
                continue
            if rec["anotacao_parcela"]:
                v, st, mot, hint = np.nan, MED_NA, "anotação de parcela (não é indivíduo)", None
            else:
                v, st, mot, hint = _measure(c, cid, cid == "dap_cm", iss, idx, line, obs_text, pos)
            rec[cid], rec[f"{cid}_status"], rec[f"{cid}_motivo"], rec[f"{cid}_pista"] = v, st, mot, hint
            rec[f"{cid}_orig"] = c.value
            rec[f"{cid}_tipo_origem"] = c.kind

        # ---- coerência entre alturas: por definição, HT vai do solo ao ápice (Manual CEPLAC;
        #      Soares et al., 2007), logo nenhuma altura parcial pode excedê-la. Nada é corrigido.
        if rec.get("ht_m_status") == MED_MEDIDO:
            for cid in ("hc_m", "hesg_m", "hesgcopa_m"):
                if rec.get(f"{cid}_status") == MED_MEDIDO and rec[cid] > rec["ht_m"]:
                    iss.add(idx, line, _cell(row.cells, cmap, cid).coord, LABEL[cid], "ALTURA_PARCIAL_MAIOR_QUE_HT",
                            f"{LABEL[cid]} = {rec[cid]:g} m maior que HT = {rec['ht_m']:g} m: incoerente com a "
                            "definição de altura total. Valores preservados; requer revisão.",
                            ADVERTENCIA, REC_HUMANA, rec[f"{cid}_orig"])

        # ---- estado vital estruturado (somente se a coluna existir)
        if "estado_vital" in cmap.mapping:
            c = _cell(row.cells, cmap, "estado_vital")
            rec["estado_vital"] = None if c.is_empty else fold(str(c.value)).strip()
        else:
            rec["estado_vital"] = None

        # ---- linha deslocada (padrão de tipos incompatível)
        num_text = sum(1 for cid in ("dap_cm", "ht_m", "hesgcopa_m")
                       if cid in cmap.mapping and rec[f"{cid}_status"] == MED_INVALIDO
                       and _cell(row.cells, cmap, cid).kind == "texto")
        sp_numeric = sp is not None and parse_number(Cell(sp, "texto")).status == "NUMERO"
        if num_text >= 2 and sp_numeric:
            iss.add(idx, line, _cell(row.cells, cmap, "especie").coord, "(estrutura)", "LINHA_DESLOCADA",
                    "Padrão de tipos incompatível (texto em colunas numéricas e número em Nome Comum): possível linha deslocada.",
                    BLOQUEANTE, REC_HUMANA, sp, "registro excluído")
            blocking = True

        # ---- menções relevantes na observação
        if rec["mencao_morte"]:
            iss.add(idx, line, oc.coord, LABEL["observacao"], "MENCAO_MORTE",
                    "Observação menciona morte. Não é estado vital estruturado; requer revisão.",
                    ADVERTENCIA, REC_HUMANA, obs_text, "não usado para mortalidade")
        if rec["mencao_multifuste"]:
            iss.add(idx, line, oc.coord, LABEL["observacao"], "MENCAO_MULTIFUSTE",
                    "Indício de multifuste/bifurcação ou lista de diâmetros na observação (ver tabela Multifustes).",
                    ADVERTENCIA, REC_HUMANA, obs_text)
        if rec["mencao_tombamento"]:
            iss.add(idx, line, oc.coord, LABEL["observacao"], "MENCAO_TOMBAMENTO", "Observação menciona tombamento.",
                    ADVERTENCIA, REC_HUMANA, obs_text)
        if rec["mencao_quebra"]:
            iss.add(idx, line, oc.coord, LABEL["observacao"], "MENCAO_FUSTE_QUEBRADO",
                    "Observação menciona quebra/fuste partido.", ADVERTENCIA, REC_HUMANA, obs_text)
        if rec["mencao_rebrotacao"]:
            iss.add(idx, line, oc.coord, LABEL["observacao"], "MENCAO_REBROTACAO", "Observação menciona rebrotação.",
                    INFORMATIVO, REC_HUMANA, obs_text)
        if obs_text and "\n" in obs_text:
            iss.add(idx, line, oc.coord, LABEL["observacao"], "OBSERVACAO_MULTILINHA",
                    "Observação com quebra de linha (preservada).", INFORMATIVO, REC_VALIDO, obs_text)

        rec["_bloqueante"] = blocking
        out.append(rec)

    df = pd.DataFrame(out)
    if df.empty:
        return QualityResult(df, pd.DataFrame(columns=["registro"]), cmap)

    # ---- identidade de indivíduo e medição
    ident_ok = ~df["_bloqueante"] & df["parcela"].notna() & df["arvore"].notna()
    df["individuo_id"] = np.where(ident_ok, df["parcela"].astype(str) + " | " + df["arvore"].astype(str), None)
    data_str = df["data_medicao"].map(lambda d: d.isoformat() if d else "")
    df["medicao_id"] = np.where(ident_ok & (data_str != ""), df["individuo_id"].astype(str) + " | " + data_str, None)
    df["n_registros_individuo"] = df.groupby("individuo_id")["_registro"].transform("count").where(ident_ok)
    df["n_datas_individuo"] = df.groupby("individuo_id")["data_medicao"].transform(
        lambda s: s.dropna().nunique()).where(ident_ok)
    df["n_registros_medicao"] = df.groupby("medicao_id")["_registro"].transform("count").where(df["medicao_id"].notna())
    for _, r in df[df["n_registros_medicao"] > 1].iterrows():
        iss.add(r["_registro"], r["_linha"], "", "Parcela + Árvore + Data Medição", "DUPLICIDADE_MEDICAO",
                f"Chave {r['medicao_id']} repetida {int(r['n_registros_medicao'])} vezes. Nenhum registro descartado.",
                ADVERTENCIA, REC_HUMANA, r["medicao_id"], "registro INCONCLUSIVO; excluído dos indicadores dendrométricos")
    for _, r in df[(df["n_registros_individuo"] > 1) & ~(df["n_registros_medicao"] > 1)].iterrows():
        iss.add(r["_registro"], r["_linha"], "", "Parcela + Árvore", "DUPLICIDADE_INDIVIDUO",
                f"Indivíduo {r['individuo_id']} com {int(r['n_registros_individuo'])} registros "
                f"({int(r['n_datas_individuo'] or 0)} datas distintas): possível múltiplas campanhas.",
                INFORMATIVO, REC_ADVERTENCIA, r["individuo_id"])

    # ---- variações de grafia de espécie (não unificadas)
    groups: dict[str, set[str]] = defaultdict(set)
    for s in df["especie"].dropna().unique():
        groups[_species_key(s)].add(s)
    variants = [sorted(v) for v in groups.values() if len(v) > 1]
    var_set = {s for g in variants for s in g}
    for _, r in df[df["especie"].isin(var_set)].iterrows():
        grupo = next(g for g in variants if r["especie"] in g)
        iss.add(r["_registro"], r["_linha"], "", LABEL["especie"], "ESPECIE_GRAFIA_VARIANTE",
                f"Possível variação de grafia: {' / '.join(grupo)}. Não unificado automaticamente.",
                ADVERTENCIA, REC_HUMANA, r["especie"], "contadas como espécies distintas")

    issues = pd.DataFrame(iss.rows)
    if issues.empty:
        issues = pd.DataFrame(columns=["registro", "linha", "célula", "campo", "código", "descrição",
                                       "severidade", "recuperação", "valor original", "impacto"])

    # ---- status do registro
    sev = issues.groupby("registro")["severidade"].agg(set) if not issues.empty else pd.Series(dtype=object)
    codes = issues.groupby("registro")["código"].agg(set) if not issues.empty else pd.Series(dtype=object)
    inconclusive_codes = {"DATA_AUSENTE", "DATA_INVALIDA", "DATA_SERIAL", "DUPLICIDADE_MEDICAO"}

    def status_of(i: int) -> str:
        s = sev.get(i, set())
        c = codes.get(i, set())
        if BLOQUEANTE in s:
            return REG_INVALIDO
        if c & inconclusive_codes:
            return REG_INCONCLUSIVO
        if ADVERTENCIA in s:
            return REG_RESSALVA
        return REG_VALIDO

    df["status_registro"] = [status_of(i) for i in df["_registro"]]
    df["motivos"] = [
        "; ".join(sorted(codes.get(i, set()))) for i in df["_registro"]
    ]
    df["identificavel"] = ident_ok
    df["_ord"] = [natural_key(p) + natural_key(a) for p, a in zip(df["parcela"], df["arvore"])]
    if not issues.empty:
        issues = issues.merge(df[["_registro", "status_registro"]], left_on="registro", right_on="_registro",
                              how="left").drop(columns="_registro")
    return QualityResult(df, issues, cmap, variants)


def campaign_summary(records: pd.DataFrame) -> dict:
    """Possíveis campanhas: estimativa pelo máximo de datas distintas por indivíduo."""
    ok = records[records["identificavel"]]
    datas = ok["data_medicao"].dropna()
    max_d = int(ok["n_datas_individuo"].max()) if len(ok) and ok["n_datas_individuo"].notna().any() else 0
    return {
        "possiveis_campanhas": max_d,
        "individuos_com_multiplas_datas": int((ok.drop_duplicates("individuo_id")["n_datas_individuo"] > 1).sum()),
        "datas_distintas": int(datas.nunique()),
        "primeira_data": min(datas) if len(datas) else None,
        "ultima_data": max(datas) if len(datas) else None,
        "criterio": "máximo de datas de medição distintas observadas para um mesmo indivíduo (Parcela + Árvore)",
    }


def measurement_status_table(records: pd.DataFrame) -> pd.DataFrame:
    """Contagem de estados por campo de medição, sobre registros potenciais (identificáveis)."""
    pot = records[records["identificavel"] & ~records["anotacao_parcela"]] if len(records) else records
    rows = []
    for cid in ("dap_cm",) + HEIGHT_COLUMNS:
        st = pot[f"{cid}_status"].value_counts() if len(pot) else pd.Series(dtype=int)
        if st.get("NÃO COLETADO", 0) == len(pot) and len(pot):
            continue
        rows.append({"campo": LABEL[cid], "registros potenciais": len(pot),
                     **{s: int(st.get(s, 0)) for s in (MED_MEDIDO, MED_AUSENTE, MED_INVALIDO, MED_NA, MED_EXTREMO, MED_REVISAO)}})
    for cid in ("especie", "data_medicao"):
        col = cid
        aus = int(pot[col].isna().sum()) if len(pot) else 0
        rows.append({"campo": LABEL[cid], "registros potenciais": len(pot), MED_MEDIDO: len(pot) - aus, MED_AUSENTE: aus})
    return pd.DataFrame(rows).fillna(0)
