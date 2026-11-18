import json

from conftest import close, ind, load

from analytics import Filters, export, run_analysis
from analytics.results import BLOQ_QUALIDADE_OU_METODOLOGIA, INDISPONIVEL


def test_contagens_distinguem_registros_individuos_especies(expected):
    raw, q = load("valido.csv")
    res = run_analysis(q.records, q.issues, raw.meta)
    e = expected["valido_csv"]
    assert ind(res.gerais, "individuos").valor == e["individuos"]
    assert ind(res.gerais, "parcelas").valor == e["parcelas"]
    assert ind(res.gerais, "especies").valor == e["especies"]
    assert ind(res.gerais, "linhas_importadas").valor == 6


def test_campanhas_nao_duplicam_individuos():
    raw, q = load("problemas.csv")
    res = run_analysis(q.records, q.issues, raw.meta)
    ids = q.records.loc[q.records["identificavel"], "individuo_id"]
    assert ind(res.gerais, "individuos").valor == ids.nunique() < len(ids)
    assert ind(res.gerais, "campanhas").valor == 2
    assert ind(res.gerais, "duplicidades").valor == 2


def test_especies_rotulos_e_ocorrencia():
    _, q = load("valido.csv")
    res = run_analysis(q.records, q.issues, None)
    sp = res.especies.set_index("espécie")
    assert sp.loc["Cedro", "Abundância por indivíduos únicos"] == 2
    assert sp.loc["Cedro", "Ocorrência em parcelas"] == 2
    assert sp.loc["Ipê", "Ocorrência em parcelas"] == 1
    # "Frequência" só aparece no sentido fitossociológico (parcelas), nunca para contagem de indivíduos
    freq = [c for c in res.especies.columns if "frequência" in c.lower()]
    assert freq == ["Frequência absoluta FA (%)", "Frequência relativa FR (%)"]
    assert sp.loc["Cedro", "Frequência absoluta FA (%)"] == 100.0  # 2 de 2 parcelas
    assert sp.loc["Ipê", "Frequência absoluta FA (%)"] == 50.0


def test_parcelas_tabela():
    _, q = load("valido.csv")
    res = run_analysis(q.records, q.issues, None)
    p = res.parcelas.set_index("parcela")
    assert p.loc["1", "indivíduos"] == 3 and p.loc["1", "riqueza observada"] == 2
    close(p.loc["2", "média aritmética DAP (cm)"], 45.0, "dap_cm")


def test_mortalidade_bloqueada_sem_estado_vital():
    _, q = load("problemas.csv")
    res = run_analysis(q.records, q.issues, None)
    m = ind(res.mortalidade, "mortalidade")
    assert m.status == BLOQ_QUALIDADE_OU_METODOLOGIA and m.valor is None


def test_mortalidade_com_estado_vital_e_denominador_configuravel(expected):
    _, q = load("estado_vital.csv")
    res = run_analysis(q.records, q.issues, None, implantados=36)
    close(ind(res.mortalidade, "mortalidade").valor, expected["estado_vital"]["mortalidade_total_pct"], "percentual")
    close(ind(res.mortalidade, "sobrevivencia").valor, expected["estado_vital"]["sobrevivencia_pct"], "percentual")
    tab = res.mortalidade_tabela.set_index("parcela")
    assert tab.loc["1", "sem registro"] == 32  # 36 − 4 avaliados: NÃO são mortos
    assert tab.loc["1", "mortos"] == 1
    r2 = run_analysis(q.records, q.issues, None, implantados={"1": 4, "2": 1})
    assert ind(r2.mortalidade, "mortalidade").valor == 20.0
    r3 = run_analysis(q.records, q.issues, None, implantados={"1": 2})
    assert r3.mortalidade_tabela.set_index("parcela").loc["1", "status"] == "BLOQUEADO POR QUALIDADE"
    r4 = run_analysis(q.records, q.issues, None, mortalidade_ativa=False)
    assert ind(r4.mortalidade, "mortalidade").status == INDISPONIVEL


def test_replantio_sem_dados_explicita_limitacao():
    _, q = load("valido.csv")
    res = run_analysis(q.records, q.issues, None)
    assert res.replantio.empty and any("Nenhum registro" in n for n in res.replantio_notas)


def test_exportacao_xlsx_csv_e_manifesto():
    raw, q = load("problemas.csv")
    f = Filters(parcelas=["1"])
    res = run_analysis(q.records, q.issues, raw.meta, f)
    tabs = export.export_tables(raw.meta, q, res, False)
    xlsx = export.to_xlsx(tabs)
    assert xlsx[:2] == b"PK"
    from openpyxl import load_workbook
    import io
    wb = load_workbook(io.BytesIO(xlsx))
    assert "04_registros_excluidos" in wb.sheetnames
    exc = tabs["04_registros_excluidos"]
    assert (exc["motivo"] != "").all()  # todo excluído tem motivo
    csv = export.to_csv(tabs["05_indicadores_gerais"])
    assert csv.startswith(b"\xef\xbb\xbf")
    man = export.build_manifest(raw.meta, q, res, f, {"incluir_extremos": False})
    j = json.loads(export.manifest_json(man))
    for k in ("sha256", "versao_analisador", "filtros_aplicados", "indicadores_calculados",
              "indicadores_bloqueados", "decisoes_metodologicas", "tolerancias_numericas"):
        assert k in j or k in j["arquivos"][0]
    assert j["filtros_aplicados"] == {"parcelas": ["1"]}
    assert j["registros_invalidos"] == int((q.records["status_registro"] == "INVÁLIDO").sum())
    html = export.to_html_report(raw.meta, q, res, man)
    assert b"<html" in html


def test_indicador_bloqueado_nunca_tem_valor_zero():
    from analytics.results import Indicator
    i = Indicator("x", "x", 0, "m", "—", None, None, None, status="BLOQUEADO POR METODOLOGIA")
    assert i.valor is None
