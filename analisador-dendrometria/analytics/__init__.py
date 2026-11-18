"""Analisador de Dendrometria — camada analítica (independente da interface).

``run_analysis`` é o único ponto que a interface chama: recebe os registros
canônicos já validados, aplica os filtros ANTES de calcular e devolve todos os
indicadores e tabelas prontos para exibição.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass, field

import pandas as pd

from . import dendrometry as dd
from . import inventory as inv
from . import observations as obs
from .ingestion import ImportMetadata
from .results import Indicator, Metodologia


@dataclass
class Filters:
    parcelas: list[str] = field(default_factory=list)
    especies: list[str] = field(default_factory=list)
    arvores: list[str] = field(default_factory=list)
    data_inicio: dt.date | None = None
    data_fim: dt.date | None = None
    dap_min: float | None = None
    dap_max: float | None = None
    manter_sem_dap: bool = True
    ht_min: float | None = None
    ht_max: float | None = None
    manter_sem_ht: bool = True
    status: list[str] = field(default_factory=list)
    observacao: str = "todos"  # todos | com | sem

    def is_active(self) -> bool:
        return self.describe() != {}

    def describe(self) -> dict:
        d = {}
        for k, v in asdict(self).items():
            if k in ("manter_sem_dap", "manter_sem_ht"):
                continue
            if v in (None, [], "todos"):
                continue
            d[k] = v.isoformat() if isinstance(v, dt.date) else v
        if "dap_min" in d or "dap_max" in d:
            d["manter_sem_dap"] = self.manter_sem_dap
        if "ht_min" in d or "ht_max" in d:
            d["manter_sem_ht"] = self.manter_sem_ht
        return d


def _range(df: pd.DataFrame, col: str, lo, hi, keep_missing: bool) -> pd.Series:
    v = df[col]
    ok = pd.Series(True, index=df.index)
    if lo is not None:
        ok &= v >= lo
    if hi is not None:
        ok &= v <= hi
    if lo is None and hi is None:
        return ok
    return ok | (v.isna() & keep_missing)


def apply_filters(records: pd.DataFrame, f: Filters) -> pd.DataFrame:
    if records.empty or not f.is_active():
        return records
    m = pd.Series(True, index=records.index)
    if f.parcelas:
        m &= records["parcela"].isin(f.parcelas)
    if f.especies:
        m &= records["especie"].isin(f.especies)
    if f.arvores:
        m &= records["arvore"].isin(f.arvores)
    if f.data_inicio:
        m &= records["data_medicao"].map(lambda d: d is not None and d >= f.data_inicio)
    if f.data_fim:
        m &= records["data_medicao"].map(lambda d: d is not None and d <= f.data_fim)
    m &= _range(records, "dap_cm", f.dap_min, f.dap_max, f.manter_sem_dap)
    m &= _range(records, "ht_m", f.ht_min, f.ht_max, f.manter_sem_ht)
    if f.status:
        m &= records["status_registro"].isin(f.status)
    if f.observacao == "com":
        m &= records["observacao"].notna()
    elif f.observacao == "sem":
        m &= records["observacao"].isna()
    return records[m]


@dataclass
class AnalysisResult:
    filtrado: bool
    n_registros: int
    gerais: list[Indicator]
    dap: list[Indicator]
    alturas: dict[str, list[Indicator]]
    area_basal: list[Indicator]
    volumes: list[Indicator]
    mortalidade: list[Indicator]
    mortalidade_tabela: pd.DataFrame
    replantio: pd.DataFrame
    replantio_notas: list[str]
    parcelas: pd.DataFrame
    especies: pd.DataFrame
    individuos: pd.DataFrame
    rankings: dict[str, pd.DataFrame]
    distribuicao: pd.DataFrame
    distribuicao_info: dict
    mencoes: pd.DataFrame
    elegibilidade_dap: pd.DataFrame
    metodologia: Metodologia = field(default_factory=Metodologia)
    diversidade: list[Indicator] = field(default_factory=list)
    copa: list[Indicator] = field(default_factory=list)
    multifustes: pd.DataFrame = field(default_factory=pd.DataFrame)

    def all_indicators(self) -> list[Indicator]:
        out = list(self.gerais) + list(self.dap)
        for v in self.alturas.values():
            out += v
        return out + list(self.area_basal) + list(self.volumes) + list(self.copa) + list(self.diversidade) + list(self.mortalidade)


def run_analysis(records: pd.DataFrame, issues: pd.DataFrame, meta: ImportMetadata | None,
                 filters: Filters | None = None, incluir_extremos: bool = False, largura_classe_cm: float = 5.0,
                 implantados: dict[str, int] | int | None = 36, mortalidade_ativa: bool = True,
                 top_n: int = 10, metodologia: Metodologia | None = None) -> AnalysisResult:
    filters = filters or Filters()
    metodologia = metodologia or Metodologia()
    df = apply_filters(records, filters)
    fl = filters.is_active()
    dist, info = dd.diameter_distribution(df, largura_classe_cm, incluir_extremos=incluir_extremos) if len(df) \
        else (pd.DataFrame(), {"n_elegivel": 0, "n_potencial": 0, "n_excluido": 0, "motivos": {}})
    mort, mort_tab = inv.mortality(df, implantados, mortalidade_ativa, fl)
    rep, rep_notas = inv.replanting(df)
    el = dd.dap_eligibility(df, incluir_extremos) if len(df) else pd.DataFrame()
    return AnalysisResult(
        filtrado=fl,
        n_registros=len(df),
        gerais=inv.general_indicators(df, issues, meta, incluir_extremos, fl),
        dap=dd.dap_indicators(df, incluir_extremos, fl) if len(df) else [],
        alturas=dd.height_indicators(df, fl) if len(df) else {},
        copa=dd.crown_indicators(df, fl) if len(df) else [],
        area_basal=(dd.basal_area_indicators(df, incluir_extremos, fl, metodologia)
                    + [dd.multifuste_indicator(df, incluir_extremos, fl)]) if len(df) else [],
        volumes=dd.volume_indicators(df, incluir_extremos, fl) if len(df) else [],
        mortalidade=mort, mortalidade_tabela=mort_tab, replantio=rep, replantio_notas=rep_notas,
        parcelas=inv.plot_table(df, incluir_extremos, metodologia),
        especies=inv.species_table(df, incluir_extremos),
        individuos=inv.individuals_table(df, incluir_extremos),
        rankings={k: dd.ranking(df, k, top_n, incluir_extremos) for k in ("dap", "ht", "g")} if len(df) else {},
        distribuicao=dist, distribuicao_info=info,
        mencoes=obs.mentions_table(df) if len(df) else pd.DataFrame(),
        elegibilidade_dap=el,
        metodologia=metodologia,
        diversidade=inv.diversity_indicators(df, fl) if len(df) else [],
        multifustes=dd.multifuste_table(df, incluir_extremos) if len(df) else pd.DataFrame(),
    )
