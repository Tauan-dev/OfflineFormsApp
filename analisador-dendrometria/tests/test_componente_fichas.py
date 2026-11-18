"""O componente React das fichas precisa estar compilado e com as licenças dos componentes de terceiros."""
import re
from pathlib import Path

from componentes import fichas

BASE = Path(fichas.__file__).parent


def test_build_presente_e_relativo():
    html = (BASE / "frontend" / "build" / "index.html").read_text(encoding="utf-8")
    assert fichas.disponivel()
    # caminhos relativos: o Streamlit serve o componente em um subcaminho próprio
    refs = re.findall(r'(?:src|href)="([^"]+)"', html)
    assert refs and all(r.startswith("./") for r in refs)
    for r in refs:
        assert (BASE / "frontend" / "build" / r[2:]).is_file()


def test_fontes_offline_no_build():
    assert len(list((BASE / "frontend" / "build" / "fonts").glob("*.woff2"))) == 4


def test_licencas_de_terceiros():
    assert "MIT" in (BASE / "licencas" / "LICENSE-MagicUI.md").read_text(encoding="utf-8")
    assert "Commons Clause" in (BASE / "licencas" / "LICENSE-ReactBits.md").read_text(encoding="utf-8")


def test_alternativa_html(monkeypatch):
    monkeypatch.setenv("ANALISADOR_FICHAS_HTML", "1")
    assert not fichas.disponivel()
