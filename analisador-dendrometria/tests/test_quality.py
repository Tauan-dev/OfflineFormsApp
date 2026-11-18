from conftest import load

from analytics import observations as obs


def _by_line(q):
    return q.records.set_index("_linha")


def codes(q, line):
    return set(q.issues.loc[q.issues["linha"] == line, "código"])


def test_dap_textual_morta_preservado_e_pendente():
    _, q = load("problemas.csv")
    r = _by_line(q).loc[3]
    assert r["dap_cm_orig"] == "MORTA"
    assert r["dap_cm_status"] == "PENDENTE DE REVISÃO"
    assert "DAP_ESTADO_VITAL" in codes(q, 3)


def test_dap_negativo_e_extremo():
    _, q = load("problemas.csv")
    r = _by_line(q)
    assert r.loc[4, "dap_cm_status"] == "INVÁLIDO" and "DAP_NEGATIVO" in codes(q, 4)
    assert r.loc[5, "dap_cm_status"] == "EXTREMO" and r.loc[5, "dap_cm"] == 350.0  # preservado
    assert r.loc[5, "status_registro"] == "VÁLIDO COM RESSALVA"  # extremo não é erro automático


def test_parcela_arvore_especie_ausentes():
    _, q = load("problemas.csv")
    r = _by_line(q)
    assert "PARCELA_AUSENTE" in codes(q, 6) and r.loc[6, "status_registro"] == "INVÁLIDO"
    assert "ARVORE_AUSENTE" in codes(q, 7) and r.loc[7, "status_registro"] == "INVÁLIDO"
    assert "ESPECIE_AUSENTE" in codes(q, 8) and r.loc[8, "status_registro"] == "VÁLIDO COM RESSALVA"


def test_data_ausente_torna_medicao_inconclusiva():
    _, q = load("problemas.csv")
    r = _by_line(q).loc[9]
    assert r["status_registro"] == "INCONCLUSIVO" and r["medicao_id"] is None


def test_duplicidade_de_medicao_nao_descarta():
    _, q = load("problemas.csv")
    r = _by_line(q)
    assert r.loc[10, "status_registro"] == r.loc[11, "status_registro"] == "INCONCLUSIVO"
    assert {r.loc[10, "dap_cm"], r.loc[11, "dap_cm"]} == {20.0, 21.0}
    assert "DUPLICIDADE_MEDICAO" in codes(q, 10)


def test_multiplas_campanhas():
    from analytics.quality import campaign_summary
    _, q = load("problemas.csv")
    r = _by_line(q)
    assert r.loc[12, "n_datas_individuo"] == 2 and "DUPLICIDADE_INDIVIDUO" in codes(q, 12)
    assert campaign_summary(q.records)["possiveis_campanhas"] == 2


def test_dap_vazio_com_morte_ou_multifuste_nao_aplicavel():
    _, q = load("problemas.csv")
    r = _by_line(q)
    assert r.loc[17, "dap_cm_status"] == "NÃO APLICÁVEL" and r.loc[17, "mencao_morte"]
    assert r.loc[18, "dap_cm_status"] == "NÃO APLICÁVEL" and "DAP_NAO_MENSURAVEL" in codes(q, 18)


def test_zeros_a_esquerda_distintos():
    _, q = load("problemas.csv")
    ids = set(q.records["individuo_id"].dropna())
    assert "07 | 1" in ids and "7 | 1" in ids


def test_xlsx_datas_em_colunas_numericas_com_coordenada():
    _, q = load("valido.xlsx", "dendrometria")
    i = q.issues
    dap = i[i["código"] == "DAP_DATA"].iloc[0]
    assert dap["célula"] == "G4" and "12.5" in dap["descrição"]
    alt = i[i["código"] == "ALTURA_DATA"].iloc[0]
    assert alt["célula"] == "K5"
    r = q.records.set_index("_linha")
    assert r.loc[4, "dap_cm_status"] == "INVÁLIDO" and r.loc[4, "dap_cm_pista"] == "12.5"


def test_anotacao_de_parcela_nao_e_individuo():
    _, q = load("valido.xlsx", "dendrometria")
    r = q.records.set_index("_linha").loc[8]
    assert r["anotacao_parcela"] and r["status_registro"] == "INVÁLIDO"
    assert "ANOTACAO_PARCELA" in codes(q, 8)


def test_soma_das_categorias_igual_ao_total():
    _, q = load("problemas.csv")
    assert q.records["status_registro"].value_counts().sum() == len(q.records)


def test_observacoes_negacao():
    ms = obs.find_mentions("sem bromélias; não possui ninho")
    assert all(m.negada for m in ms if m.categoria in ("bromélias", "ninhos"))
    assert obs.positive_categories(obs.find_mentions("Ninho de beija-flor")) >= {"ninhos", "fauna"}
    assert obs.positive_categories(obs.find_mentions("nenhum animal observado")) == set()
    assert "morte" in obs.positive_categories(obs.find_mentions("MORTA"))


def test_observacao_preenchida_nao_e_fauna():
    assert "fauna" not in obs.positive_categories(obs.find_mentions("difícil acesso à árvore"))
