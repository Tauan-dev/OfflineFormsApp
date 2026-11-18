"""Gera o relatório de validação matemática (relatorios/validacao_matematica.md).

Para cada indicador: fórmula, variáveis, unidade, fixture, exemplo manual,
esperado, produzido, erro absoluto, erro relativo, tolerância e conclusão.
Critério (Burden & Faires): |produzido − esperado| ≤ atol + rtol·|esperado|.

Uso:  python validar_indicadores.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from analytics import canonicalization as canon
from analytics import dendrometry as dd
from analytics import Filters, Metodologia, ingestion, quality, run_analysis
from analytics.results import ANALISADOR_VERSAO, TOLERANCIAS, VERSAO_METODOLOGICA

ROOT = Path(__file__).parent
SYN = ROOT / "fixtures" / "synthetic"
EXP = json.loads((ROOT / "fixtures" / "expected" / "esperados.json").read_text(encoding="utf-8"))


def load(name):
    raw = ingestion.read_file((SYN / name).read_bytes(), name)
    q = quality.build_records(raw, canon.auto_map(raw.headers))
    return raw, q


def ind(lst, id_):
    return next(i for i in lst if i.id == id_)


def main() -> int:
    raw_ab, q_ab = load("area_basal.csv")
    r_ab = run_analysis(q_ab.records, q_ab.issues, raw_ab.meta)
    raw_v, q_v = load("valido.csv")
    r_v = run_analysis(q_v.records, q_v.issues, raw_v.meta)
    raw_e, q_e = load("estado_vital.csv")
    r_e = run_analysis(q_e.records, q_e.issues, raw_e.meta, implantados=36)
    raw_h, q_h = load("ab_hectare.csv")
    met = Metodologia(area_parcela=1000, unidade_area="m²", desenho_amostral="validação (fixture)")
    from analytics.results import metodologia_arboreto_esarm
    r_h3 = run_analysis(q_h.records, q_h.issues, raw_h.meta, metodologia=metodologia_arboreto_esarm())
    raw_m, q_m = load("multifuste.csv")
    r_m = run_analysis(q_m.records, q_m.issues, raw_m.meta)
    emf = EXP["multifuste"]
    raw_c, q_c = load("copa.csv")
    r_c = run_analysis(q_c.records, q_c.issues, raw_c.meta)
    ecp = EXP["copa"]
    r_h1 = run_analysis(q_h.records, q_h.issues, raw_h.meta, Filters(parcelas=["1"]), metodologia=met)
    r_h2 = run_analysis(q_h.records, q_h.issues, raw_h.meta, metodologia=met)
    eh = EXP["ab_hectare"]
    ev = EXP["valido_csv"]
    eab = EXP["area_basal"]
    eev = EXP["estado_vital"]

    casos = [
        ("Área seccional individual (g)", "g = π·DAP²/40000", "DAP (cm)", "m²", "—", "DAP = 20 cm → π·400/40000",
         math.pi * 400 / 40000, dd.area_seccional_m2(20), "area_basal_m2"),
        ("Área basal total (G)", "G = Σ π·DAPᵢ²/40000", "DAPᵢ (cm)", "m²", "area_basal.csv", "DAP 10, 20, 30 cm (seção 32)",
         eab["G_total_m2"], ind(r_ab.area_basal, "g_total").valor, "area_basal_m2"),
        ("Área basal média por indivíduo", "Ḡ = G / n", "G, n", "m²", "area_basal.csv", "0,109955742876 / 3",
         eab["G_media_m2"], ind(r_ab.area_basal, "g_media").valor, "area_basal_m2"),
        ("Maior área basal individual", "max(gᵢ)", "gᵢ", "m²", "area_basal.csv", "g(30) = π·900/40000",
         eab["g_max_m2"], ind(r_ab.area_basal, "g_max").valor, "area_basal_m2"),
        ("Média aritmética do DAP", "Σxᵢ/n", "DAP", "cm", "valido.csv", "150/5", ev["dap_media_cm"],
         ind(r_v.dap, "dap_media").valor, "dap_cm"),
        ("Mediana do DAP", "valor central", "DAP", "cm", "valido.csv", "10,20,[30],40,50", ev["dap_mediana_cm"],
         ind(r_v.dap, "dap_mediana").valor, "dap_cm"),
        ("1º quartil do DAP", "tipo 7: x₍₁₊₀,₂₅·(n−1)₎", "DAP", "cm", "valido.csv", "posição 1 → 20", ev["dap_q1_cm"],
         ind(r_v.dap, "dap_q1").valor, "dap_cm"),
        ("3º quartil do DAP", "tipo 7: x₍₁₊₀,₇₅·(n−1)₎", "DAP", "cm", "valido.csv", "posição 3 → 40", ev["dap_q3_cm"],
         ind(r_v.dap, "dap_q3").valor, "dap_cm"),
        ("Mínimo do DAP", "min", "DAP", "cm", "valido.csv", "10", 10.0, ind(r_v.dap, "dap_min").valor, "dap_cm"),
        ("Máximo do DAP", "max", "DAP", "cm", "valido.csv", "50", 50.0, ind(r_v.dap, "dap_max").valor, "dap_cm"),
        ("Desvio-padrão amostral do DAP", "√[Σ(xᵢ−x̄)²/(n−1)]", "DAP", "cm", "valido.csv", "√(1000/4) = √250",
         ev["dap_dp_cm"], ind(r_v.dap, "dap_dp").valor, "dispersao"),
        ("Coeficiente de variação do DAP", "s/x̄·100", "s, x̄", "%", "valido.csv", "15,8113883/30·100",
         ev["dap_cv_pct"], ind(r_v.dap, "dap_cv").valor, "dispersao"),
        ("Contagem de DAPs elegíveis", "n", "—", "valores", "valido.csv", "5", 5, ind(r_v.dap, "dap_n").valor, "contagem"),
        ("Altura total média (HT)", "Σ HTᵢ/n", "HT", "m", "valido.csv", "(8+12+15+18+20)/5", ev["ht_media_m"],
         ind(r_v.alturas["ht_m"], "ht_media").valor, "altura_m"),
        ("Volume cilíndrico total", "Σ gᵢ·HTᵢ", "DAP, HT", "m³", "valido.csv", "Σ π·DAP²/40000·HT", ev["v_cil_total_m3"],
         ind(r_v.volumes, "v_cil_total").valor, "volume_m3"),
        ("Volume comercial (Spurr)", "Σ [b₀ + b₁·DAP²·HC]", "DAP, HC", "m³", "valido.csv",
         "2 árvores com HC: (20 cm, 6 m) e (40 cm, 8 m)", ev["v_spurr_total_m3"],
         ind(r_v.volumes, "v_spurr_total").valor, "volume_m3"),
        ("Indivíduos únicos", "nº pares (Parcela, Árvore)", "—", "indivíduos", "valido.csv", "5", ev["individuos"],
         ind(r_v.gerais, "individuos").valor, "contagem"),
        ("Riqueza observada", "nº espécies distintas", "—", "táxons", "valido.csv", "Ipê, Cedro, Jatobá", ev["especies"],
         ind(r_v.gerais, "especies").valor, "contagem"),
        ("Cobertura de DAP", "elegíveis/potenciais·100", "—", "%", "valido.csv", "5/5·100", 100.0,
         ind(r_v.gerais, "cobertura_dap").valor, "percentual"),
        ("Área basal por hectare (decisão do usuário)", "ABₕₐ = G / A", "G (m²), A (ha)", "m²/ha", "ab_hectare.csv",
         "0,424115 / 0,10 (exemplo do documento de fórmulas)", eh["G_ha_parcela_1"], ind(r_h1.area_basal, "g_ha").valor,
         "area_basal_m2"),
        ("Área basal por hectare — parcela sem árvores na área", "ABₕₐ = G / Σaⱼ", "G, aⱼ", "m²/ha", "ab_hectare.csv",
         "0,424115 / (0,10 + 0,10)", eh["G_ha_duas_parcelas"], ind(r_h2.area_basal, "g_ha").valor, "area_basal_m2"),
        ("Área basal por hectare — predefinição ESARM (144 m²)", "ABₕₐ = G / Σaⱼ", "G, aⱼ = 0,0144 ha", "m²/ha",
         "ab_hectare.csv", "0,424115 / (2 × 0,0144)", eh["G_total_m2"] / 0.0288, ind(r_h3.area_basal, "g_ha").valor,
         "area_basal_m2"),
        ("Diâmetro quadrático médio (literatura)", "dg = √(Σ DAP² / n)", "DAPᵢ (cm)", "cm", "ab_hectare.csv",
         "√(5400 / 4) = √1350", eh["dg_cm"], ind(r_h2.area_basal, "dg").valor, "dap_cm"),
        ("Área basal com multifustes (Finger, 1992)", "gᵢ = Σⱼ π·dᵢⱼ²/40000", "dᵢⱼ (cm)", "m²", "multifuste.csv",
         "g(20) + π·169/40000 + g(44,4) + π·129,28/40000", emf["G_multifuste_m2"],
         ind(r_m.area_basal, "g_total_multifuste").valor, "area_basal_m2"),
        ("Comprimento médio de copa", "HT − HESGCOPA", "HT, HESGCOPA (m)", "m", "copa.csv",
         "(10−4)=6; (20−5)=15; média 10,5", ecp["comprimento_medio_m"],
         ind(r_c.copa, "copa_comprimento_media").valor, "altura_m"),
        ("Proporção média de copa", "(HT − HESGCOPA)/HT × 100", "HT, HESGCOPA (m)", "%", "copa.csv",
         "60 %; 75 %; média 67,5 %", ecp["proporcao_media_pct"],
         ind(r_c.copa, "copa_proporcao_media").valor, "altura_m"),
        ("DAP equivalente (Stewart & Salazar, 1992)", "d_eq = √(Σ dⱼ²)", "dⱼ (cm)", "cm", "—", "√(3² + 4² + 12²) = 13",
         13.0, dd.dap_equivalente_cm([3, 4, 12]), "dap_cm"),
        ("Índice de Shannon (H')", "−Σ pᵢ ln pᵢ", "nᵢ", "nats/ind.", "valido.csv", "p = 0,4; 0,4; 0,2",
         ev["shannon"], ind(r_v.diversidade, "shannon").valor, "indice"),
        ("Equabilidade de Pielou (J')", "H' / ln S", "H', S", "—", "valido.csv", "1,054920 / ln 3",
         ev["pielou"], ind(r_v.diversidade, "pielou").valor, "indice"),
        ("Índice de Simpson (1 − D)", "1 − Σ nᵢ(nᵢ−1)/[N(N−1)]", "nᵢ, N", "—", "valido.csv", "1 − 4/20",
         ev["simpson_1_menos_D"], ind(r_v.diversidade, "simpson").valor, "indice"),
        ("Dominância relativa (Cedro)", "Gᵢ / G × 100", "DAP (cm)", "%", "valido.csv", "(900+1600)/5500 × 100",
         ev["DoR_cedro_pct"], r_v.especies.set_index("espécie").loc["Cedro", "Dominância relativa DoR (%)"],
         "percentual"),
        ("Mortalidade (estado vital estruturado)", "mortos/implantados·100", "—", "%", "estado_vital.csv",
         "1/(36+36)·100", eev["mortalidade_total_pct"], ind(r_e.mortalidade, "mortalidade").valor, "percentual"),
        ("Sobrevivência (estado vital estruturado)", "vivos/implantados·100", "—", "%", "estado_vital.csv",
         "3/72·100", eev["sobrevivencia_pct"], ind(r_e.mortalidade, "sobrevivencia").valor, "percentual"),
    ]
    linhas = ["# Validação matemática dos indicadores", "",
              f"Analisador {ANALISADOR_VERSAO} · metodologia {VERSAO_METODOLOGICA}. Gerado por `validar_indicadores.py`.",
              "", "Critério: |produzido − esperado| ≤ atol + rtol·|esperado| (Burden & Faires). "
              "Erro relativo = erro absoluto / |esperado|.", "",
              "| Indicador | Fórmula | Variáveis | Unidade | Fixture | Exemplo manual | Esperado | Produzido | "
              "Erro absoluto | Erro relativo | Tolerância | Conclusão |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    falhas = 0
    for nome, formula, var, un, fx, ex, esp, prod, tk in casos:
        t = TOLERANCIAS[tk]
        ea = abs(prod - esp)
        er = ea / abs(esp) if esp else float("nan")
        ok = t.aceita(prod, esp)
        falhas += not ok
        linhas.append(f"| {nome} | {formula} | {var} | {un} | {fx} | {ex} | {esp:.15g} | {prod:.15g} | {ea:.3e} | "
                      f"{er:.3e} | atol={t.atol:g}; rtol={t.rtol:g} | {'APROVADO' if ok else 'REPROVADO'} |")
    linhas += ["", f"**{len(casos) - falhas} de {len(casos)} indicadores aprovados.**", "",
               "## Indicadores não validados (bloqueados ou pendentes)", "",
               "- Área basal por hectare na planilha real: calculada com a predefinição da literatura (arboreto ESARM, "
               "144 m²; parcelas PX1–PX5 fora do desenho publicado ficam excluídas) — VÁLIDO COM RESSALVA.",
               "- Escolha do 'diâmetro médio oficial' (média aritmética × dg) — decisão M5 da equipe.",
               "- Multifustes sem padrão estrutural — revisão humana.",
               "- Mortalidade/sobrevivência na planilha real — BLOQUEADO POR QUALIDADE OU METODOLOGIA (sem estado vital estruturado).",
               "- Indicador de saúde, dano leve/severo, serrapilheira, classificação do povoamento, papel de "
               "Nota (*) da definição de HESGCOPA — não fornecida.", "",
               "## Tolerâncias", ""]
    linhas += [f"- **{k}**: atol={v.atol:g}, rtol={v.rtol:g} — {v.justificativa}" for k, v in TOLERANCIAS.items()]
    out = ROOT / "relatorios" / "validacao_matematica.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"{len(casos) - falhas}/{len(casos)} aprovados → {out}")
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
