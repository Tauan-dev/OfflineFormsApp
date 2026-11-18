"""Exploração das observações em texto livre.

Identifica apenas MENÇÕES POTENCIAIS. Nenhuma menção é convertida em
ocorrência científica: toda menção sai com status "revisão necessária".
Negações próximas ("sem bromélias", "não possui ninho") são marcadas.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .canonicalization import fold

# categoria -> padrões (aplicados sobre texto minúsculo e sem acentos)
TERMOS: dict[str, tuple[str, ...]] = {
    "morte": (r"\bmort[oa]s?\b", r"\bmorreu\b", r"\bsem vida\b"),
    "dano": (r"\bdan[oi]\w*", r"\bdanific\w*"),
    "quebra": (r"\bquebr\w*", r"\bpartid[oa]\b"),
    "podridão": (r"\bpodr\w*",),
    "tombamento": (r"\btombad[oa]\b", r"\btomb\w*", r"\bcaid[oa]\b", r"\bderrubad[oa]\b"),
    "rebrotação": (r"\brebrot\w*", r"\bbrot[oa]\w*", r"\bbrotac\w*"),
    "bifurcação": (r"\bbifurc\w*",),
    "múltiplos fustes": (r"\b\d+\s*fustes\b", r"\bmultifuste\w*", r"\bvarios fustes\b"),
    "epífitas": (r"(?<!hemi)\bepifit\w*",),
    "hemiepífitas": (r"\bhemiepifit\w*", r"\bhemi-epifit\w*"),
    "bromélias": (r"\bbromel\w*",),
    "orquídeas": (r"\borquid\w*",),
    "ninhos": (r"\bninhos?\b",),
    "fauna": (r"\bninhos?\b", r"\bbeija-?flor\w*", r"\baves?\b", r"\bpassar\w*", r"\bformig\w*",
              r"\bcupi\w*", r"\babelh\w*", r"\bmarimbond\w*", r"\bvesp\w*", r"\bmacac\w*",
              r"\bsagu\w*", r"\banima\w*", r"\binset\w*", r"\blagart\w*", r"\bcobra\w*",
              r"\bpreguica\w*", r"\bmorceg\w*"),
    "serrapilheira": (r"\bser+apilh\w*",),
}
# Padrões de revisão adicionais (não são termos ecológicos)
LISTA_DIAMETROS = re.compile(r"\d+(?:[.,]\d+)?\s*(?:,|e|;)\s*\d+(?:[.,]\d+)?")
DUVIDA_ESPECIE = re.compile(r"\?|\bconfirmar\b|\bduvida\b|\bou seria\b")
NEGACOES = ("sem", "nao", "nenhum", "nenhuma", "nunca", "ausencia de", "ausente", "inexistente", "nem")
_COMPILED = {cat: [re.compile(p) for p in pats] for cat, pats in TERMOS.items()}


@dataclass
class Mencao:
    categoria: str
    termo: str
    negada: bool
    posicao: int


def _negated(text: str, start: int) -> bool:
    janela = text[max(0, start - 30):start]
    palavras = re.findall(r"[a-z]+(?: de)?", janela)[-3:]
    return any(p in NEGACOES or p.split(" ")[0] in NEGACOES for p in palavras)


def find_mentions(texto: str | None) -> list[Mencao]:
    if not texto or not str(texto).strip():
        return []
    t = fold(str(texto))
    out: list[Mencao] = []
    for cat, pats in _COMPILED.items():
        for p in pats:
            for m in p.finditer(t):
                out.append(Mencao(cat, m.group(0), _negated(t, m.start()), m.start()))
    # uma menção por (categoria, posição)
    uniq = {(m.categoria, m.posicao): m for m in out}
    return sorted(uniq.values(), key=lambda m: (m.posicao, m.categoria))


def has_diameter_list(texto: str | None) -> bool:
    """Lista de diâmetros numéricos (ex.: '6.9, 7.4' ou '3 fustes: 15.5, 9.0') — possível multifuste."""
    return bool(texto) and bool(LISTA_DIAMETROS.search(str(texto)))


# ------------------------------------------------------------ multifuste (regra de Finger, 1992)
# Extração ESTRITA: só aceita "<N> fustes|bifurcações|brotações [com DAP][:|-] d1, d2 ... e dN"
# quando a quantidade declarada N é igual à quantidade de valores listados. Números por
# extenso ("Dois fustes com Hc 11 e 8 metros"), listas sem quantidade declarada (moitas)
# ou listas com contagem divergente NÃO são extraídos: ficam para revisão humana.
_NUM = r"\d+(?:\.\d+)?"
FUSTES_DECLARADOS = re.compile(
    r"(?<![\d.])(?P<n>\d{1,2})\s*(?:fustes|bifurca[cç](?:[oõ]es|oes)|brota[cç](?:[oõ]es|oes))\s*"
    r"(?:com\s+dap)?\s*[:\-–]?\s*"
    rf"(?P<lista>{_NUM}(?:\s*(?:,|\be\b)\s*{_NUM})*)",
    re.IGNORECASE)


@dataclass
class Fustes:
    diametros_cm: list[float] | None  # None quando não extraível
    motivo: str  # explicação (extraído ou por que não)
    trecho: str = ""


def extract_stems(texto: str | None) -> Fustes:
    """Diâmetros de cada fuste declarados na observação, ou None (revisão humana)."""
    if not texto:
        return Fustes(None, "sem observação")
    achados = []
    for m in FUSTES_DECLARADOS.finditer(str(texto)):
        n = int(m.group("n"))
        vals = [float(v) for v in re.findall(_NUM, m.group("lista"))]
        achados.append((n, vals, m.group(0).strip()))
    if not achados:
        if has_diameter_list(texto):
            return Fustes(None, "lista de valores sem quantidade de fustes declarada (revisão humana)")
        return Fustes(None, "sem lista de fustes")
    validos = [(n, v, t) for n, v, t in achados if n >= 2 and len(v) == n and all(0 < x for x in v)]
    if not validos:
        n, v, t = achados[0]
        return Fustes(None, f"quantidade declarada ({n}) difere dos valores listados ({len(v)}) — revisão humana", t)
    if len({tuple(v) for _, v, _ in validos}) > 1:
        return Fustes(None, "mais de uma lista de fustes divergente na observação — revisão humana", validos[0][2])
    n, v, t = validos[-1]
    return Fustes(v, f"{n} fustes extraídos (quantidade declarada = valores listados)", t)


def has_species_doubt(texto: str | None) -> bool:
    return bool(texto) and bool(DUVIDA_ESPECIE.search(fold(str(texto))))


def positive_categories(mencoes: list[Mencao]) -> set[str]:
    return {m.categoria for m in mencoes if not m.negada}


def mentions_table(records) -> "pd.DataFrame":
    """Uma linha por menção encontrada, com texto original preservado."""
    import pandas as pd

    rows = []
    for _, r in records[records["observacao"].notna()].iterrows():
        ms = find_mentions(r["observacao"])
        extra = []
        if has_diameter_list(r["observacao"]):
            extra.append(("lista de diâmetros (possível multifuste)", False))
        if has_species_doubt(r["observacao"]):
            extra.append(("dúvida de identificação", False))
        items = [(m.categoria, m.negada, m.termo) for m in ms] + [(c, n, "") for c, n in extra]
        for cat, neg, termo in items:
            rows.append({
                "parcela": r["parcela"] if r["parcela"] is not None else r["parcela_orig"],
                "árvore": r["arvore"] if r["arvore"] is not None else r["arvore_orig"],
                "espécie": r["especie"], "categoria": cat, "termo encontrado": termo,
                "negação": "sim" if neg else "não", "texto original": r["observacao"],
                "status": "revisão necessária", "linha": r["_linha"],
            })
    cols = ["parcela", "árvore", "espécie", "categoria", "termo encontrado", "negação", "texto original",
            "status", "linha"]
    return pd.DataFrame(rows, columns=cols)


def mentions_summary(mentions) -> "pd.DataFrame":
    import pandas as pd

    if mentions is None or mentions.empty:
        return pd.DataFrame(columns=["categoria", "menções positivas", "menções negadas", "registros"])
    g = mentions.groupby("categoria").agg(
        **{"menções positivas": ("negação", lambda s: int((s == "não").sum())),
           "menções negadas": ("negação", lambda s: int((s == "sim").sum())),
           "registros": ("linha", "nunique")}).reset_index()
    return g.sort_values("registros", ascending=False).reset_index(drop=True)
