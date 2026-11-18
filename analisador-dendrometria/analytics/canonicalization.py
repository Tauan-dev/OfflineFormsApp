"""Mapeamento de colunas e interpretação determinística de valores.

Regras:
- somente variações de cabeçalho explicitamente listadas são aceitas;
- identificadores: remove-se apenas espaço externo ("07" ≠ "7");
- números: aceita-se vírgula OU ponto como separador decimal (um único);
- nada é corrigido por adivinhação: datas em colunas numéricas, textos,
  infinitos e negativos são classificados, nunca convertidos.
"""
from __future__ import annotations

import datetime as dt
import math
import re
import unicodedata
from dataclasses import dataclass

from .ingestion import Cell

# ------------------------------------------------------------ colunas canônicas
# id canônico -> (rótulo de exibição, obrigatória?, variações aceitas)
CANONICAL_COLUMNS: dict[str, tuple[str, bool, tuple[str, ...]]] = {
    "parcela": ("Parcela", True, ("Parcela",)),
    "arvore": ("Árvore", True, ("Árvore", "Arvore")),
    "plantio": ("Plantio", False, ("Plantio", "Data Plantio", "Data de Plantio")),
    "replantio": ("Replantio", False, ("Replantio", "Data Replantio", "Data de Replantio")),
    "especie": ("Nome Comum", True, ("Nome Comum", "Nome comum")),
    "data_medicao": ("Data Medição", True, ("Data Medição", "Data medição", "Data Medicao", "Data medicao")),
    "dap_cm": ("DAP (cm)", True, ("DAP (cm)", "DAP")),
    "hesg_m": ("HESG (m)", False, ("HESG (m)", "HESG")),
    "hesgcopa_m": ("HESGCOPA (m)", False, ("HESGCOPA (m)", "HESGCOPA")),
    "hc_m": ("HC (m)", False, ("HC (m)", "HC")),
    "ht_m": ("HT (m)", False, ("HT (m)", "HT")),
    "observacao": ("Observação", False, ("Observação", "Observacao", "Observações", "Observacoes")),
    "estado_vital": ("Estado vital", False, ("Estado vital", "Estado Vital")),
}
NUMERIC_COLUMNS = ("dap_cm", "hesg_m", "hesgcopa_m", "hc_m", "ht_m")
HEIGHT_COLUMNS = ("hesg_m", "hesgcopa_m", "hc_m", "ht_m")
DATE_COLUMNS = ("plantio", "replantio", "data_medicao")
LABEL = {k: v[0] for k, v in CANONICAL_COLUMNS.items()}


def _header_key(h: str) -> str:
    return " ".join(str(h).split())


@dataclass
class ColumnMapping:
    mapping: dict[str, int]  # id canônico -> índice da coluna de origem
    originals: dict[str, str]  # id canônico -> cabeçalho original
    missing_required: list[str]
    ambiguous: dict[str, list[str]]
    unmapped_headers: list[str]

    @property
    def is_safe(self) -> bool:
        return not self.missing_required and not self.ambiguous


def auto_map(headers: list[str]) -> ColumnMapping:
    mapping: dict[str, int] = {}
    originals: dict[str, str] = {}
    ambiguous: dict[str, list[str]] = {}
    for cid, (_, _, variants) in CANONICAL_COLUMNS.items():
        accepted = {_header_key(v) for v in variants}
        hits = [i for i, h in enumerate(headers) if _header_key(h) in accepted]
        if len(hits) == 1:
            mapping[cid] = hits[0]
            originals[cid] = headers[hits[0]]
        elif len(hits) > 1:
            ambiguous[cid] = [headers[i] for i in hits]
    missing = [c for c, (_, req, _) in CANONICAL_COLUMNS.items() if req and c not in mapping and c not in ambiguous]
    used = set(mapping.values())
    unmapped = [h for i, h in enumerate(headers) if i not in used]
    return ColumnMapping(mapping, originals, missing, ambiguous, unmapped)


def manual_map(headers: list[str], choices: dict[str, str | None]) -> ColumnMapping:
    """Mapeamento escolhido pelo usuário (cabeçalho original por id canônico)."""
    mapping, originals = {}, {}
    for cid, h in choices.items():
        if h is None or h == "":
            continue
        if h not in headers:
            raise ValueError(f"Cabeçalho inexistente: {h}")
        mapping[cid] = headers.index(h)
        originals[cid] = h
    dup = {}
    for cid, idx in mapping.items():
        dup.setdefault(idx, []).append(cid)
    ambiguous = {cids[0]: [headers[idx]] for idx, cids in dup.items() if len(cids) > 1}
    missing = [c for c, (_, req, _) in CANONICAL_COLUMNS.items() if req and c not in mapping]
    used = set(mapping.values())
    return ColumnMapping(mapping, originals, missing, ambiguous, [h for i, h in enumerate(headers) if i not in used])


# ------------------------------------------------------------ texto
def strip_outer(s: str) -> str:
    return s.strip()


def fold(s: str) -> str:
    """Minúsculas sem acento — usado só para BUSCA e detecção de variantes, nunca como valor."""
    nfkd = unicodedata.normalize("NFKD", s.casefold())
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


# ------------------------------------------------------------ números
_NUM_RE = re.compile(r"^[+-]?\d+(?:[.,]\d+)?$")


@dataclass
class NumParse:
    status: str  # NUMERO | AUSENTE | TEXTO | DATA | NAO_FINITO | BOOLEANO
    value: float | None
    original: object
    normalized: str
    trimmed: bool = False  # havia espaço externo (recuperação automática)
    display_hint: str | None = None  # para DATA: como a célula aparecia (somente revisão humana)


def _date_display(cell: Cell) -> str | None:
    """Texto que a planilha exibiria para uma data em formato 'd.m' / 'd\\.m'.

    Usado APENAS como pista para revisão humana: não é usado em cálculo,
    porque '12.05' e '12.5' produzem a mesma data e não podem ser distinguidos.
    """
    v = cell.value
    if not isinstance(v, (dt.datetime, dt.date)):
        return None
    fmt = cell.number_format.replace("\\", "")
    if fmt in ("d.m", "dd.mm", "d.mm", "dd.m"):
        return f"{v.day}.{v.month}"
    return v.strftime("%d/%m/%Y")


def parse_number(cell: Cell) -> NumParse:
    v = cell.value
    if cell.kind == "vazio":
        return NumParse("AUSENTE", None, v, "")
    if cell.kind == "booleano":
        return NumParse("BOOLEANO", None, v, str(v))
    if cell.kind == "data":
        return NumParse("DATA", None, v, str(v), display_hint=_date_display(cell))
    if cell.kind in ("inteiro", "decimal"):
        f = float(v)
        if not math.isfinite(f):
            return NumParse("NAO_FINITO", None, v, str(v))
        return NumParse("NUMERO", f, v, repr(v) if cell.kind == "decimal" else str(v))
    s = str(v)
    t = s.strip()
    if t == "":
        return NumParse("AUSENTE", None, v, "", trimmed=s != t)
    if _NUM_RE.match(t):
        f = float(t.replace(",", "."))
        return NumParse("NUMERO", f, v, t.replace(",", "."), trimmed=s != t)
    if fold(t) in ("inf", "+inf", "-inf", "infinity", "nan", "#num!", "#div/0!", "#valor!", "#value!"):
        return NumParse("NAO_FINITO", None, v, t, trimmed=s != t)
    return NumParse("TEXTO", None, v, t, trimmed=s != t)


# ------------------------------------------------------------ identificadores
_CODE_RE = re.compile(r"^[A-Za-z]{1,4}-?\d+[A-Za-z]?$")
_DIGITS_RE = re.compile(r"^\d+$")


@dataclass
class IdParse:
    status: str  # NUMERICO | CODIGO | AUSENTE | TEXTO_LIVRE | INVALIDO
    value: str | None
    original: object
    trimmed: bool = False


def parse_id(cell: Cell) -> IdParse:
    v = cell.value
    if cell.kind == "vazio":
        return IdParse("AUSENTE", None, v)
    if cell.kind == "inteiro":
        return IdParse("NUMERICO", str(v), v)
    if cell.kind == "decimal":
        if math.isfinite(v) and float(v).is_integer():
            return IdParse("NUMERICO", str(int(v)), v)
        return IdParse("INVALIDO", None, v)
    if cell.kind in ("data", "booleano"):
        return IdParse("INVALIDO", None, v)
    s = str(v)
    t = s.strip()
    if t == "":
        return IdParse("AUSENTE", None, v, trimmed=True)
    if _DIGITS_RE.match(t):
        return IdParse("NUMERICO", t, v, trimmed=s != t)  # '07' preservado como '07'
    if _CODE_RE.match(t):
        return IdParse("CODIGO", t, v, trimmed=s != t)
    return IdParse("TEXTO_LIVRE", None, v, trimmed=s != t)


# ------------------------------------------------------------ datas
_BR_DATE = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")
_ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:[ T]00:00(?::00)?)?$")


@dataclass
class DateParse:
    status: str  # DATA | AUSENTE | INVALIDA | SERIAL
    value: dt.date | None
    original: object


def parse_date(cell: Cell) -> DateParse:
    v = cell.value
    if cell.kind == "vazio":
        return DateParse("AUSENTE", None, v)
    if cell.kind == "data":
        if isinstance(v, dt.datetime):
            return DateParse("DATA", v.date(), v)
        if isinstance(v, dt.date):
            return DateParse("DATA", v, v)
        return DateParse("INVALIDA", None, v)
    if cell.kind in ("inteiro", "decimal"):
        return DateParse("SERIAL", None, v)  # nunca convertido silenciosamente
    t = str(v).strip()
    if t == "":
        return DateParse("AUSENTE", None, v)
    m = _BR_DATE.match(t)
    try:
        if m:
            return DateParse("DATA", dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1))), v)
        m = _ISO_DATE.match(t)
        if m:
            return DateParse("DATA", dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))), v)
    except ValueError:
        return DateParse("INVALIDA", None, v)  # ex.: 31/02/2025
    if re.match(r"^\d+(?:[.,]\d+)?$", t):
        return DateParse("SERIAL", None, v)
    return DateParse("INVALIDA", None, v)


def natural_key(s: str | None) -> tuple:
    """Ordenação determinística: números antes de códigos, numéricos por valor."""
    if s is None:
        return (2, "", 0)
    if s.isdigit():
        return (0, "", int(s), s)
    m = re.match(r"^([A-Za-z-]+)(\d+)", s)
    if m:
        return (1, m.group(1).upper(), int(m.group(2)), s)
    return (1, s.upper(), 0, s)
