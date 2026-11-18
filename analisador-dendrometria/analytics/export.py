"""Exportação (XLSX, CSV, JSON, HTML) e manifesto de execução."""
from __future__ import annotations

import datetime as dt
import html
import io
import json
from typing import Any

import pandas as pd

from . import AnalysisResult, Filters
from . import dendrometry as dd
from .canonicalization import LABEL, ColumnMapping
from .ingestion import ImportMetadata
from .inventory import PENDENTES
from .quality import DAP_LIMITE_LEGADO_CM, REG_INVALIDO, QualityResult
from .results import ANALISADOR_VERSAO, ESTADOS_SEM_VALOR, TOLERANCIAS, VERSAO_METODOLOGICA, indicadores_para_tabela

DECISOES_METODOLOGICAS = [
    "Indivíduo = Parcela + Árvore; medição = Parcela + Árvore + Data Medição (provisório, seção 12).",
    "Identificadores: remoção apenas de espaço externo; '7', '07' e '007' permanecem distintos.",
    "Separador decimal: vírgula ou ponto (um único); '1.2,5' é inválido.",
    "Política única de elegibilidade de DAP: MEDIDO (> 0), não duplicado, ≤ 300 cm salvo opção explícita.",
    f"Limite de {DAP_LIMITE_LEGADO_CM:g} cm: REGRA LEGADA NÃO VALIDADA METODOLOGICAMENTE.",
    "Área seccional g = π·DAP²/40000 (m²); área basal G = Σg (absoluta, não por hectare).",
    "Diâmetro: 'Média aritmética do DAP' e 'Diâmetro quadrático médio (dg)' (literatura) apresentados separados; "
    "o 'diâmetro médio oficial' do projeto é decisão M5.",
    "Área basal por hectare somente com área + desenho amostral (predefinição da literatura para o arboreto ESARM "
    "ou informados pelo usuário); parcelas sem área ficam fora de G e de A.",
    "Multifuste: regra de Finger (1992) / Manual CEPLAC — g do indivíduo = Σ g dos fustes; DAP equivalente = √(Σd²); "
    "fustes extraídos só por padrão estrutural (quantidade declarada = valores listados).",
    "Diversidade: Shannon (ln), Pielou, Simpson (1 − D, sem reposição) sobre indivíduos únicos (Brower & Zar, 1984).",
    "Fitossociologia: DR, DoR, FA, FR, VI (Mueller-Dombois & Ellenberg, 1974).",
    "Limite físico de altura 120 m (maior árvore viva medida ≈ 116 m); HC/HESG/HESGCOPA ≤ HT por definição.",
    "Siglas (equipe, 17/11/2026): HESG = altura do esgalhamento (solo até o 1º galho vivo); HESGCOPA = altura da formação "
    "da copa (solo até o início da copa); HC = altura comercial; HT = altura total (solo até o ápice). Copa = HT − HESGCOPA.",
    "Alturas HESG, HESGCOPA, HC e HT tratadas separadamente; 'Altura total média' somente para HT.",
    "Volume cilíndrico v = g·HT (sem fator de forma), conforme orientação em áudio de 17/11/2026.",
    "Volume comercial por Spurr (Jorge, 1982) apenas com HC: Vc = 0,106531813 + 5,3372e-5·DAP²·HC.",
    "Quartis por interpolação linear (Hyndman & Fan tipo 7); desvio-padrão amostral (n − 1).",
    "Distribuição diamétrica exploratória com classes [a; b) de largura escolhida pelo usuário.",
    "Mortalidade/sobrevivência apenas com estado vital estruturado; denominador configurável (padrão 36).",
    "Datas em colunas numéricas não são reconstruídas; o texto exibido serve só de pista para revisão.",
]


def excluded_records(records: pd.DataFrame, incluir_extremos: bool = False) -> pd.DataFrame:
    """Um registro por (registro, cálculo) do qual foi excluído, com o motivo."""
    rows = []
    for _, r in records[records["status_registro"] == REG_INVALIDO].iterrows():
        rows.append({"linha": r["_linha"], "parcela (original)": r["parcela_orig"], "árvore (original)": r["arvore_orig"],
                     "espécie": r["especie"], "excluído de": "todas as análises de indivíduo",
                     "motivo": r["motivos"], "valor original": "", "status do registro": r["status_registro"]})
    if len(records):
        el = dd.individual_table(records, incluir_extremos)
        for _, r in el[~el["dap_elegivel"]].iterrows():
            rows.append({"linha": r["_linha"], "parcela (original)": r["parcela_orig"], "árvore (original)": r["arvore_orig"],
                         "espécie": r["especie"], "excluído de": "indicadores de DAP, área basal e volumes",
                         "motivo": r["dap_motivo_exclusao"], "valor original": r["dap_cm_orig"],
                         "status do registro": r["status_registro"]})
        for col in ("ht_m", "hc_m", "hesg_m", "hesgcopa_m"):
            sub = el[~el[f"{col}_elegivel"] & (el[f"{col}_status"] != "AUSENTE") & (el[f"{col}_status"] != "NÃO COLETADO")]
            for _, r in sub.iterrows():
                rows.append({"linha": r["_linha"], "parcela (original)": r["parcela_orig"],
                             "árvore (original)": r["arvore_orig"], "espécie": r["especie"],
                             "excluído de": f"indicadores de {LABEL[col]}", "motivo": r[f"{col}_motivo_exclusao"],
                             "valor original": r[f"{col}_orig"], "status do registro": r["status_registro"]})
    cols = ["linha", "parcela (original)", "árvore (original)", "espécie", "excluído de", "motivo",
            "valor original", "status do registro"]
    out = pd.DataFrame(rows, columns=cols)
    for c in ("parcela (original)", "árvore (original)", "valor original"):
        out[c] = out[c].map(lambda v: "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v))
    return out.sort_values(["linha", "excluído de"]).reset_index(drop=True)


def quality_report(q: QualityResult) -> pd.DataFrame:
    if q.issues.empty:
        return pd.DataFrame(columns=["código", "severidade", "recuperação", "ocorrências", "registros"])
    g = q.issues.groupby(["código", "severidade", "recuperação"]).agg(
        ocorrências=("registro", "size"), registros=("registro", "nunique")).reset_index()
    return g.sort_values(["severidade", "ocorrências"], ascending=[True, False]).reset_index(drop=True)


def original_with_diagnosis(q: QualityResult) -> pd.DataFrame:
    df = q.records
    keep = {"_linha": "linha"}
    for cid, label in LABEL.items():
        if f"{cid}_orig" in df.columns:
            keep[f"{cid}_orig"] = f"{label} (original)"
    if "observacao" in df.columns:
        keep["observacao"] = "Observação (original)"
    keep.update({"status_registro": "status do registro", "motivos": "diagnósticos"})
    out = df[[c for c in keep if c in df.columns]].rename(columns=keep)
    return _stringify_objects(out)


def normalized_table(q: QualityResult) -> pd.DataFrame:
    df = q.records
    cols = ["_linha", "parcela", "parcela_tipo", "arvore", "arvore_tipo", "especie", "data_medicao",
            "data_medicao_status", "dap_cm", "dap_cm_status", "dap_cm_motivo", "dap_cm_pista", "hesg_m", "hesg_m_status",
            "hesgcopa_m", "hesgcopa_m_status", "hc_m", "hc_m_status", "ht_m", "ht_m_status", "observacao",
            "obs_termos", "individuo_id", "medicao_id", "status_registro", "motivos"]
    return _stringify_objects(df[[c for c in cols if c in df.columns]].copy())


def _stringify_objects(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in out.columns:
        if out[c].dtype == object:
            out[c] = out[c].map(lambda v: v.isoformat() if isinstance(v, (dt.date, dt.datetime)) else v)
    return out


def build_manifest(meta: ImportMetadata, q: QualityResult, res: AnalysisResult, filters: Filters,
                   params: dict[str, Any]) -> dict:
    inds = res.all_indicators()
    st = q.records["status_registro"].value_counts().to_dict() if len(q.records) else {}
    return {
        "analisador": "Analisador de Dendrometria", "versao_analisador": ANALISADOR_VERSAO,
        "versao_metodologica": VERSAO_METODOLOGICA,
        "data_hora_execucao": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "arquivos": [{"nome": meta.nome_arquivo, "sha256": meta.sha256, "tamanho_bytes": meta.tamanho_bytes,
                      "formato": meta.formato, "codificacao": meta.codificacao, "separador": meta.separador}],
        "planilhas_processadas": [meta.planilha] if meta.planilha else [],
        "planilhas_disponiveis": meta.planilhas_disponiveis,
        "numero_linhas_fisicas": meta.linhas_fisicas,
        "registros_interpretados": meta.registros_interpretados,
        "linhas_vazias_ignoradas": meta.linhas_vazias_ignoradas,
        "registros_por_status": st,
        "registros_validos": st.get("VÁLIDO", 0), "registros_com_ressalva": st.get("VÁLIDO COM RESSALVA", 0),
        "registros_invalidos": st.get("INVÁLIDO", 0), "registros_inconclusivos": st.get("INCONCLUSIVO", 0),
        "avisos": int((q.issues["severidade"] == "ADVERTÊNCIA").sum()) if len(q.issues) else 0,
        "ocorrencias_bloqueantes": int((q.issues["severidade"] == "BLOQUEANTE").sum()) if len(q.issues) else 0,
        "mapeamento_colunas": q.mapping.originals,
        "filtros_aplicados": filters.describe(), "registros_apos_filtro": res.n_registros,
        "parametros": params,
        "indicadores_calculados": [{"id": i.id, "nome": i.nome, "valor": i.valor, "unidade": i.unidade,
                                    "status": i.status, "elegivel": i.quantidade_elegivel,
                                    "potencial": i.quantidade_potencial} for i in inds if i.disponivel],
        "indicadores_bloqueados": [{"id": i.id, "nome": i.nome, "status": i.status, "motivo": " ".join(i.observacoes)}
                                   for i in inds if i.status in ESTADOS_SEM_VALOR]
        + [{"id": None, "nome": n, "status": "PENDENTE DE DEFINIÇÃO", "motivo": m} for n, m in PENDENTES],
        "decisoes_metodologicas": DECISOES_METODOLOGICAS + res.metodologia.decisoes(),
        "decisoes_do_usuario": res.metodologia.describe(),
        "tolerancias_numericas": {k: {"atol": t.atol, "rtol": t.rtol, "justificativa": t.justificativa}
                                  for k, t in TOLERANCIAS.items()},
    }


def manifest_json(manifest: dict) -> bytes:
    return json.dumps(manifest, ensure_ascii=False, indent=2, default=str).encode("utf-8")


def indicators_table(res: AnalysisResult) -> pd.DataFrame:
    return pd.DataFrame(indicadores_para_tabela(res.all_indicators()))


def export_tables(meta: ImportMetadata, q: QualityResult, res: AnalysisResult, incluir_extremos: bool) -> dict[str, pd.DataFrame]:
    return {
        "01_originais_diagnostico": original_with_diagnosis(q),
        "02_normalizados": normalized_table(q),
        "03_registros_invalidos": original_with_diagnosis(q)[q.records["status_registro"].values == REG_INVALIDO],
        "04_registros_excluidos": excluded_records(q.records, incluir_extremos),
        "05_indicadores_gerais": indicators_table(res),
        "06_resultados_parcela": res.parcelas,
        "07_resultados_especie": res.especies,
        "08_resultados_individuo": _stringify_objects(res.individuos),
        "08b_multifustes": res.multifustes,
        "09_relatorio_qualidade": quality_report(q),
        "09b_ocorrencias_qualidade": q.issues,
    }


def to_xlsx(tables: dict[str, pd.DataFrame], manifest: dict | None = None) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, df in tables.items():
            _stringify_objects(df).to_excel(xw, sheet_name=name[:31], index=False)
        if manifest is not None:
            flat = pd.DataFrame([(k, json.dumps(v, ensure_ascii=False, default=str) if isinstance(v, (dict, list)) else v)
                                 for k, v in manifest.items()], columns=["campo", "valor"])
            flat.to_excel(xw, sheet_name="10_manifesto", index=False)
        for ws in xw.book.worksheets:
            ws.freeze_panes = "A2"
            for col in ws.columns:
                width = max(len(str(c.value)) if c.value is not None else 0 for c in list(col)[:200])
                ws.column_dimensions[col[0].column_letter].width = min(max(10, width + 2), 60)
    return buf.getvalue()


def to_csv(df: pd.DataFrame) -> bytes:
    return _stringify_objects(df).to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")


def to_html_report(meta: ImportMetadata, q: QualityResult, res: AnalysisResult, manifest: dict) -> bytes:
    def table(df: pd.DataFrame, max_rows: int = 500) -> str:
        return _stringify_objects(df.head(max_rows)).to_html(index=False, na_rep="—", border=0, classes="t")

    parts = [
        "<!DOCTYPE html><html lang='pt-BR'><head><meta charset='utf-8'><title>Relatório — Dendrometria</title>",
        "<style>body{font-family:Segoe UI,Arial,sans-serif;color:#1f2937;margin:32px;max-width:1200px}"
        "h1{color:#1F3A5F}h2{color:#1F3A5F;border-bottom:2px solid #e5e7eb;padding-bottom:4px;margin-top:32px}"
        "table.t{border-collapse:collapse;font-size:12px;width:100%}table.t th{background:#1F3A5F;color:#fff;"
        "text-align:left;padding:6px}table.t td{border-bottom:1px solid #e5e7eb;padding:4px 6px}"
        ".m{color:#6b7280;font-size:13px}</style></head><body>",
        f"<h1>Relatório de Dendrometria</h1><p class='m'>Arquivo: {html.escape(meta.nome_arquivo)} · SHA-256 "
        f"{meta.sha256} · planilha {html.escape(str(meta.planilha))} · gerado em {manifest['data_hora_execucao']} · "
        f"analisador {ANALISADOR_VERSAO} · metodologia {VERSAO_METODOLOGICA}</p>",
        f"<p class='m'>Filtros: {html.escape(json.dumps(manifest['filtros_aplicados'], ensure_ascii=False, default=str)) or 'nenhum'}</p>",
        "<h2>Indicadores</h2>", table(indicators_table(res)),
        "<h2>Qualidade dos dados</h2>", table(quality_report(q)),
        "<h2>Resultados por parcela</h2>", table(res.parcelas),
        "<h2>Resultados por espécie</h2>", table(res.especies),
        "<h2>Indicadores pendentes de definição</h2>",
        table(pd.DataFrame(PENDENTES, columns=["indicador", "motivo"])),
        "</body></html>",
    ]
    return "".join(parts).encode("utf-8")
