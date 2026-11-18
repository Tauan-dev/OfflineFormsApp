import datetime as dt

import pytest
from conftest import SYN, load

from analytics import canonicalization as canon
from analytics import ingestion
from analytics.ingestion import Cell


def test_xlsx_valido_lista_planilhas_e_preserva_tipos():
    data = (SYN / "valido.xlsx").read_bytes()
    assert ingestion.list_sheets(data) == ["dendrometria", "MAPA"]
    raw = ingestion.read_xlsx(data, "valido.xlsx", "dendrometria")
    assert raw.meta.planilha == "dendrometria"
    assert raw.meta.cabecalhos[6] == "DAP (cm)"
    assert raw.meta.linhas_vazias_ignoradas == 1
    assert raw.meta.registros_interpretados == 6
    assert len(raw.meta.sha256) == 64
    dap = [r.cells[6] for r in raw.rows]
    assert dap[0].kind == "inteiro"
    assert dap[1].kind == "texto" and dap[1].value == "20.5"
    assert dap[2].kind == "data" and dap[2].coord == "G4" and "d" in dap[2].number_format


def test_csv_valido():
    raw, q = load("valido.csv")
    assert raw.meta.separador == ","
    assert raw.meta.codificacao == "utf-8"
    assert raw.meta.registros_interpretados == 5
    assert raw.meta.linhas_fisicas == 6
    assert (q.records["status_registro"] == "VÁLIDO").all()


def test_csv_com_bom_e_ponto_e_virgula():
    raw, q = load("bom_ponto_virgula.csv")
    assert raw.meta.codificacao == "utf-8 com BOM"
    assert raw.meta.separador == ";"
    assert raw.headers[0] == "Parcela"  # BOM não contamina o cabeçalho
    assert q.records["dap_cm"].tolist() == [12.5, 35.0]  # vírgula decimal e espaço externo
    assert "ESPACO_EXTERNO" in set(q.issues["código"])


def test_csv_multilinha_virgula_aspas_crlf_sem_quebra_final():
    raw, q = load("multilinha_virgula.csv")
    assert raw.meta.registros_interpretados == 3
    obs = q.records["observacao"].tolist()
    assert obs[0] == "Brotação na base, com dano"
    assert obs[1] == 'linha 1\r\nlinha 2 com "aspas"'
    assert obs[2] is None  # campo final vazio preservado como vazio
    assert raw.rows[1].line == 3 and raw.rows[1].line_end == 4
    assert raw.rows[2].line == 5  # última linha sem quebra
    assert (q.records["status_registro"] != "INVÁLIDO").all()


def test_campo_final_vazio_mantem_numero_de_campos():
    raw, _ = load("multilinha_virgula.csv")
    assert raw.rows[2].n_fields == 12


def test_linha_deslocada_e_fragmento():
    _, q = load("problemas.csv")
    codes = q.issues.groupby("linha")["código"].agg(set)
    assert "COLUNAS_EXCEDENTES" in codes[14]
    assert "OBSERVACAO_FRAGMENTADA" in codes[15]
    assert "QTD_COLUNAS_INCORRETA" in codes[16]  # "1.2,5" sem aspas desloca a linha
    st = q.records.set_index("_linha")["status_registro"]
    assert st[14] == st[15] == st[16] == "INVÁLIDO"


def test_formato_nao_suportado():
    with pytest.raises(ValueError):
        ingestion.detect_format("dados.ods")


def test_mapeamento_aliases_explicitos_e_obrigatoria_ausente():
    m = canon.auto_map(["Parcela", "Arvore", "Nome comum", "Data medicao", "DAP", "HT"])
    assert m.is_safe and m.mapping["arvore"] == 1 and m.mapping["ht_m"] == 5
    m2 = canon.auto_map(["Parcela", "Arv", "Nome Comum", "Data Medição", "DAP (cm)"])
    assert m2.missing_required == ["arvore"] and not m2.is_safe
    m3 = canon.manual_map(["Parcela", "Arv", "Nome Comum", "Data Medição", "DAP (cm)"],
                          {"parcela": "Parcela", "arvore": "Arv", "especie": "Nome Comum",
                           "data_medicao": "Data Medição", "dap_cm": "DAP (cm)"})
    assert m3.is_safe


def test_mapeamento_ambiguo_nao_e_seguro():
    m = canon.auto_map(["Parcela", "Árvore", "Arvore", "Nome Comum", "Data Medição", "DAP (cm)"])
    assert "arvore" in m.ambiguous and not m.is_safe


def test_parse_number_casos():
    P = canon.parse_number
    assert P(Cell("12,5", "texto")).value == 12.5
    assert P(Cell("12.5", "texto")).value == 12.5
    assert P(Cell("1.2,5", "texto")).status == "TEXTO"
    assert P(Cell("MORTA", "texto")).status == "TEXTO"
    assert P(Cell(None, "vazio")).status == "AUSENTE"
    assert P(Cell(float("inf"), "decimal")).status == "NAO_FINITO"
    assert P(Cell("nan", "texto")).status == "NAO_FINITO"
    d = P(Cell(dt.datetime(2026, 5, 12), "data", "d\\.m"))
    assert d.status == "DATA" and d.value is None and d.display_hint == "12.5"


def test_identificadores_nao_unificam_zeros():
    I = canon.parse_id
    assert I(Cell("07", "texto")).value == "07"
    assert I(Cell(7, "inteiro")).value == "7"
    assert I(Cell(" 7 ", "texto")).value == "7"
    assert I(Cell("PX1", "texto")).status == "CODIGO"
    assert I(Cell("NÃO TEM ÁRVORES", "texto")).status == "TEXTO_LIVRE"


def test_datas():
    D = canon.parse_date
    assert D(Cell("31/02/2025", "texto")).status == "INVALIDA"
    assert D(Cell(45123, "inteiro")).status == "SERIAL"
    assert D(Cell("28/07/2026", "texto")).value == dt.date(2026, 7, 28)
