"""Regressões dos defeitos já identificados (AUDITORIA-CALCULOS.md e matriz R1–R32
da OpenSpec) e dos problemas encontrados na planilha real."""
import pytest
from conftest import REAL_FILE, ind, load

from analytics import canonicalization as canon
from analytics import ingestion, quality, run_analysis


def _csv(text: str, name="t.csv"):
    raw = ingestion.read_csv(text.encode("utf-8"), name)
    return raw, quality.build_records(raw, canon.auto_map(raw.headers))


H = "Parcela,Árvore,Nome Comum,Data Medição,DAP (cm),HT (m),Observação\n"


def test_r6_auditoria_4_4_dap_zero_nao_aparece_no_minimo():
    """Antes: minDap = 0 enquanto a mesma árvore era excluída da área basal."""
    _, q = _csv(H + "1,1,A,28/07/2026,0,5,\n1,2,A,28/07/2026,10,6,\n")
    res = run_analysis(q.records, q.issues, None)
    assert ind(res.dap, "dap_min").valor == 10.0
    assert ind(res.dap, "dap_n").valor == ind(res.area_basal, "g_total").quantidade_elegivel == 1
    assert any("zero" in k for k in ind(res.dap, "dap_min").motivos_exclusao)


def test_r12_auditoria_4_7_chave_com_espaco_externo():
    _, q = _csv(H + " 1 ,7,A,28/07/2026,10,5,\n1,7,A,29/07/2026,11,5,\n")
    assert q.records["individuo_id"].nunique() == 1


def test_r10_registro_nao_e_individuo():
    raw, q = _csv(H + "1,7,A,28/07/2026,10,5,\n1,7,A,28/01/2027,11,5,\n")
    res = run_analysis(q.records, q.issues, raw.meta)
    assert ind(res.gerais, "individuos").valor == 1
    assert ind(res.gerais, "medicoes").valor == 2


def test_r19_registro_sem_parcela_nao_vira_parcela():
    raw, q = _csv(H + ",7,A,28/07/2026,10,5,\n1,1,A,28/07/2026,10,5,\n")
    res = run_analysis(q.records, q.issues, raw.meta)
    assert ind(res.gerais, "parcelas").valor == 1
    assert "Sem parcela" not in set(res.parcelas["parcela"])


def test_r13_observacao_preenchida_nao_e_fauna():
    _, q = _csv(H + "1,1,A,28/07/2026,10,5,acesso difícil\n1,2,A,28/07/2026,10,5,ninho de beija-flor\n")
    res = run_analysis(q.records, q.issues, None)
    fauna = res.mencoes[res.mencoes["categoria"] == "fauna"]
    assert set(fauna["linha"]) == {3} and (fauna["status"] == "revisão necessária").all()


def test_r14_csv_multilinha_nao_gera_linha_espuria():
    raw, q = _csv(H + '1,1,A,28/07/2026,10,5,"linha 1\nlinha 2"\n1,2,A,28/07/2026,10,5,\n')
    assert raw.meta.registros_interpretados == 2
    assert (q.records["status_registro"] != "INVÁLIDO").all()


def test_r15_mapeamento_por_cabecalho_nao_por_posicao():
    _, q = _csv("Árvore,Parcela,Data Medição,Nome Comum,DAP (cm)\n7,1,28/07/2026,A,10\n")
    r = q.records.iloc[0]
    assert r["parcela"] == "1" and r["arvore"] == "7"


def test_r16_falha_de_leitura_nao_vira_conjunto_vazio():
    with pytest.raises(Exception):
        ingestion.read_xlsx(b"isto nao e xlsx", "x.xlsx")


def test_contrato_morta_vazio_e_texto_sao_estados_distintos():
    """Antes: toNum('') e toNum('MORTA') eram ambos null."""
    _, q = _csv(H + "1,1,A,28/07/2026,,5,\n1,2,A,28/07/2026,MORTA,5,\n1,3,A,28/07/2026,abc,5,\n")
    st = q.records["dap_cm_status"].tolist()
    assert st == ["AUSENTE", "PENDENTE DE REVISÃO", "INVÁLIDO"]


def test_r11_especies_ordenadas_pela_grandeza_exibida():
    _, q = _csv(H + "1,1,A,28/07/2026,10,5,\n1,2,B,28/07/2026,10,5,\n2,1,B,28/07/2026,10,5,\n")
    sp = run_analysis(q.records, q.issues, None).especies
    assert sp["espécie"].tolist() == ["B", "A"]
    assert sp["Abundância por indivíduos únicos"].tolist() == [2, 1]


def test_auditoria_4_2_contagem_bruta_nao_reconstruida():
    rows = "".join(f"1,{i},{'A' if i == 1 else 'B'},28/07/2026,10,5,\n" for i in range(1, 201))
    _, q = _csv(H + rows)
    sp = run_analysis(q.records, q.issues, None).especies.set_index("espécie")
    assert sp.loc["A", "Abundância por indivíduos únicos"] == 1  # nunca round(pct·total/100) = 2


def test_altura_serial_de_data_e_extrema_fora_do_calculo():
    _, q = _csv(H + "1,1,A,28/07/2026,10,46151,\n1,2,A,28/07/2026,10,12,\n")
    r = q.records.iloc[0]
    assert r["ht_m"] == 46151 and r["ht_m_status"] == "EXTREMO"
    assert {"POSSIVEL_SERIAL_DATA", "ALTURA_EXTREMA"} <= set(q.issues["código"])
    res = run_analysis(q.records, q.issues, None)
    assert ind(res.alturas["ht_m"], "ht_max").valor == 12.0


# ------------------------------------------------------------ planilha real
real = pytest.mark.skipif(not REAL_FILE.exists(), reason="planilha real não disponível")


@pytest.fixture(scope="module")
def real_q():
    data = REAL_FILE.read_bytes()
    raw = ingestion.read_file(data, REAL_FILE.name, "dendrometria")
    return raw, quality.build_records(raw, canon.auto_map(raw.headers))


@real
def test_real_planilhas_e_colunas(real_q):
    raw, q = real_q
    assert raw.meta.planilhas_disponiveis == ["dendrometria", "MAPA"]
    assert q.mapping.is_safe and not q.mapping.missing_required


@real
def test_real_datas_em_colunas_numericas(real_q):
    _, q = real_q
    c = q.issues["código"].value_counts()
    assert c["DAP_DATA"] == 140
    assert c["ALTURA_DATA"] == 64  # HESG 16 + HESGCOPA 39 + HT 9


@real
def test_real_anotacoes_de_parcela_e_serial(real_q):
    _, q = real_q
    assert int(q.records["anotacao_parcela"].sum()) == 14
    r = q.records.set_index("_linha").loc[299]
    assert r["ht_m_status"] == "EXTREMO"


@real
def test_real_soma_status(real_q):
    _, q = real_q
    assert len(q.records) == 1131
    assert q.records["status_registro"].value_counts().sum() == 1131
