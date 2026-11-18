"""Gera as fixtures sintéticas e os resultados esperados (cálculo manual).

Uso:  python fixtures/gerar_fixtures.py
Os arquivos gerados são versionados; rodar de novo produz bytes idênticos
(exceto XLSX, cujo conteúdo de células é idêntico).
"""
from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path

from openpyxl import Workbook

HERE = Path(__file__).parent
SYN = HERE / "synthetic"
EXP = HERE / "expected"
HEADER = ["Parcela", "Árvore", "Plantio", "Replantio", "Nome Comum", "Data Medição", "DAP (cm)", "HESG (m)",
          "HESGCOPA (m)", "HC (m)", "HT (m)", "Observação"]


def w(name: str, text: str, bom: bool = False) -> None:
    data = text.encode("utf-8")
    (SYN / name).write_bytes((b"\xef\xbb\xbf" if bom else b"") + data)


def main() -> None:
    SYN.mkdir(parents=True, exist_ok=True)
    EXP.mkdir(parents=True, exist_ok=True)
    h = ",".join(HEADER)

    # 1. CSV válido, separador vírgula, LF
    w("valido.csv", h + "\n" + "\n".join([
        "1,1,,,Ipê,28/07/2026,10,2,4,,8,",
        "1,2,,,Ipê,28/07/2026,20,3,5,6,12,",
        "1,3,,,Cedro,28/07/2026,30,3,6,,15,",
        "2,1,,,Cedro,29/07/2026,40,4,7,8,18,",
        "2,2,,,Jatobá,29/07/2026,50,5,8,,20,",
    ]) + "\n")

    # 2. CSV com BOM, ponto e vírgula e vírgula decimal, CRLF
    w("bom_ponto_virgula.csv", ";".join(HEADER) + "\r\n" + "\r\n".join([
        "1;1;;;Ipê;28/07/2026;12,5;2,0;4,5;;8,5;",
        "1;2;;;Ipê;28/07/2026; 35,0 ;3;5;;12;",
    ]) + "\r\n", bom=True)

    # 3. Observação com vírgula, multilinha, aspas escapadas; última linha sem quebra; campo final vazio
    w("multilinha_virgula.csv", h + "\r\n"
      + '1,1,,,Ipê,28/07/2026,10,2,4,,8,"Brotação na base, com dano"\r\n'
      + '1,2,,,Ipê,28/07/2026,20,3,5,,12,"linha 1\r\nlinha 2 com ""aspas"""\r\n'
      + '1,3,,,Ipê,28/07/2026,30,3,6,,15,')

    # 4. Problemas diversos
    w("problemas.csv", h + "\n" + "\n".join([
        "1,1,,,Ipê,28/07/2026,10,2,4,,8,",                                  # válido
        "1,2,,,Ipê,28/07/2026,MORTA,,,,,",                                   # DAP textual / estado vital
        "1,3,,,Ipê,28/07/2026,-5,,,,6,",                                     # DAP negativo
        "1,4,,,Ipê,28/07/2026,350,,,,25,",                                   # DAP extremo
        ",5,,,Ipê,28/07/2026,12,,,,7,",                                      # parcela ausente
        "1,,,,Ipê,28/07/2026,12,,,,7,",                                      # árvore ausente
        "1,6,,,,28/07/2026,15,,,,9,",                                        # espécie ausente
        "1,7,,,Ipê,,16,,,,9,",                                               # data ausente
        "2,1,,,Cedro,28/07/2026,20,,,,10,",                                  # duplicidade (mesma data)
        "2,1,,,Cedro,28/07/2026,21,,,,10,",
        "3,1,,,Jatobá,28/07/2026,20,,,,10,",                                 # duas campanhas
        "3,1,,,Jatobá,28/01/2027,22,,,,11,",
        "1,8,,,Ipê,28/07/2026,10,2,4,,8,obs,EXTRA",                          # linha deslocada (13 campos)
        "continuação de observação sem aspas",                               # fragmento
        "1,9,,,Ipê,28/07/2026,1.2,5,,,,7,",                                  # deslocada: vírgula decimal sem aspas
        "1,10,,,Ipê,28/07/2026,,,,,,MORTA",                                  # DAP vazio + menção de morte
        "1,11,,,Ipê,28/07/2026,,,,,,2 fustes: 10.0 e 9.4",                   # multifuste
        "07,1,,,Ipê,28/07/2026,10,,,,8,",                                    # '07' ≠ '7'
        "7,1,,,Ipê,28/07/2026,10,,,,8,sem bromélias",                        # negação
    ]) + "\n")

    # 5. Área basal: DAPs 10, 20, 30 cm (seção 32)
    w("area_basal.csv", h + "\n" + "\n".join([
        "1,1,,,A,28/07/2026,10,,,,,",
        "1,2,,,A,28/07/2026,20,,,,,",
        "1,3,,,B,28/07/2026,30,,,,,",
    ]) + "\n")

    # 5b. Área basal por hectare: exemplo do documento de fórmulas (DAP 20, 30, 40, 50 cm; Sc = 0,42412 m²)
    #     + parcela 2 inventariada sem árvores (entra na área amostrada, contribui G = 0)
    w("ab_hectare.csv", h + "\n" + "\n".join([
        "1,1,,,A,28/07/2026,20,,,,,",
        "1,2,,,A,28/07/2026,30,,,,,",
        "1,3,,,B,28/07/2026,40,,,,,",
        "1,4,,,B,28/07/2026,50,,,,,",
        "2,NÃO TEM ÁRVORES,,,,,,,,,,NÃO TEM",
    ]) + "\n")

    # 5b'. Copa (HT − HESGCOPA): 2 elegíveis, 1 incoerente (HESGCOPA > HT), 1 sem HESGCOPA
    w("copa.csv", h + "\n" + "\n".join([
        "1,1,,,A,28/07/2026,10,,4,,10,",    # copa 6 m, 60 %
        "1,2,,,A,28/07/2026,20,,5,,20,",    # copa 15 m, 75 %
        "1,3,,,A,28/07/2026,30,,12,,10,",   # HESGCOPA > HT → excluído da copa
        "1,4,,,A,28/07/2026,40,,,,8,",      # sem HESGCOPA → excluído da copa
    ]) + "\n")

    # 5c. Multifuste (regra de Finger, 1992): extração estrita dos fustes declarados na observação
    w("multifuste.csv", h + "\n" + "\n".join([
        "1,1,,,A,28/07/2026,20,,,,,",                                        # fuste único
        '1,2,,,A,28/07/2026,,,,,,"3 fustes: 3, 4 e 12"',                     # extraído: d_eq = 13
        '1,3,,,A,28/07/2026,,,,,,"2 fustes: 5, 6 e 7"',                      # contagem divergente → revisão
        '1,4,,,A,28/07/2026,44.4,,,,,"2 fustes: 15.0 e 33.5"',               # DAP da coluna ≠ fustes → revisão
        '1,5,,,A,28/07/2026,8.8,,,,,"2 fustes - 8.8 e 7.2"',                 # extraído (DAP = 1º fuste)
    ]) + "\n")

    # 6. XLSX com tipos reais de célula
    wb = Workbook()
    ws = wb.active
    ws.title = "dendrometria"
    ws.append(HEADER)
    ws.append([1, 1, None, None, "Ipê", dt.datetime(2026, 7, 28), 10, 2, 4, None, 8, None])
    ws.append([1, 2, None, None, "Ipê", dt.datetime(2026, 7, 28), "20.5", "3.2", 5, None, 12, None])
    ws.append([1, 3, None, None, "Ipê", dt.datetime(2026, 7, 28), dt.datetime(2026, 5, 12), 3, 5, None, 12, None])
    ws["G4"].number_format = "d\\.m"  # DAP '12.5' convertido em data pelo Excel
    ws.append([1, 4, None, None, "Ipê", dt.datetime(2026, 7, 28), 15, 3, 5, None, dt.datetime(2026, 5, 9), None])
    ws["K5"].number_format = "d\\.m"  # HT como data
    ws.append([1, 5, None, None, "Ipê", dt.datetime(2026, 7, 28), None, None, None, None, None, "MORTA"])
    ws.append([None] * 12)
    ws.append([2, "NÃO TEM ÁRVORES", None, None, None, None, None, None, None, None, None, "NÃO TEM"])
    ws2 = wb.create_sheet("MAPA")
    ws2["A1"] = "mapa"
    wb.save(SYN / "valido.xlsx")

    # 7. Estado vital estruturado (para mortalidade)
    hv = h + ",Estado vital"
    w("estado_vital.csv", hv + "\n" + "\n".join([
        "1,1,,,Ipê,28/07/2026,10,,,,8,,vivo",
        "1,2,,,Ipê,28/07/2026,,,,,,,morto",
        "1,3,,,Ipê,28/07/2026,12,,,,9,,vivo",
        "1,4,,,Ipê,28/07/2026,,,,,,,não localizado",
        "2,1,,,Cedro,28/07/2026,20,,,,10,,vivo",
    ]) + "\n")

    # ------------------------------------------------------------ esperados (cálculo manual)
    g = lambda d: math.pi * d * d / 40000.0  # noqa: E731
    daps = [10, 20, 30, 40, 50]
    m = sum(daps) / 5  # 30
    var = sum((d - m) ** 2 for d in daps) / 4  # 1000/4 = 250
    expected = {
        "area_basal": {
            "dap_cm": [10, 20, 30],
            "g_m2": [g(10), g(20), g(30)],
            "G_total_m2": 0.10995574287564276,
            "G_media_m2": 0.10995574287564276 / 3,
            "g_max_m2": g(30),
            "calculo": "g = π·DAP²/40000: 0,007853981634 + 0,031415926536 + 0,070685834706 = 0,109955742876 m²",
        },
        "ab_hectare": {
            "G_total_m2": math.pi * (20 ** 2 + 30 ** 2 + 40 ** 2 + 50 ** 2) / 40000.0,
            "parcela_1_area_ha": 0.10,
            "G_ha_parcela_1": math.pi * 5400 / 40000.0 / 0.10,
            "G_ha_duas_parcelas": math.pi * 5400 / 40000.0 / 0.20,
            "dg_cm": math.sqrt((20 ** 2 + 30 ** 2 + 40 ** 2 + 50 ** 2) / 4),
            "calculo": "Sc = π·5400/40000 = 0,424115 m²; parcela 1 (0,10 ha) → 4,2412 m²/ha (exemplo do documento); "
                       "com a parcela 2 sem árvores, A = 0,20 ha → 2,1206 m²/ha; dg = √(5400/4) = √1350 = 36,7423 cm",
        },
        "copa": {"comprimento_medio_m": (6 + 15) / 2, "proporcao_media_pct": (60 + 75) / 2,
                 "n_elegivel": 2, "n_potencial": 4,
                 "calculo": "(10−4)=6 m (60 %); (20−5)=15 m (75 %); média 10,5 m e 67,5 %; árvores 3 e 4 excluídas"},
        "multifuste": {
            "G_coluna_m2": g(20) + g(44.4) + g(8.8),
            "G_multifuste_m2": g(20) + math.pi * (3 ** 2 + 4 ** 2 + 12 ** 2) / 40000.0 + g(44.4)
            + math.pi * (8.8 ** 2 + 7.2 ** 2) / 40000.0,
            "calculo": "G' = g(20) + π·(9+16+144)/40000 + g(44,4) + π·(77,44+51,84)/40000; "
                       "árvore 3 (contagem divergente) e fustes da árvore 4 (DAP ≠ fustes) não entram",
        },
        "valido_csv": {
            "dap_media_cm": m, "dap_mediana_cm": 30.0, "dap_min_cm": 10.0, "dap_max_cm": 50.0,
            "dap_q1_cm": 20.0, "dap_q3_cm": 40.0,
            "dap_dp_cm": math.sqrt(var), "dap_cv_pct": math.sqrt(var) / m * 100,
            "ht_media_m": (8 + 12 + 15 + 18 + 20) / 5,
            "G_total_m2": sum(g(d) for d in daps),
            "v_cil_total_m3": g(10) * 8 + g(20) * 12 + g(30) * 15 + g(40) * 18 + g(50) * 20,
            "v_spurr_total_m3": (0.106531813 + 5.3372e-5 * 20 ** 2 * 6) + (0.106531813 + 5.3372e-5 * 40 ** 2 * 8),
            "individuos": 5, "parcelas": 2, "especies": 3,
            # Ipê 2, Cedro 2, Jatobá 1 (N = 5): p = 0,4; 0,4; 0,2
            "shannon": -(0.4 * math.log(0.4) * 2 + 0.2 * math.log(0.2)),
            "pielou": -(0.4 * math.log(0.4) * 2 + 0.2 * math.log(0.2)) / math.log(3),
            "simpson_1_menos_D": 1 - (2 * 1 + 2 * 1 + 1 * 0) / (5 * 4),
            "DoR_cedro_pct": (30 ** 2 + 40 ** 2) / (10 ** 2 + 20 ** 2 + 30 ** 2 + 40 ** 2 + 50 ** 2) * 100,
            "calculo": "x̄ = 150/5 = 30; s² = (400+100+0+100+400)/4 = 250; s = 15,8113883; CV = 52,7046277 %; "
                       "Q1/Q3 por interpolação linear: posição 1 → 20, posição 3 → 40",
        },
        "estado_vital": {"sobrevivencia_pct": 3 / 72 * 100,
                         "calculo": "implantados 36 + 36 = 72; mortos 1 → 1,3889 %; vivos 3 → 4,1667 %",
                         "mortalidade_total_pct": 1 / 72 * 100},
    }
    (EXP / "esperados.json").write_text(json.dumps(expected, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Fixtures geradas em", SYN)


if __name__ == "__main__":
    main()
