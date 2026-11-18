"""Fichas de indicador em React (Magic UI BlurFade + React Bits CountUp e SpotlightCard).

O build já compilado fica em ``frontend/build`` e é servido localmente pelo Streamlit:
quem só usa o sistema não precisa de Node. Para alterar o visual:
``cd componentes/fichas/frontend && npm install && npm run build``.

Se o build não existir, ``disponivel()`` retorna False e o app usa as fichas em HTML.
"""
from __future__ import annotations

import os
from pathlib import Path

_BUILD = Path(__file__).parent / "frontend" / "build"
_componente = None


def disponivel() -> bool:
    if os.environ.get("ANALISADOR_FICHAS_HTML") == "1":  # forçar as fichas HTML (diagnóstico)
        return False
    return (_BUILD / "index.html").is_file()


def fichas(lista: list[dict], colunas: int, key: str) -> None:
    global _componente
    if _componente is None:
        import streamlit.components.v1 as components  # só aqui: o resto do módulo não depende do Streamlit

        _componente = components.declare_component("fichas_dendrometria", path=str(_BUILD))
    _componente(fichas=lista, colunas=colunas, key=key, default=None)
