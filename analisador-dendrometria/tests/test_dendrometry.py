import math

import pandas as pd
import pytest
from conftest import close, ind, load

from analytics import Filters, run_analysis
from analytics import dendrometry as dd
from analytics.results import BLOQ_METODOLOGIA, INDISPONIVEL


def test_area_seccional_individual():
    assert abs(dd.area_seccional_m2(20) - 0.031416) <= 1e-6  # cenário da OpenSpec
    close(dd.area_seccional_m2(40), 0.12566370614359174, "area_basal_m2")  # exemplo do documento de fórmulas


def test_area_basal_total_secao_32(expected):
    _, q = load("area_basal.csv")
    res = run_analysis(q.records, q.issues, None)
    e = expected["area_basal"]
    close(ind(res.area_basal, "g_total").valor, e["G_total_m2"], "area_basal_m2")
    close(ind(res.area_basal, "g_media").valor, e["G_media_m2"], "area_basal_m2")
    close(ind(res.area_basal, "g_max").valor, e["g_max_m2"], "area_basal_m2")
    assert ind(res.area_basal, "g_total").quantidade_elegivel == 3


def test_estatisticas_descritivas(expected):
    _, q = load("valido.csv")
    res = run_analysis(q.records, q.issues, None)
    e = expected["valido_csv"]
    close(ind(res.dap, "dap_media").valor, e["dap_media_cm"], "dap_cm")
    close(ind(res.dap, "dap_mediana").valor, e["dap_mediana_cm"], "dap_cm")
    close(ind(res.dap, "dap_q1").valor, e["dap_q1_cm"], "dap_cm")
    close(ind(res.dap, "dap_q3").valor, e["dap_q3_cm"], "dap_cm")
    close(ind(res.dap, "dap_dp").valor, e["dap_dp_cm"], "dispersao")
    close(ind(res.dap, "dap_cv").valor, e["dap_cv_pct"], "dispersao")
    assert ind(res.dap, "dap_media").nome == "Média aritmética do DAP"
    close(ind(res.alturas["ht_m"], "ht_media").valor, e["ht_media_m"], "altura_m")
    assert ind(res.alturas["ht_m"], "ht_media").nome == "Altura total média (HT)"
    close(ind(res.volumes, "v_cil_total").valor, e["v_cil_total_m3"], "volume_m3")
    close(ind(res.volumes, "v_spurr_total").valor, e["v_spurr_total_m3"], "volume_m3")
    assert ind(res.volumes, "v_spurr_total").quantidade_elegivel == 2


def test_mediana_par_e_quartis_interpolados():
    assert dd.quantile([1, 2, 3, 4], 0.5) == 2.5
    assert dd.quantile([1, 2, 3, 4], 0.25) == 1.75


def test_desvio_padrao_estavel_grande_deslocamento():
    xs = [1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16]  # exemplo clássico de cancelamento catastrófico
    assert abs(dd.sample_std(xs) - math.sqrt(30)) < 1e-6


def test_cobertura_e_exclusoes_politica_unica():
    _, q = load("problemas.csv")
    res = run_analysis(q.records, q.issues, None)
    media = ind(res.dap, "dap_media")
    g = ind(res.area_basal, "g_total")
    assert media.quantidade_elegivel == g.quantidade_elegivel == res.distribuicao_info["n_elegivel"]
    assert media.quantidade_potencial == media.quantidade_elegivel + media.quantidade_excluida
    assert media.cobertura == pytest.approx(media.quantidade_elegivel / media.quantidade_potencial)
    assert any("300" in k for k in media.motivos_exclusao)
    assert media.status == "VÁLIDO COM RESSALVA"


def test_extremo_incluido_somente_por_opcao_explicita():
    _, q = load("problemas.csv")
    a = run_analysis(q.records, q.issues, None)
    b = run_analysis(q.records, q.issues, None, incluir_extremos=True)
    assert ind(b.dap, "dap_max").valor == 350.0
    assert ind(a.dap, "dap_max").valor < 350.0
    assert ind(b.dap, "dap_n").valor == ind(a.dap, "dap_n").valor + 1


def test_divisao_por_zero_e_sem_dados_indisponivel():
    _, q = load("valido.csv")
    vazio = q.records.iloc[0:0]
    res = run_analysis(vazio, q.issues, None)
    assert res.dap == [] and res.area_basal == []
    um = run_analysis(q.records.iloc[:1], q.issues, None)
    assert ind(um.dap, "dap_dp").status == INDISPONIVEL and ind(um.dap, "dap_dp").valor is None
    assert ind(um.dap, "dap_cv").status == INDISPONIVEL
    from analytics.results import cobertura
    assert cobertura(0, 0) is None


def test_sem_dap_elegivel_area_basal_indisponivel_nao_zero():
    _, q = load("problemas.csv")
    df = q.records[q.records["dap_cm_status"] != "MEDIDO"]
    res = run_analysis(df, q.issues, None)
    g = ind(res.area_basal, "g_total")
    assert g.status == INDISPONIVEL and g.valor is None


def test_bloqueados_metodologia():
    _, q = load("valido.csv")
    res = run_analysis(q.records, q.issues, None)
    assert ind(res.area_basal, "g_ha").status == BLOQ_METODOLOGIA and ind(res.area_basal, "g_ha").valor is None
    # dg é definição da literatura: sempre calculado, separado da média aritmética
    assert ind(res.area_basal, "dg").status == "VÁLIDO" and ind(res.area_basal, "dg").valor is not None


def test_distribuicao_classes_fechadas_esquerda_soma():
    _, q = load("valido.csv")
    tab, info = dd.diameter_distribution(q.records, 10)
    assert tab["frequência absoluta"].sum() == info["n_elegivel"] == 5
    # 10 → [10;20), 20 → [20;30): valor no limite vai para a classe que começa nele
    assert dict(zip(tab["classe"], tab["frequência absoluta"]))["[10 ; 20)"] == 1
    assert tab["frequência relativa (%)"].sum() == pytest.approx(100.0)
    with pytest.raises(ValueError):
        dd.diameter_distribution(q.records, 0)


def test_rankings_separados_e_empate_deterministico():
    _, q = load("valido.csv")
    r = dd.ranking(q.records, "dap", 3)
    assert r["valor"].tolist() == [50, 40, 30] and r["unidade"].iloc[0] == "cm"
    df = q.records.copy()
    df.loc[df.index[0], "dap_cm"] = 50.0
    r2 = dd.ranking(df, "dap", 2)
    assert r2["posição"].tolist() == [1, 1] and (r2["empate"] == "sim").all()
    assert r2["parcela"].tolist() == ["1", "2"]  # desempate por parcela/árvore, não por ordem de leitura
    assert dd.ranking(q.records, "ht", 1)["unidade"].iloc[0] == "m"
    assert dd.ranking(q.records, "g", 1)["unidade"].iloc[0] == "m²"


def test_altura_ausente_fora_do_denominador_e_altura_como_data():
    _, q = load("valido.xlsx", "dendrometria")
    res = run_analysis(q.records, q.issues, None)
    ht = ind(res.alturas["ht_m"], "ht_media")
    assert ht.quantidade_elegivel == 3  # 8, 12, 12; data em K5 e ausente fora
    assert any("data" in k for k in ht.motivos_exclusao)
    assert ind(res.alturas["ht_m"], "ht_m_ausentes").valor == 1


def test_filtros_por_parcela_e_especie():
    _, q = load("valido.csv")
    r = run_analysis(q.records, q.issues, None, Filters(parcelas=["2"]))
    assert r.filtrado and ind(r.dap, "dap_n").valor == 2 and ind(r.dap, "dap_media").filtrado
    r2 = run_analysis(q.records, q.issues, None, Filters(especies=["Cedro"]))
    assert ind(r2.dap, "dap_media").valor == 35.0
    r3 = run_analysis(q.records, q.issues, None, Filters(dap_min=25, dap_max=45))
    assert ind(r3.dap, "dap_n").valor == 2


def test_dap_virgula_decimal():
    _, q = load("bom_ponto_virgula.csv")
    res = run_analysis(q.records, q.issues, None)
    close(ind(res.dap, "dap_media").valor, (12.5 + 35.0) / 2, "dap_cm")


def test_copa_comprimento_e_proporcao(expected):
    _, q = load("copa.csv")
    res = run_analysis(q.records, q.issues, None)
    e = expected["copa"]
    c, p = ind(res.copa, "copa_comprimento_media"), ind(res.copa, "copa_proporcao_media")
    close(c.valor, e["comprimento_medio_m"], "altura_m")
    close(p.valor, e["proporcao_media_pct"], "altura_m")
    assert (c.quantidade_elegivel, c.quantidade_potencial) == (e["n_elegivel"], e["n_potencial"])
    assert sum(c.motivos_exclusao.values()) == 2  # HESGCOPA > HT e HESGCOPA ausente
    assert c.status == "VÁLIDO COM RESSALVA"


def test_copa_sem_colunas_nao_vira_zero():
    _, q = load("copa.csv")
    df = q.records.copy()
    df["hesgcopa_m_status"] = "NÃO COLETADO"
    r = dd.crown_indicators(df)
    assert r[0].valor is None and r[0].status == INDISPONIVEL
