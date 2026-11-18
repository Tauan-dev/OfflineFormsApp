"""Indicadores liberados pela literatura e decisões por execução.

- Área basal por hectare: só com área + desenho amostral (do usuário ou da predefinição da literatura
  para o arboreto ESARM); parcelas sem área ficam fora de G e de A.
- dg: definição da literatura, sempre calculado e separado da média aritmética.
- Multifuste: regra de Finger (1992) com extração estrita dos fustes.
- Diversidade e fitossociologia: Brower & Zar (1984); Mueller-Dombois & Ellenberg (1974).
"""
import json
import math

import pandas as pd
from conftest import close, ind, load

from analytics import Filters, Metodologia, run_analysis
from analytics import dendrometry as dd
from analytics import export
from analytics.observations import extract_stems
from analytics.results import (BLOQ_METODOLOGIA, ESARM_AREA_M2, VALIDO, VALIDO_RESSALVA, esarm_aplicavel,
                               metodologia_arboreto_esarm)

DESENHO = "parcelas permanentes de área fixa (teste)"


def _run(met=None, filters=None, fixture="ab_hectare.csv"):
    raw, q = load(fixture)
    return raw, q, run_analysis(q.records, q.issues, raw.meta, filters, metodologia=met)


# ------------------------------------------------------------ área basal por hectare
def test_padrao_bloqueado_sem_valor():
    _, _, res = _run()
    i = ind(res.area_basal, "g_ha")
    assert i.status == BLOQ_METODOLOGIA and i.valor is None  # nunca zero
    assert "área da parcela (ha)" not in res.parcelas.columns


def test_area_sem_desenho_amostral_continua_bloqueado():
    _, _, res = _run(Metodologia(area_parcela=1000, unidade_area="m²"))
    i = ind(res.area_basal, "g_ha")
    assert i.status == BLOQ_METODOLOGIA and i.valor is None
    assert "desenho amostral" in i.observacoes[0]


def test_area_invalida_bloqueia():
    for a in (0, -5, float("nan"), float("inf")):
        _, _, res = _run(Metodologia(area_parcela=a, desenho_amostral=DESENHO))
        assert ind(res.area_basal, "g_ha").valor is None, a


def test_ab_hectare_exemplo_do_documento(expected):
    """Exemplo do documento de fórmulas: Sc = 0,42412 m² em 0,10 ha → 4,2412 m²/ha."""
    e = expected["ab_hectare"]
    _, _, res = _run(Metodologia(area_parcela=1000, unidade_area="m²", desenho_amostral=DESENHO),
                     Filters(parcelas=["1"]))
    i = ind(res.area_basal, "g_ha")
    assert i.status == VALIDO_RESSALVA and i.unidade == "m²/ha"
    close(i.valor, e["G_ha_parcela_1"], "area_basal_m2")
    assert abs(i.valor - 4.2412) < 5e-5  # valor arredondado do documento
    close(ind(res.area_basal, "area_amostrada").valor, 0.10, "area_basal_m2")


def test_parcela_sem_arvores_entra_na_area(expected):
    e = expected["ab_hectare"]
    _, _, res = _run(Metodologia(area_parcela=0.10, unidade_area="ha", desenho_amostral=DESENHO))
    close(ind(res.area_basal, "area_amostrada").valor, 0.20, "area_basal_m2")
    close(ind(res.area_basal, "g_ha").valor, e["G_ha_duas_parcelas"], "area_basal_m2")
    assert "2 parcelas" in ind(res.area_basal, "g_ha").denominador


def test_unidades_equivalentes():
    _, _, a = _run(Metodologia(area_parcela=1000, unidade_area="m²", desenho_amostral=DESENHO))
    _, _, b = _run(Metodologia(area_parcela=0.1, unidade_area="ha", desenho_amostral=DESENHO))
    close(ind(a.area_basal, "g_ha").valor, ind(b.area_basal, "g_ha").valor, "area_basal_m2")


def test_parcela_sem_area_sai_de_G_e_de_A(expected):
    """Parcela 2 sem área: excluída do numerador e do denominador; o motivo é exibido."""
    e = expected["ab_hectare"]
    _, _, res = _run(Metodologia(area_parcela={"1": 1000}, unidade_area="m²", desenho_amostral=DESENHO))
    i = ind(res.area_basal, "g_ha")
    close(i.valor, e["G_ha_parcela_1"], "area_basal_m2")
    assert any("sem área conhecida" in o for o in i.observacoes)


def test_nenhuma_parcela_com_area_bloqueia():
    _, _, res = _run(Metodologia(area_parcela={"99": 1000}, unidade_area="m²", desenho_amostral=DESENHO))
    assert ind(res.area_basal, "g_ha").valor is None


def test_g_ha_por_parcela_na_tabela(expected):
    e = expected["ab_hectare"]
    _, _, res = _run(Metodologia(area_parcela={"1": 1000, "2": 500}, unidade_area="m²", desenho_amostral=DESENHO))
    P = res.parcelas.set_index("parcela")
    close(P.loc["1", "área basal G (m²/ha)"], e["G_ha_parcela_1"], "area_basal_m2")
    close(P.loc["2", "área da parcela (ha)"], 0.05, "area_basal_m2")
    assert pd.isna(P.loc["2", "área basal G (m²/ha)"])  # sem DAP elegível: vazio, nunca zero inventado
    close(ind(res.area_basal, "g_ha").valor, e["G_total_m2"] / 0.15, "area_basal_m2")


def test_predefinicao_esarm():
    assert ESARM_AREA_M2 == 144.0  # 36 plantas × (2 m × 2 m)
    met = metodologia_arboreto_esarm()
    close(met.area_ha("1"), 0.0144, "area_basal_m2")
    close(met.area_ha("98"), 0.0144, "area_basal_m2")
    assert met.area_ha("99") is None and met.area_ha("PX1") is None  # fora do desenho publicado
    assert met.fonte.startswith("literatura") and met.por_hectare_informado
    assert esarm_aplicavel(["1", "2", "98", "PX3"])
    assert not esarm_aplicavel(["1", "120"]) and not esarm_aplicavel(["07"]) and not esarm_aplicavel(["PX1"])


def test_predefinicao_esarm_calculo(expected):
    e = expected["ab_hectare"]
    _, _, res = _run(metodologia_arboreto_esarm())
    i = ind(res.area_basal, "g_ha")
    close(i.valor, e["G_total_m2"] / 0.0288, "area_basal_m2")  # parcelas 1 e 2 × 144 m²
    assert i.versao_metodologica == "literatura"
    # Sensibilidade à convenção de área exposta, não escondida: 100 m² e 196 m²
    sens = next(o for o in i.observacoes if o.startswith("Sensibilidade"))
    v100 = e["G_total_m2"] / 0.02
    assert f"{v100:.2f}".replace(".", ",") in sens and "196 m²" in sens


# ------------------------------------------------------------ dg
def test_dg_literatura(expected):
    e = expected["ab_hectare"]
    _, _, res = _run()
    dg = ind(res.area_basal, "dg")
    assert dg.status == VALIDO and dg.unidade == "cm" and dg.nome == "Diâmetro quadrático médio (dg)"
    close(dg.valor, e["dg_cm"], "dap_cm")
    gm = ind(res.area_basal, "g_media").valor
    close(dg.valor, math.sqrt(40000 * gm / math.pi), "dap_cm")  # identidade dg = √(40000·Ḡ/π)
    assert dg.valor > ind(res.dap, "dap_media").valor  # dg ≥ média aritmética (igual só sem variância)
    assert ind(res.dap, "dap_media").nome == "Média aritmética do DAP"


# ------------------------------------------------------------ multifuste
def test_extracao_estrita_de_fustes():
    assert extract_stems("3 fustes: 12.1, 14.5, 13.0").diametros_cm == [12.1, 14.5, 13.0]
    assert extract_stems("DAP 2 fustes - 4.9 e 3.5. 1 das bifurcações dá 2m").diametros_cm == [4.9, 3.5]
    assert extract_stems("4 Fustes 10.5, 8.4, 7.5 ,12.0.").diametros_cm == [10.5, 8.4, 7.5, 12.0]
    assert extract_stems("3 bifurcações: 7, 5.5 e 4 cm de DAP. Bifurcações a 0.89 cm").diametros_cm == [7, 5.5, 4]
    # não extraíveis → revisão humana
    assert extract_stems("Dois fustes com Hc 11 e 8 metros").diametros_cm is None  # alturas, por extenso
    assert extract_stems("2 fustes: 30.2, 17.6 e 3.5").diametros_cm is None  # contagem divergente
    assert extract_stems("4.0, 3.9. brotações com ramos").diametros_cm is None  # sem quantidade declarada
    assert extract_stems("bifurcação 2 fustes grandes").diametros_cm is None


def test_dap_equivalente_e_area_basal_multifuste():
    close(dd.dap_equivalente_cm([3.0, 4.0]), 5.0, "dap_cm")  # √(9 + 16)
    g = dd.area_seccional_m2(3) + dd.area_seccional_m2(4)
    close(g, dd.area_seccional_m2(5), "area_basal_m2")  # Σg dos fustes = g do DAP equivalente


def test_multifuste_no_indicador(expected):
    raw, q, res = _run(fixture="multifuste.csv")
    e = expected["multifuste"]
    t = res.multifustes.set_index("árvore")
    assert t.loc["2", "situação"] == "FUSTES EXTRAÍDOS"
    assert t.loc["3", "situação"] == "REVISÃO HUMANA"  # contagem divergente
    assert t.loc["4", "situação"] == "REVISÃO HUMANA"  # DAP da coluna ≠ fustes
    i = ind(res.area_basal, "g_total_multifuste")
    assert i.status == VALIDO_RESSALVA
    close(i.valor, e["G_multifuste_m2"], "area_basal_m2")
    close(ind(res.area_basal, "g_total").valor, e["G_coluna_m2"], "area_basal_m2")  # G original inalterado


# ------------------------------------------------------------ diversidade e fitossociologia
def test_diversidade(expected):
    e = expected["valido_csv"]
    _, q = load("valido.csv")
    res = run_analysis(q.records, q.issues, None)
    close(ind(res.diversidade, "shannon").valor, e["shannon"], "indice")
    close(ind(res.diversidade, "pielou").valor, e["pielou"], "indice")
    close(ind(res.diversidade, "simpson").valor, e["simpson_1_menos_D"], "indice")
    assert all(i.status == VALIDO_RESSALVA for i in res.diversidade)


def test_diversidade_casos_limite():
    _, q = load("area_basal.csv")  # A: 2 indivíduos, B: 1
    res = run_analysis(q.records, q.issues, None)
    close(ind(res.diversidade, "shannon").valor, -(2 / 3 * math.log(2 / 3) + 1 / 3 * math.log(1 / 3)), "indice")
    close(ind(res.diversidade, "simpson").valor, 1 - (2 * 1) / (3 * 2), "indice")
    one = q.records[q.records["especie"] == "A"]
    r1 = run_analysis(one, q.issues, None)
    assert ind(r1.diversidade, "pielou").valor is None  # S = 1: ln 1 = 0 → indisponível, nunca zero
    close(ind(r1.diversidade, "shannon").valor, 0.0, "indice")


def test_fitossociologia(expected):
    e = expected["valido_csv"]
    _, q = load("valido.csv")
    res = run_analysis(q.records, q.issues, None)
    sp = res.especies.set_index("espécie")
    for k in ("Densidade relativa DR (%)", "Dominância relativa DoR (%)", "Frequência relativa FR (%)"):
        close(sp[k].sum(), 100.0, "percentual")
    close(sp["Valor de importância VI (0–300)"].sum(), 300.0, "percentual")
    close(sp.loc["Cedro", "Dominância relativa DoR (%)"], e["DoR_cedro_pct"], "percentual")


# ------------------------------------------------------------ manifesto
def test_manifesto_registra_decisoes():
    raw, q, res = _run(metodologia_arboreto_esarm())
    man = json.loads(export.manifest_json(export.build_manifest(raw.meta, q, res, Filters(), {})))
    assert man["decisoes_do_usuario"]["fonte"].startswith("literatura")
    assert any("Área basal por hectare (fonte: literatura" in d for d in man["decisoes_metodologicas"])
    ids = {i["id"] for i in man["indicadores_calculados"]}
    assert {"g_ha", "dg", "area_amostrada", "shannon", "g_total_multifuste"} <= ids


def test_manifesto_sem_decisoes_lista_bloqueados():
    raw, q, res = _run()
    man = export.build_manifest(raw.meta, q, res, Filters(), {})
    bl = {i["id"] for i in man["indicadores_bloqueados"]}
    assert "g_ha" in bl and "dg" not in bl
