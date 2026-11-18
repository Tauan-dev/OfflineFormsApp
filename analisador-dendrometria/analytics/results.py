"""Contrato dos indicadores, estados permitidos e tolerâncias numéricas.

Todo indicador produzido pelo analisador é uma instância de ``Indicator``.
A interface apenas exibe esses objetos; ela não recalcula nada.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any

ANALISADOR_VERSAO = "1.1.0"
VERSAO_METODOLOGICA = "dendro-2026.11-r1"

# Estados permitidos para indicadores (seção 10 da especificação)
VALIDO = "VÁLIDO"
VALIDO_RESSALVA = "VÁLIDO COM RESSALVA"
INDISPONIVEL = "INDISPONÍVEL"
BLOQ_METODOLOGIA = "BLOQUEADO POR METODOLOGIA"
BLOQ_QUALIDADE = "BLOQUEADO POR QUALIDADE"
BLOQ_QUALIDADE_OU_METODOLOGIA = "BLOQUEADO POR QUALIDADE OU METODOLOGIA"

ESTADOS_INDICADOR = (
    VALIDO,
    VALIDO_RESSALVA,
    INDISPONIVEL,
    BLOQ_METODOLOGIA,
    BLOQ_QUALIDADE,
    BLOQ_QUALIDADE_OU_METODOLOGIA,
)
ESTADOS_SEM_VALOR = (INDISPONIVEL, BLOQ_METODOLOGIA, BLOQ_QUALIDADE, BLOQ_QUALIDADE_OU_METODOLOGIA)


@dataclass(frozen=True)
class Tolerancia:
    """Critério de comparação |produzido − esperado| ≤ atol + rtol·|esperado|.

    Referência: Burden & Faires, *Análise Numérica* — erro absoluto, erro
    relativo e comparação de ponto flutuante. Os valores são definidos por
    grandeza, com justificativa, e não como tolerância universal.
    """

    atol: float
    rtol: float
    justificativa: str

    def aceita(self, produzido: float, esperado: float) -> bool:
        return abs(produzido - esperado) <= self.atol + self.rtol * abs(esperado)


# A dupla precisão (IEEE-754, ε ≈ 2,2e-16) dá ~15 dígitos significativos.
# Somas com math.fsum e o algoritmo de duas passagens para variância mantêm o
# erro de arredondamento na ordem de n·ε; as tolerâncias abaixo ficam algumas
# ordens de grandeza acima disso e bem abaixo da resolução de campo
# (DAP medido a 0,1 cm; alturas a 0,1 m).
TOLERANCIAS: dict[str, Tolerancia] = {
    "contagem": Tolerancia(0.0, 0.0, "Contagens são inteiras: comparação exata."),
    "dap_cm": Tolerancia(1e-9, 1e-12, "Estatísticas de DAP (cm): resolução de campo 0,1 cm ≫ 1e-9 cm."),
    "altura_m": Tolerancia(1e-9, 1e-12, "Estatísticas de altura (m): resolução de campo 0,1 m ≫ 1e-9 m."),
    "dispersao": Tolerancia(1e-9, 1e-9, "Desvio-padrão e CV envolvem raiz quadrada e divisão; rtol 1e-9."),
    "area_basal_m2": Tolerancia(1e-12, 1e-9, "g ~ 1e-4 a 1 m²; atol 1e-12 m² e rtol 1e-9 cobrem o erro de π·d²/40000 em dupla precisão."),
    "volume_m3": Tolerancia(1e-12, 1e-9, "Produto de g por altura ou polinômio de Spurr: mesma ordem de erro da área basal."),
    "percentual": Tolerancia(1e-9, 0.0, "Percentuais (0–100): erro absoluto de 1e-9 ponto percentual."),
    "indice": Tolerancia(1e-12, 1e-9, "Índices de diversidade (ordem 0–10): soma de termos p·ln p com math.fsum; "
                                      "atol 1e-12 e rtol 1e-9 ficam muito acima do erro de arredondamento."),
}


@dataclass
class Indicator:
    id: str
    nome: str
    valor: Any
    unidade: str
    denominador: str
    quantidade_potencial: int | None
    quantidade_elegivel: int | None
    quantidade_excluida: int | None
    motivos_exclusao: dict[str, int] = field(default_factory=dict)
    cobertura: float | None = None  # fração 0–1
    versao_metodologica: str = VERSAO_METODOLOGICA
    status: str = VALIDO
    observacoes: list[str] = field(default_factory=list)
    formula: str = ""
    tolerancia: str = ""
    filtrado: bool = False

    def __post_init__(self) -> None:
        if self.status not in ESTADOS_INDICADOR:
            raise ValueError(f"Estado inválido: {self.status}")
        if self.status in ESTADOS_SEM_VALOR:
            # Indicador indisponível ou bloqueado nunca carrega valor (nunca zero).
            self.valor = None
        if isinstance(self.valor, float) and not math.isfinite(self.valor):
            raise ValueError(f"Indicador {self.id} produziu valor não finito")

    @property
    def disponivel(self) -> bool:
        return self.status in (VALIDO, VALIDO_RESSALVA)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["cobertura_pct"] = None if self.cobertura is None else round(self.cobertura * 100, 6)
        return d


def cobertura(elegivel: int, potencial: int) -> float | None:
    """Fração elegível/potencial; None quando o denominador é zero (nunca divide por zero)."""
    if potencial <= 0:
        return None
    return elegivel / potencial


def bloqueado(id_: str, nome: str, unidade: str, motivo: str, status: str = BLOQ_METODOLOGIA,
              formula: str = "", filtrado: bool = False) -> Indicator:
    return Indicator(
        id=id_, nome=nome, valor=None, unidade=unidade, denominador="—",
        quantidade_potencial=None, quantidade_elegivel=None, quantidade_excluida=None,
        status=status, observacoes=[motivo], formula=formula, filtrado=filtrado,
    )


UNIDADES_AREA = {"m²": 1.0 / 10000.0, "ha": 1.0}  # fator de conversão para hectares


@dataclass
class Metodologia:
    """Decisões metodológicas informadas EXPLICITAMENTE pelo usuário em uma execução.

    Sem área e desenho amostral, a área basal por hectare permanece BLOQUEADA
    POR METODOLOGIA. Quando informados (pelo usuário ou pela predefinição da
    literatura), são registrados no manifesto e o indicador liberado recebe
    status VÁLIDO COM RESSALVA.
    """

    area_parcela: float | dict[str, float] | None = None  # valor único ou por parcela
    unidade_area: str = "m²"  # "m²" ou "ha"
    desenho_amostral: str = ""  # descrição obrigatória para liberar o cálculo por hectare
    fonte: str = "usuário"  # "usuário" ou referência bibliográfica (predefinição da literatura)
    sensibilidade_m2: tuple = ()  # áreas alternativas (m²) reportadas como análise de sensibilidade

    def area_ha(self, parcela: str) -> float | None:
        """Área da parcela em hectares; None se não informada ou inválida (≤ 0, não finita)."""
        if self.area_parcela is None or self.unidade_area not in UNIDADES_AREA:
            return None
        v = self.area_parcela.get(parcela) if isinstance(self.area_parcela, dict) else self.area_parcela
        try:
            v = float(v)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(v) or v <= 0:
            return None
        return v * UNIDADES_AREA[self.unidade_area]

    @property
    def por_hectare_informado(self) -> bool:
        return self.area_parcela is not None and bool(self.desenho_amostral.strip())

    def describe(self) -> dict[str, Any]:
        return {
            "area_parcela": self.area_parcela, "unidade_area": self.unidade_area,
            "desenho_amostral": self.desenho_amostral.strip() or None, "fonte": self.fonte,
        }

    def decisoes(self) -> list[str]:
        out = []
        if self.por_hectare_informado:
            a = ("por parcela" if isinstance(self.area_parcela, dict) else f"{self.area_parcela:g} {self.unidade_area}")
            out.append(f"Área basal por hectare (fonte: {self.fonte}): área da parcela {a}; desenho amostral: "
                       f"{self.desenho_amostral.strip()}; ABₕₐ = G / A; fator de expansão F = 1 / a (ha).")
        return out


# ------------------------------------------------------------ predefinição da literatura
ESARM_PARCELAS = 98
ESARM_AREA_M2 = 36 * 2.0 * 2.0  # 36 plantas × 4 m² por planta (espaçamento 2 × 2 m) = 144 m²
ESARM_REFERENCIAS = ("Barazetti et al. (2011), Unoesc & Ciência – ACET 2(1):31-46 — arboreto da ESARM/CEPLAC, "
                     "Ilhéus: 98 parcelas, 36 indivíduos da mesma espécie, 6 linhas × 6 colunas, espaçamento 2 × 2 m; "
                     "Gama-Rodrigues, Barros & Mendonça (1999), R. Bras. Ci. Solo 23:581-592 — arboreto CEPLAC/ESPAB: "
                     "parcelas puras de 144 m², 2 × 2 m, 36 árvores por espécie")


def esarm_aplicavel(parcelas) -> bool:
    """A predefinição só vale se as parcelas numéricas do arquivo couberem no desenho publicado (1–98)."""
    num = [str(p) for p in parcelas if str(p).isdigit()]
    return bool(num) and all(1 <= int(p) <= ESARM_PARCELAS and str(int(p)) == p for p in num)


def metodologia_arboreto_esarm() -> Metodologia:
    return Metodologia(
        area_parcela={str(i): ESARM_AREA_M2 for i in range(1, ESARM_PARCELAS + 1)}, unidade_area="m²",
        desenho_amostral=("censo de parcelas monoespecíficas do arboreto da ESARM/CEPLAC (todas as árvores medidas, "
                          "sem amostragem); 36 plantas em grade 6 × 6, espaçamento 2 × 2 m → área útil 144 m² "
                          "(36 × 4 m²). Os 100 m² citados por Barazetti et al. correspondem ao polígono entre as "
                          "árvores externas ((6 − 1) × 2 m)²; a área útil é a que reproduz a densidade do "
                          "espaçamento (2.500 plantas/ha). Corredores de 4 m entre parcelas não entram em A."),
        fonte="literatura — " + ESARM_REFERENCIAS,
        sensibilidade_m2=(100.0, 196.0))  # polígono entre árvores externas; área com corredor de 4 m


def indicadores_para_tabela(inds: list[Indicator]) -> list[dict[str, Any]]:
    linhas = []
    for i in inds:
        linhas.append({
            "id": i.id,
            "indicador": i.nome,
            "valor": i.valor,
            "unidade": i.unidade,
            "status": i.status,
            "denominador": i.denominador,
            "potencial": i.quantidade_potencial,
            "elegível": i.quantidade_elegivel,
            "excluído": i.quantidade_excluida,
            "cobertura (%)": None if i.cobertura is None else round(i.cobertura * 100, 2),
            "motivos de exclusão": "; ".join(f"{k}: {v}" for k, v in i.motivos_exclusao.items()),
            "fórmula": i.formula,
            "observações": " | ".join(i.observacoes),
            "versão metodológica": i.versao_metodologica,
            "filtrado": "sim" if i.filtrado else "não",
        })
    return linhas
