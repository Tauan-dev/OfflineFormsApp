import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analytics import canonicalization as canon  # noqa: E402
from analytics import ingestion, quality  # noqa: E402
from analytics.results import TOLERANCIAS  # noqa: E402

SYN = ROOT / "fixtures" / "synthetic"
EXPECTED = json.loads((ROOT / "fixtures" / "expected" / "esperados.json").read_text(encoding="utf-8"))
REAL_FILE = ROOT.parent / "OfflineFormsApp" / "referencias" / "DENDROMETRIA.xlsx_15-09_ATUAL.xlsx"


def load(name: str, sheet: str | None = None):
    data = (SYN / name).read_bytes()
    raw = ingestion.read_file(data, name, sheet)
    q = quality.build_records(raw, canon.auto_map(raw.headers))
    return raw, q


def close(produzido, esperado, chave):
    t = TOLERANCIAS[chave]
    assert t.aceita(produzido, esperado), (
        f"|{produzido} − {esperado}| = {abs(produzido - esperado):.3e} > atol {t.atol} + rtol {t.rtol}·|esperado|")


def ind(lista, id_):
    return next(i for i in lista if i.id == id_)


@pytest.fixture
def expected():
    return EXPECTED
