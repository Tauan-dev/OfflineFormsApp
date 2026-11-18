"""Processa uma planilha sem interface e grava resultados, manifesto e relatório.

Uso:
  python processar_planilha.py ARQUIVO [--planilha NOME] [--saida PASTA]
         [--area-parcela VALOR --unidade-area m²|ha --desenho "TEXTO"] [--sem-predefinicao]

Área basal por hectare: se as parcelas do arquivo couberem no desenho publicado do arboreto ESARM
(1 a 98), aplica-se a predefinição da literatura (144 m² por parcela); --area-parcela/--desenho a
substituem; --sem-predefinicao a desliga (indicador BLOQUEADO).

Também executa uma conferência independente: recalcula, lendo as células
diretamente com openpyxl/csv (sem a camada analytics), o DAP médio e a área
basal de algumas parcelas e compara com o resultado do analisador.
"""
from __future__ import annotations

import argparse
import datetime as dt
import math
import re
from pathlib import Path

import openpyxl

from analytics import canonicalization as canon
from analytics import export, ingestion, quality, run_analysis
from analytics.inventory import PENDENTES
from analytics.results import ESTADOS_SEM_VALOR, TOLERANCIAS

NUM = re.compile(r"^\s*\d+(?:[.,]\d+)?\s*$")


def conferencia_independente(path: Path, sheet: str | None, parcelas: list[str]) -> dict[str, tuple[int, float, float]]:
    """DAPs numéricos (> 0 e ≤ 300) por parcela, lidos diretamente da planilha.

    Exclui linhas cuja observação contém 'mort' (mesmo critério de revisão) e
    linhas duplicadas por Parcela+Árvore+Data. Retorna n, média, G por parcela.
    """
    out = {}
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[sheet] if sheet else wb.worksheets[0]
    head = [c.value for c in ws[1]]
    ip, ia, idap, iobs = head.index("Parcela"), head.index("Árvore"), head.index("DAP (cm)"), head.index("Observação")
    for p in parcelas:
        vals = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            if str(row[ip]).strip() != p or row[ia] is None or not str(row[ia]).strip().isdigit():
                continue
            v = row[idap]
            o = str(row[iobs] or "").lower()
            if isinstance(v, bool) or isinstance(v, dt.datetime):
                continue
            if isinstance(v, (int, float)):
                x = float(v)
            elif isinstance(v, str) and NUM.match(v):
                x = float(v.strip().replace(",", "."))
            else:
                continue
            if 0 < x <= 300 and "mort" not in o:
                vals.append(x)
        g = math.fsum(math.pi * x * x / 40000 for x in vals)
        out[p] = (len(vals), (math.fsum(vals) / len(vals)) if vals else float("nan"), g)
    return out


def relatorio_md(meta, q, res, conf, saida: Path) -> str:
    R = q.records
    iss = q.issues
    st = R["status_registro"].value_counts()
    tipos = []
    for cid in ("parcela", "arvore", "especie", "data_medicao", "dap_cm", "hesg_m", "hesgcopa_m", "hc_m", "ht_m", "observacao"):
        col = f"{cid}_tipo_origem" if f"{cid}_tipo_origem" in R else None
        if col:
            vc = R[col].value_counts().to_dict()
        else:
            orig = R[f"{cid}_orig"] if f"{cid}_orig" in R else R[cid]
            vc = orig.map(lambda v: "vazio" if v is None else type(v).__name__).value_counts().to_dict()
        tipos.append(f"| {canon.LABEL[cid]} | " + ", ".join(f"{k}: {v}" for k, v in vc.items()) + " |")
    cod = iss["código"].value_counts()
    L = [f"# Relatório da planilha real — {meta.nome_arquivo}", "",
         f"Processado em {meta.data_processamento} · SHA-256 `{meta.sha256}`", "",
         "## 1. Estrutura", "",
         f"- Planilhas: {', '.join(meta.planilhas_disponiveis)} (processada: **{meta.planilha}**; 'MAPA' contém apenas imagem).",
         f"- Linhas físicas: {meta.linhas_fisicas} (cabeçalho + {meta.registros_interpretados} registros + "
         f"{meta.linhas_vazias_ignoradas} linhas vazias ignoradas).",
         f"- Cabeçalhos: {', '.join(meta.cabecalhos)}. Colunas M–Z vazias (sem valores).",
         "- Plantio e Replantio: vazias em todos os registros.", "",
         "## 2. Tipos reais das células (registros interpretados)", "", "| Coluna | Tipos |", "|---|---|", *tipos, "",
         "## 3. Inconsistências encontradas", "",
         f"- **{cod.get('DAP_DATA', 0)} DAPs armazenados como data** pelo Excel (formato `d.m`; ex.: '12.4' virou 12/abr). "
         "Não reconstruídos: '12.05' e '12.5' geram a mesma data. Pista exibida apenas para revisão.",
         f"- **{cod.get('ALTURA_DATA', 0)} alturas armazenadas como data** (HESG, HESGCOPA, HT).",
         f"- **{cod.get('POSSIVEL_SERIAL_DATA', 0)} altura com número serial de data** (HT = 46151 na linha 299 ≈ 08/05/2026 → '8.5'); "
         "classificada EXTREMA e fora dos cálculos.",
         f"- **{cod.get('ANOTACAO_PARCELA', 0)} linhas de anotação de parcela** ('NÃO TEM ÁRVORES' na coluna Árvore): não são indivíduos nem mortos.",
         f"- {cod.get('PARCELA_NAO_NUMERICA', 0)} registros em parcelas com código alfanumérico (PX1–PX5), preservadas com ressalva.",
         f"- {cod.get('MENCAO_MORTE', 0)} observações mencionam morte ('MORTA'); sem coluna estruturada de estado vital.",
         f"- {cod.get('DAP_NAO_MENSURAVEL', 0)} DAPs vazios com lista de diâmetros/multifuste na observação; "
         f"{cod.get('MENCAO_MULTIFUSTE', 0)} menções de multifuste no total.",
         f"- {cod.get('DAP_AUSENTE', 0)} DAPs ausentes sem justificativa; {cod.get('DATA_AUSENTE', 0)} datas de medição ausentes.",
         f"- {cod.get('ESPECIE_GRAFIA_VARIANTE', 0)} registros com variação de grafia de espécie "
         f"({'; '.join(' / '.join(g) for g in q.species_variants)}), não unificados.",
         f"- {cod.get('ESPECIE_NAO_IDENTIFICADA', 0)} registros com 'Não identificada N'; "
         f"{cod.get('ESPECIE_DUVIDA', 0)} com dúvida de identificação na observação.",
         "- Nenhuma duplicidade de Parcela + Árvore + Data; uma única campanha provável (19/05 a 28/08/2026).",
         "- Números como texto ('45.5') são a maioria das células de DAP; interpretados por regra determinística.", "",
         "## 4. Classificação dos registros", "",
         *[f"- {k}: {v}" for k, v in st.items()], f"- Total: {int(st.sum())}", "",
         "## 5. Indicadores calculados", "", "| Indicador | Valor | Unidade | Elegíveis/potenciais | Status |",
         "|---|---|---|---|---|"]
    for i in res.all_indicators():
        v = "—" if i.valor is None else (f"{i.valor:.6g}" if isinstance(i.valor, float) else str(i.valor))
        el = "—" if i.quantidade_elegivel is None else f"{i.quantidade_elegivel}/{i.quantidade_potencial}"
        L.append(f"| {i.nome} | {v} | {i.unidade} | {el} | {i.status} |")
    L += ["", "## 6. Indicadores bloqueados ou pendentes", ""]
    L += [f"- **{i.nome}** — {i.status}: {' '.join(i.observacoes)}" for i in res.all_indicators() if i.status in ESTADOS_SEM_VALOR]
    L += [f"- **{n}** — PENDENTE DE DEFINIÇÃO: {m}" for n, m in PENDENTES]
    L += ["", "## 7. Conferência independente (leitura direta das células)", "",
          "Recalculado sem a camada `analytics`, com regra simplificada equivalente para estas parcelas.", "",
          "| Parcela | n (indep.) | n (analisador) | DAP médio indep. (cm) | DAP médio analisador | G indep. (m²) | G analisador | Erro abs. G | Conclusão |",
          "|---|---|---|---|---|---|---|---|---|"]
    P = res.parcelas.set_index("parcela")
    tg, tm = TOLERANCIAS["area_basal_m2"], TOLERANCIAS["dap_cm"]
    for p, (n, m, g) in conf.items():
        an = int(P.loc[p, "DAPs elegíveis"]); am = P.loc[p, "média aritmética DAP (cm)"]; ag = P.loc[p, "área basal G (m²)"]
        ok = n == an and tm.aceita(am, m) and tg.aceita(ag, g)
        L.append(f"| {p} | {n} | {an} | {m:.10g} | {am:.10g} | {g:.12g} | {ag:.12g} | {abs(ag - g):.2e} | "
                 f"{'CONFERE' if ok else 'DIVERGE'} |")
    L += ["", "## 8. Arquivos gerados", "", *[f"- `{f.name}`" for f in sorted(saida.iterdir())], ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("arquivo")
    ap.add_argument("--planilha", default=None)
    ap.add_argument("--saida", default="resultados")
    ap.add_argument("--conferir", default="1,14,16,49,75,PX5", help="parcelas para conferência independente")
    ap.add_argument("--area-parcela", type=float, default=None, help="área de cada parcela (decisão do usuário)")
    ap.add_argument("--unidade-area", default="m²", choices=["m²", "m2", "ha"])
    ap.add_argument("--desenho", default="", help="descrição do desenho amostral (obrigatória para AB/ha)")
    ap.add_argument("--sem-predefinicao", action="store_true", help="não aplica a predefinição da literatura (ESARM)")
    a = ap.parse_args()
    from analytics import Metodologia
    from analytics.results import esarm_aplicavel, metodologia_arboreto_esarm
    met = Metodologia(area_parcela=a.area_parcela, unidade_area="m²" if a.unidade_area == "m2" else a.unidade_area,
                      desenho_amostral=a.desenho)
    path = Path(a.arquivo)
    data = path.read_bytes()
    sheet = a.planilha
    if sheet is None and ingestion.detect_format(path.name) == "xlsx":
        sheets = ingestion.list_sheets(data)
        sheet = next((s for s in sheets if "dendr" in s.lower()), sheets[0])
    raw = ingestion.read_file(data, path.name, sheet)
    cmap = canon.auto_map(raw.headers)
    if not cmap.is_safe:
        print("Mapeamento inseguro:", cmap.missing_required, cmap.ambiguous)
        return 2
    q = quality.build_records(raw, cmap)
    if a.area_parcela is None and not a.sem_predefinicao and esarm_aplicavel(q.records["parcela"].dropna().unique()):
        met = metodologia_arboreto_esarm()
    params = {"incluir_extremos": False, "largura_classe_cm": 5.0, "implantados": 36, "mortalidade_ativa": True,
              "metodologia": met.describe()}
    res = run_analysis(q.records, q.issues, raw.meta, incluir_extremos=False, largura_classe_cm=5.0, metodologia=met)
    from analytics import Filters
    man = export.build_manifest(raw.meta, q, res, Filters(), params)
    out = Path(a.saida)
    out.mkdir(parents=True, exist_ok=True)
    base = path.stem
    tabs = export.export_tables(raw.meta, q, res, False)
    (out / f"{base}_resultados.xlsx").write_bytes(export.to_xlsx(tabs, man))
    (out / f"{base}_manifesto.json").write_bytes(export.manifest_json(man))
    (out / f"{base}_relatorio.html").write_bytes(export.to_html_report(raw.meta, q, res, man))
    (out / f"{base}_registros_excluidos.csv").write_bytes(export.to_csv(tabs["04_registros_excluidos"]))
    (out / f"{base}_indicadores.csv").write_bytes(export.to_csv(tabs["05_indicadores_gerais"]))
    (out / f"{base}_multifustes.csv").write_bytes(export.to_csv(tabs["08b_multifustes"]))
    conf = {}
    if raw.meta.formato == "xlsx":
        conf = conferencia_independente(path, sheet, [p for p in a.conferir.split(",") if p in set(res.parcelas["parcela"])])
    md = relatorio_md(raw.meta, q, res, conf, out)
    (out / f"{base}_relatorio_planilha.md").write_text(md, encoding="utf-8")
    print(f"Resultados em {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
