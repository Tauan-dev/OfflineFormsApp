"""Analisador de Dendrometria — interface local (Streamlit).

A interface NÃO calcula indicadores: apenas exibe o que a camada
``analytics`` produz. Todo processamento é local; nada é enviado à internet.

Execução:  streamlit run app.py
"""
from __future__ import annotations

import datetime as dt
import html
import os
import signal
import threading

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from analytics import Filters, Metodologia, run_analysis
from componentes import fichas as fichas_react
from analytics.results import ESARM_REFERENCIAS, esarm_aplicavel, metodologia_arboreto_esarm
from analytics import canonicalization as canon
from analytics import dendrometry as dd
from analytics import export, ingestion, quality
from analytics import observations as obs
from analytics.canonicalization import CANONICAL_COLUMNS, LABEL, natural_key
from analytics.inventory import PENDENTES
from analytics.quality import DAP_LIMITE_LEGADO_CM, ESTADOS_REGISTRO
from analytics.results import (
    ANALISADOR_VERSAO,
    ESTADOS_SEM_VALOR,
    TOLERANCIAS,
    VERSAO_METODOLOGICA,
    Indicator,
    indicadores_para_tabela,
)

# ------------------------------------------------------------ paleta (identidade: mata + fita dendrométrica)
MARCA = "#14513B"       # verde-floresta: títulos, abas, ações
AZUL = "#2F5D7C"        # séries de gráfico
AZUL_CLARO = "#7FA3BD"
VERDE = "#1E7A4F"
CINZA = "#53625A"
AMARELO = "#C58B1A"
VERMELHO = "#B3261E"
STATUS_COR = {"VÁLIDO": VERDE, "VÁLIDO COM RESSALVA": AMARELO, "INCONCLUSIVO": "#7A8791", "INVÁLIDO": VERMELHO}

from pathlib import Path as _Path
try:
    from PIL import Image as _Image
    _ICONE = _Image.open(_Path(__file__).parent / "assets" / "logo_256.png")
except Exception:  # sem logo ou sem Pillow: emoji
    _ICONE = "🌳"
st.set_page_config(page_title="Analisador de Dendrometria", page_icon=_ICONE, layout="wide",
                   initial_sidebar_state="expanded")

_CSS = """
<style>
  @font-face {font-family:"Atkinson Next"; font-weight:400; font-display:swap;
              src:url(/app/static/atkinson-hyperlegible-next-latin-400-normal.woff2) format("woff2");}
  @font-face {font-family:"Atkinson Next"; font-weight:600; font-display:swap;
              src:url(/app/static/atkinson-hyperlegible-next-latin-600-normal.woff2) format("woff2");}
  @font-face {font-family:"Atkinson Next"; font-weight:700; font-display:swap;
              src:url(/app/static/atkinson-hyperlegible-next-latin-700-normal.woff2) format("woff2");}
  @font-face {font-family:"Source Serif 4"; font-weight:200 900; font-display:swap;
              src:url(/app/static/source-serif-4-latin-wght-normal.woff2) format("woff2");}
  :root {--ink:#1B2B24; --marca:#14513B; --sub:#53625A; --rule:#D5DDD4; --ok:#1E7A4F; --ok-t:#1B6A43;
         --warn:#C58B1A; --warn-t:#8A5A00; --err:#B3261E; --blk:#6B7780; --blk-t:#46535B;
         --serif:"Source Serif 4", Georgia, "Times New Roman", serif;
         --sans:"Atkinson Next", "Segoe UI", system-ui, sans-serif;}
  html, body, .stApp {font-family:var(--sans) !important; color:var(--ink);}
  .block-container {padding-top:1rem; padding-bottom:2.5rem; max-width:1480px;}
  header[data-testid="stHeader"] {height:0;}
  :focus-visible {outline:2px solid var(--warn) !important; outline-offset:2px;}

  /* cabeçalho */
  .topo {display:flex; align-items:center; gap:14px; padding:2px 0 12px; border-bottom:1px solid var(--rule);
         margin-bottom:6px;}
  .topo img {width:44px; height:44px; display:block;}
  .topo .nome {font-family:var(--serif); font-size:1.6rem; font-weight:600; color:var(--marca); line-height:1.1;}
  .topo .sub {font-size:.8rem; color:var(--sub); margin-top:2px;}
  .topo .arq {margin-left:auto; text-align:right; font-size:.84rem; color:var(--sub); line-height:1.35;}
  .topo .arq b {color:var(--ink); font-weight:700;}

  /* títulos */
  div[data-testid="stMarkdownContainer"] h4 {font-family:var(--serif); font-weight:600; color:var(--marca);
         font-size:1.2rem; padding:.35rem 0 .15rem;}
  section[data-testid="stSidebar"] h3 {font-family:var(--serif); font-weight:600; color:var(--marca);
         font-size:1.1rem; padding:.2rem 0;}

  /* abas */
  div[data-testid="stTabs"] [role="tablist"] {gap:0; flex-wrap:wrap; overflow:visible;}
  div[data-testid="stTabs"] [data-baseweb="tab-highlight"], div[data-testid="stTabs"] [data-baseweb="tab-border"] {display:none;}
  div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {box-shadow:inset 0 -3px 0 var(--marca);}
  div[data-testid="stTabs"] [role="tablist"] {border-bottom:1px solid var(--rule);}
  /* sub-abas (dentro de uma aba): menores, em pílulas */
  div[data-testid="stTabs"] div[data-testid="stTabs"] [role="tablist"] {border-bottom:0; gap:6px; margin-bottom:4px;}
  div[data-testid="stTabs"] div[data-testid="stTabs"] button[role="tab"] {border:1px solid var(--rule); border-radius:999px;
      padding:4px 14px; background:#fff;}
  div[data-testid="stTabs"] div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {background:var(--marca);
      border-color:var(--marca); box-shadow:none;}
  div[data-testid="stTabs"] div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] p {color:#fff;}
  div[data-testid="stMarkdownContainer"] h5 {font-weight:700; color:var(--ink); font-size:1rem; padding:.6rem 0 .1rem;}
  div[data-testid="stTabs"] button[role="tab"] {padding:8px 13px;}
  div[data-testid="stTabs"] button[role="tab"] p {font-size:.9rem; font-weight:600; color:var(--sub);}
  div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] p {color:var(--marca);}

  /* barra lateral */
  section[data-testid="stSidebar"] {background:#F0F4EF; border-right:1px solid var(--rule);}
  section[data-testid="stSidebar"] details {background:#fff; border-radius:2px;}
  details summary {font-weight:600;}

  /* ficha de indicador: valor + quanto dos dados sustenta o valor */
  .ficha {position:relative; overflow:hidden; min-width:0; background:#fff; border:1px solid var(--rule);
          border-top:3px solid var(--blk); border-radius:2px; padding:10px 13px 10px; height:100%;
          transition:transform .25s ease, box-shadow .25s ease, border-color .25s ease;
          animation:entrar .55s cubic-bezier(.2,.7,.2,1) both; animation-delay:calc(var(--o, 0) * 70ms);}
  .ficha::before {content:""; position:absolute; inset:0; pointer-events:none; opacity:0; transition:opacity .3s;
          background:radial-gradient(260px circle at var(--mx, 50%) var(--my, 0%), rgba(30,122,79,.10), transparent 70%);}
  .ficha:hover, .ficha:focus-within {transform:translateY(-2px); box-shadow:0 6px 18px rgba(20,81,59,.10);}
  .ficha:hover::before, .ficha:focus-within::before {opacity:1;}
  .ficha.ok {border-top-color:var(--ok);} .ficha.warn {border-top-color:var(--warn);}
  .ficha.warn::before {background:radial-gradient(260px circle at var(--mx, 50%) var(--my, 0%), rgba(197,139,26,.13), transparent 70%);}
  .ficha.err {border-top-color:var(--err);}
  .ficha.blk {background:repeating-linear-gradient(135deg,#F7F9F7 0 7px,#ECF0ED 7px 14px);}
  .ficha > * {position:relative;}
  .ficha .t {font-size:.85rem; color:var(--sub); font-weight:600; line-height:1.25; min-height:2.5em;}
  .ficha .v {font-family:var(--serif); font-variant-numeric:lining-nums tabular-nums; font-size:1.9rem;
             font-weight:600; color:var(--ink); line-height:1.15; margin-top:2px;}
  .ficha .v small {font-family:var(--sans); font-size:.85rem; color:var(--sub); font-weight:400; margin-left:4px;}
  .ficha .v.sem {font-family:var(--sans); font-size:.98rem; font-weight:700; color:var(--blk-t); line-height:1.3;
                 padding:4px 0 2px;}
  .sr {position:absolute !important; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap;}
  .ficha .bar {height:4px; background:#E3E9E3; border-radius:2px; margin:9px 0 6px; overflow:hidden;}
  .ficha .bar.vazia {background:transparent;}
  .ficha .bar i {display:block; height:100%; width:var(--w); background:var(--ok); transform-origin:left;
                 animation:encher .9s cubic-bezier(.2,.7,.2,1) both; animation-delay:calc(var(--o, 0) * 70ms + .15s);}
  .ficha.warn .bar i {background:var(--warn);} .ficha.err .bar i {background:var(--err);}
  .ficha .d {font-size:.8rem; color:var(--sub); line-height:1.35; min-height:5.4em;}
  .ficha .ress {margin:8px 0 0; padding:7px 9px; background:#FBF3D9; border-left:3px solid var(--warn);
                font-size:.8rem; line-height:1.4; color:#4A3700; border-radius:0 2px 2px 0;}
  .ficha .ress b {color:var(--warn-t);}
  .ficha .s {margin-top:8px; font-size:.8rem; font-weight:700; color:var(--blk-t);}
  .ficha.ok .s {color:var(--ok-t);} .ficha.warn .s {color:var(--warn-t);} .ficha.err .s {color:var(--err);}
  .ficha .s em {font-style:normal; font-weight:600; color:var(--marca); border:1px solid var(--marca);
                border-radius:2px; padding:0 5px; margin-left:8px; font-size:.74rem;}
  .ficha details {margin-top:6px; font-size:.78rem; color:var(--sub);}
  .ficha details summary {cursor:pointer; font-weight:600; color:var(--marca); padding:4px 0; min-height:24px;
                          list-style-position:inside;}
  .ficha details[open] summary {margin-bottom:2px;}
  .ficha details .form {font-family:var(--serif); color:var(--ink); margin:2px 0 4px;}
  .ficha details ul {margin:0; padding-left:1.1em;} .ficha details li {margin:2px 0; line-height:1.35;}
  @keyframes entrar {from {opacity:0; transform:translateY(10px); filter:blur(5px);} to {opacity:1; transform:none; filter:none;}}
  @keyframes encher {from {transform:scaleX(0);} to {transform:scaleX(1);}}
  @media (prefers-reduced-motion: reduce) {
    .ficha, .ficha .bar i {animation:none !important; transition:none !important;}
    .ficha:hover, .ficha:focus-within {transform:none;}
  }
  /* o componente invisível que liga as animações não ocupa espaço */
  div[data-testid="stElementContainer"]:has(> iframe[height="0"]),
  div.element-container:has(> iframe[height="0"]) {display:none;}

  /* situação dos indicadores */
  .sit {display:flex; height:14px; gap:2px; margin:8px 0 8px;}
  .sit i {display:block; height:100%; border-radius:1px;}
  .sit i.h {background:repeating-linear-gradient(135deg,#8F9AA1 0 4px,#C5CCD0 4px 8px);}
  .sit-leg {margin-bottom:14px; display:flex; gap:22px; flex-wrap:wrap; font-size:.86rem; color:var(--sub);}
  .sit-leg b {color:var(--ink); font-weight:700;}
  .sit-leg .dot {display:inline-block; width:10px; height:10px; border-radius:1px; margin-right:6px;}

  /* envio de arquivo em português */
  [data-testid="stFileUploaderDropzoneInstructions"] span {font-size:0 !important;}
  [data-testid="stFileUploaderDropzoneInstructions"] span::before {content:"Arraste a planilha aqui"; font-size:1rem;}
  [data-testid="stFileUploaderDropzoneInstructions"] small {font-size:0 !important;}
  [data-testid="stFileUploaderDropzoneInstructions"] small::before {content:"Até 200 MB · XLSX, XLSM, CSV"; font-size:.8rem;}
  [data-testid="stFileUploaderDropzone"] button {font-size:0 !important;}
  [data-testid="stFileUploaderDropzone"] button::after {content:"Procurar arquivo"; font-size:.9rem;}
  .ind-cab {padding:22px 0 4px;} .ind-esp {font-family:var(--serif); font-size:1.45rem; font-weight:600; color:var(--marca);}
  .ind-meta {color:var(--sub); font-size:.92rem; margin-top:2px;} .ind-meta b {color:var(--ink);}
  .obs-campo {margin:4px 0 6px; padding:10px 14px; border-left:3px solid var(--marca); background:#F7FAF6;
              font-size:.98rem; line-height:1.55; color:var(--ink); max-width:72ch;}
  .ocorr {list-style:none; padding:0; margin:4px 0;} .ocorr li {border-left:2px solid var(--rule); padding:4px 0 4px 12px;
          margin:0 0 10px; font-size:.92rem; line-height:1.5; max-width:72ch;} .ocorr li span {color:var(--sub); font-size:.84rem;}
  .filtro {background:#FBF3D9; border:1px solid #E8D28A; color:#5E4500; padding:7px 11px; border-radius:2px;
           font-size:.86rem; margin-bottom:10px;}
  @media (max-width: 1000px) {
    .topo .arq {display:none;}
    .ficha .v {font-size:1.45rem;} .ficha .v small {display:block; margin-left:0;}
    .ficha .t, .ficha .d, .ficha .s {font-size:.74rem;}
  }
  .nota {color:var(--sub); font-size:.84rem;}
  .proximo {border-left:3px solid var(--marca); background:#F0F4EF; padding:8px 12px; margin:6px 0;
            font-size:.92rem; border-radius:0 2px 2px 0;}
</style>
"""
st.markdown(_CSS, unsafe_allow_html=True)


_ANIMACAO_JS = """
<script>
(function () {
  const P = window.parent, D = P.document;
  D.documentElement.lang = "pt-BR";
  if (P.__dendroAnim) return;            // instala uma única vez por página
  P.__dendroAnim = true;
  const vistos = new Set();
  const calmo = P.matchMedia("(prefers-reduced-motion: reduce)");
  const fmt = (v, c) => new Intl.NumberFormat("pt-BR", {minimumFractionDigits: c, maximumFractionDigits: c}).format(v);
  function contar(el) {
    const alvo = parseFloat(el.dataset.alvo), casas = parseInt(el.dataset.casas || "0", 10);
    const ficha = el.closest(".ficha"), chave = ficha ? ficha.dataset.k : null;
    if (!isFinite(alvo) || calmo.matches || (chave && vistos.has(chave))) return;
    if (chave) vistos.add(chave);
    const final = el.textContent, t0 = P.performance.now(), dur = 900;
    function passo(t) {
      const p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(2, -10 * p);
      el.textContent = p < 1 ? fmt(alvo * e, casas) : final;
      if (p < 1) P.requestAnimationFrame(passo);
    }
    P.requestAnimationFrame(passo);
  }
  const io = new P.IntersectionObserver((es) => es.forEach((e) => {
    if (e.isIntersecting) { io.unobserve(e.target); contar(e.target); }
  }), {threshold: 0.4});
  function varrer() {
    D.querySelectorAll(".ficha .num[data-alvo]:not([data-obs])").forEach((el) => { el.dataset.obs = "1"; io.observe(el); });
    // nome legível para leitores de tela no quadro do componente React
    D.querySelectorAll("iframe[title*='fichas_dendrometria']").forEach((f) => { f.title = "Fichas de indicadores"; });
  }
  new P.MutationObserver(varrer).observe(D.body, {childList: true, subtree: true});
  varrer();
  D.addEventListener("pointermove", (ev) => {
    const f = ev.target.closest && ev.target.closest(".ficha");
    if (!f) return;
    const r = f.getBoundingClientRect();
    f.style.setProperty("--mx", (ev.clientX - r.left) + "px");
    f.style.setProperty("--my", (ev.clientY - r.top) + "px");
  }, {passive: true});
})();
</script>
"""
components.html(_ANIMACAO_JS, height=0)


# ------------------------------------------------------------ formatação (apenas exibição)
DEC = {"cm": 2, "m": 2, "m²": 4, "m³": 3, "%": 1, "m²/ha": 3}


def fmt(v, unidade: str = "") -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    if isinstance(v, (int,)) and not isinstance(v, bool):
        return f"{v:,}".replace(",", ".")
    if isinstance(v, float):
        d = DEC.get(unidade, 2)
        s = f"{v:,.{d}f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    return str(v)


_ESTADO_UI = {"VÁLIDO": ("ok", "✓ cálculo válido"), "VÁLIDO COM RESSALVA": ("warn", "! cálculo com ressalva"),
              "BLOQUEADO POR QUALIDADE": ("err", "✕ bloqueado por qualidade"),
              "INDISPONÍVEL": ("blk", "– indisponível"),
              "BLOQUEADO POR METODOLOGIA": ("blk", "⊘ bloqueado por metodologia"),
              "BLOQUEADO POR QUALIDADE OU METODOLOGIA": ("blk", "⊘ bloqueado por qualidade ou metodologia")}


SEM_COBERTURA = {"linhas_importadas", "registros_validos", "registros_ressalva", "registros_invalidos",
                 "registros_inconclusivos", "dap_ausentes", "dap_invalidos", "duplicidades", "obs_revisao"}


# Nota que melhor resume a ressalva de cada indicador (prefixo da observação); padrão: a primeira.
RESSALVA_PRIORIDADE = {"g_ha": "Sensibilidade", "g_total_multifuste": "27 indivíduos"}
# Quando a observação descreve o cálculo mas não diz qual é a ressalva.
RESSALVA_TEXTO = {"area_amostrada": "Depende da área adotada para cada parcela (barra lateral → Decisões metodológicas)."}
_IDS_VISTOS: dict[str, int] = {}


def _ressalva(i: Indicator) -> tuple[str, list[str]]:
    obs_ = [o for o in i.observacoes if o]
    if i.id in RESSALVA_TEXTO and i.status == "VÁLIDO COM RESSALVA":
        return RESSALVA_TEXTO[i.id], obs_
    if not obs_:
        return "", []
    pref = RESSALVA_PRIORIDADE.get(i.id)
    k = next((n for n, o in enumerate(obs_) if pref and o.startswith(pref)), 0)
    if pref and not obs_[k].startswith(pref):  # prefixo não encontrado (ex.: número diferente)
        k = next((n for n, o in enumerate(obs_) if o.split()[0:1] == pref.split()[0:1]), 0)
    principal, demais = obs_[k], obs_[:k] + obs_[k + 1:]
    if len(principal) > 170:  # nota longa: a primeira frase vai no cartão, o restante nas notas
        import re as _re
        partes = _re.split(r"(?<=[a-z²%)])\. (?=[A-Z0-9])", principal, maxsplit=1)
        if len(partes) == 2:
            principal, demais = partes[0] + ".", [partes[1]] + demais
    return principal, demais


def _casas(v, unidade: str) -> int:
    return 0 if isinstance(v, int) and not isinstance(v, bool) else DEC.get(unidade, 2)


def card(i: Indicator, titulo: str | None = None, ordem: int = 0) -> str:
    cls, rotulo = _ESTADO_UI.get(i.status, ("blk", i.status.lower()))
    sem_valor = i.status in ESTADOS_SEM_VALOR
    nome = titulo or i.nome
    texto_valor = "sem valor calculado" if sem_valor else f"{fmt(i.valor, i.unidade)} {i.unidade}".strip()
    if sem_valor:
        val = "<div class='v sem'>Sem valor calculado</div>"
    else:
        num = fmt(i.valor, i.unidade)
        attrs = ""
        if isinstance(i.valor, (int, float)) and not isinstance(i.valor, bool) and pd.notna(i.valor):
            attrs = f" data-alvo='{float(i.valor)!r}' data-casas='{_casas(i.valor, i.unidade)}'"
        val = (f"<div class='v'><span class='num' aria-hidden='true'{attrs}>{num}</span>"
               f"<small aria-hidden='true'>{html.escape(i.unidade)}</small>"
               f"<span class='sr'>{html.escape(texto_valor)}</span></div>")
    barra = ""
    if i.id in SEM_COBERTURA:  # contagem de ocorrências: cobertura não é a leitura adequada
        barra = "<div class='bar vazia'></div>"
    elif not sem_valor and i.cobertura is not None:
        pct = max(0.0, min(100.0, i.cobertura * 100))
        barra = (f"<div class='bar' role='img' aria-label='cobertura {fmt(pct, '%')}%'>"
                 f"<i style='--w:{pct:.1f}%'></i></div>")
    elif not sem_valor:
        barra = "<div class='bar vazia'></div>"
    cov = "" if (i.cobertura is None or sem_valor or i.id in SEM_COBERTURA) else f" · cobertura {fmt(i.cobertura * 100, '%')}%"
    den = html.escape(i.denominador) + cov
    principal, demais = _ressalva(i)
    aviso = ""
    if sem_valor and principal:  # bloqueado: o motivo ocupa o lugar do denominador
        den = html.escape(principal)
        principal = ""
    elif i.status == "VÁLIDO COM RESSALVA" and principal:
        aviso = f"<p class='ress'><b>Ressalva:</b> {html.escape(principal)}</p>"
        principal = ""
    notas = ([principal] if principal else []) + demais
    itens = "".join(f"<li>{html.escape(n)}</li>" for n in notas)
    detalhe = (f"<details><summary>Fórmula e notas</summary><p class='form'>{html.escape(i.formula)}</p>"
               f"{'<ul>' + itens + '</ul>' if itens else ''}</details>") if (i.formula or itens) else ""
    filt = "<em>filtrado</em>" if i.filtrado else ""
    chave = html.escape(f"{i.id}|{i.valor!r}|{i.status}")
    return (f"<section class='ficha {cls}' style='--o:{ordem}' data-k='{chave}' "
            f"aria-label='{html.escape(nome)}: {html.escape(texto_valor)}, {html.escape(rotulo.split(' ', 1)[1])}'>"
            f"<div class='t'>{html.escape(nome)}</div>{val}{barra}<div class='d'>{den}</div>{aviso}"
            f"<div class='s'>{rotulo}{filt}</div>{detalhe}</section>")


def ficha_dados(i: Indicator, titulo: str | None = None) -> dict:
    """Mesmo conteúdo da ficha HTML, como dados para o componente React (nada é recalculado lá)."""
    cls, rotulo = _ESTADO_UI.get(i.status, ("blk", i.status.lower()))
    sem_valor = i.status in ESTADOS_SEM_VALOR
    numerico = isinstance(i.valor, (int, float)) and not isinstance(i.valor, bool) and pd.notna(i.valor)
    cob = None
    if not sem_valor and i.cobertura is not None and i.id not in SEM_COBERTURA:
        cob = round(max(0.0, min(100.0, i.cobertura * 100)), 2)
    cov = "" if cob is None else f" · cobertura {fmt(i.cobertura * 100, '%')}%"
    den = i.denominador + cov
    principal, demais = _ressalva(i)
    ressalva = ""
    if sem_valor and principal:
        den, principal = principal, ""
    elif i.status == "VÁLIDO COM RESSALVA" and principal:
        ressalva, principal = principal, ""
    return {
        "chave": f"{i.id}", "titulo": titulo or i.nome,
        "valor_txt": "" if sem_valor else fmt(i.valor, i.unidade),
        "alvo": float(i.valor) if (numerico and not sem_valor) else None,
        "casas": _casas(i.valor, i.unidade), "unidade": i.unidade,
        "classe": cls, "rotulo": rotulo, "estado": rotulo.split(" ", 1)[1], "sem_valor": sem_valor,
        "denominador": den, "cobertura": cob, "barra": not sem_valor,
        "ressalva": ressalva, "formula": i.formula or "",
        "notas": ([principal] if principal else []) + demais, "filtrado": bool(i.filtrado),
    }


def cards(inds: list[Indicator], cols: int = 4, titulos: dict | None = None) -> None:
    titulos = titulos or {}
    if not inds:
        return
    if fichas_react.disponivel():
        fichas_react.fichas([ficha_dados(i, titulos.get(i.id)) for i in inds], cols,
                            key="fichas-" + "-".join(i.id for i in inds))
        return
    for k in range(0, len(inds), cols):  # alternativa sem o componente React
        row = st.columns(cols)
        for n, (c, i) in enumerate(zip(row, inds[k:k + cols])):
            c.markdown(card(i, titulos.get(i.id), ordem=n + (k // cols)), unsafe_allow_html=True)
        st.write("")


def get(inds: list[Indicator], id_: str) -> Indicator:
    return next(i for i in inds if i.id == id_)


def chart(fig: go.Figure, fonte: str, n: str, height: int = 380) -> None:
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=56, b=10), plot_bgcolor="#fff", paper_bgcolor="#fff",
                      font=dict(family="Atkinson Next, Segoe UI, Arial", size=12.5, color="#2B3A33"),
                      title=dict(font=dict(family="Source Serif 4, Georgia, serif", size=16, color=MARCA),
                                 x=0, xanchor="left"),
                      colorway=[AZUL, VERDE, AMARELO, AZUL_CLARO, "#7A8791"],
                      hoverlabel=dict(bgcolor="#fff", font_size=12.5, bordercolor="#D5DDD4"))
    fig.update_xaxes(showgrid=False, linecolor="#C3CDC3", ticks="outside", tickcolor="#C3CDC3")
    fig.update_yaxes(gridcolor="#E9EEE9", zeroline=False)
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
    st.caption(f"Fonte: {fonte} · {n}")


def table(df: pd.DataFrame, height: int | None = None, **kw) -> None:
    if df is None or df.empty:
        st.info("Nenhum registro para exibir.")
        return
    df = export._stringify_objects(df)
    for c in df.columns:  # colunas mistas (ex.: número ou status) viram texto para exibição
        if df[c].dtype == object:
            if len({type(v) for v in df[c] if v is not None and v == v}) > 1:
                df[c] = df[c].map(lambda v: "" if v is None or v != v else (fmt(v) if isinstance(v, float) else str(v)))
            elif df[c].isna().any():
                df[c] = df[c].where(df[c].notna(), "")
    st.dataframe(df, use_container_width=True, hide_index=True,
                 height=height or min(38 + 35 * len(df), 520), **kw)


def filtro_banner(res) -> None:
    if res.filtrado:
        st.markdown(f"<div class='filtro'><b>Indicadores filtrados:</b> {res.n_registros} registros após os "
                    f"filtros da barra lateral. Limpe os filtros para voltar ao arquivo completo.</div>", unsafe_allow_html=True)


# ------------------------------------------------------------ processamento (cache)
@st.cache_data(show_spinner=False)
def c_sheets(data: bytes) -> list[str]:
    return ingestion.list_sheets(data)


@st.cache_data(show_spinner="Lendo arquivo…")
def c_raw(data: bytes, name: str, sheet: str | None):
    return ingestion.read_file(data, name, sheet)


@st.cache_data(show_spinner="Validando registros…")
def c_quality(data: bytes, name: str, sheet: str | None, mapping: tuple):
    raw = c_raw(data, name, sheet)
    cmap = canon.manual_map(raw.headers, dict(mapping))
    return quality.build_records(raw, cmap)


def _shutdown() -> None:
    threading.Timer(0.8, lambda: os.kill(os.getpid(), signal.SIGTERM)).start()


def _logo_b64() -> str:
    try:
        import base64
        return base64.b64encode((_Path(__file__).parent / "assets" / "logo_256.png").read_bytes()).decode()
    except Exception:
        return ""


def cabecalho(raw, res) -> str:
    logo = _logo_b64()
    img = f"<img alt='' src='data:image/png;base64,{logo}'/>" if logo else ""
    arq = "<span>Nenhuma planilha carregada</span>"
    if raw is not None:
        m = raw.meta
        arq = (f"<b>{html.escape(m.nome_arquivo)}</b><br/>aba {html.escape(m.planilha or '—')} · "
               f"{fmt(m.registros_interpretados)} registros")
        if res is not None and res.filtrado:
            arq += f" · <b>filtrado: {fmt(res.n_registros)}</b>"
    return (f"<div class='topo'>{img}<div><div class='nome'>Analisador de Dendrometria</div>"
            f"<div class='sub'>Processamento local · versão {ANALISADOR_VERSAO} · metodologia {VERSAO_METODOLOGICA}</div></div>"
            f"<div class='arq'>{arq}</div></div>")


def situacao_indicadores(inds: list[Indicator]) -> str:
    n_ok = sum(i.status == "VÁLIDO" for i in inds)
    n_res = sum(i.status == "VÁLIDO COM RESSALVA" for i in inds)
    n_blk = sum(i.status in ESTADOS_SEM_VALOR for i in inds)
    tot = max(1, n_ok + n_res + n_blk)
    seg = [("", VERDE, n_ok, "válidos"), ("", AMARELO, n_res, "válidos com ressalva"),
           ("h", "", n_blk, "sem valor (bloqueados ou indisponíveis)")]
    barra = "".join(f"<i class='{c}' style='width:{n / tot * 100:.2f}%;background:{cor}'></i>" if cor else
                    f"<i class='{c}' style='width:{n / tot * 100:.2f}%'></i>" for c, cor, n, _ in seg if n)
    leg = "".join(f"<span><span class='dot' style='background:{cor or '#8F9AA1'}'></span><b>{n}</b> {rot}</span>"
                  for _, cor, n, rot in seg)
    return f"<div class='sit' role='img' aria-label='situação dos indicadores'>{barra}</div><div class='sit-leg'>{leg}</div>"


# ------------------------------------------------------------ ficha do indivíduo (apenas exibição)
_MEDIDA_UI = {"MEDIDO": ("ok", "✓ medido"), "EXTREMO": ("warn", "! valor extremo"),
              "AUSENTE": ("blk", "– não medido"), "NÃO COLETADO": ("blk", "– não coletado"),
              "NÃO APLICÁVEL": ("blk", "⊘ não aplicável"), "INVÁLIDO": ("err", "✕ inválido")}


def _ficha_livre(chave: str, titulo: str, valor, unidade: str, classe: str, rotulo: str, base: str,
                 formula: str = "", ressalva: str = "", notas: list[str] | None = None) -> dict:
    tem = valor is not None and not (isinstance(valor, float) and pd.isna(valor))
    return {"chave": chave, "titulo": titulo, "valor_txt": fmt(float(valor), unidade) if tem else "",
            "alvo": float(valor) if tem else None, "casas": DEC.get(unidade, 2), "unidade": unidade,
            "classe": classe if tem or classe != "ok" else "blk", "rotulo": rotulo,
            "estado": rotulo.split(" ", 1)[1], "sem_valor": not tem, "denominador": base, "cobertura": None,
            "barra": False, "ressalva": ressalva, "formula": formula, "notas": [n for n in (notas or []) if n],
            "filtrado": False}


def fichas_individuo(reg: pd.Series, linha_ind: pd.Series | None, copa: pd.Series | None) -> list[dict]:
    """Cartões de um registro (a medição mais recente do indivíduo). Valores vêm de analytics."""
    data = reg.get("data_medicao")
    base = f"medição de {data.strftime('%d/%m/%Y') if hasattr(data, 'strftime') else '—'} · linha {int(reg['_linha'])} da planilha"
    out = []
    medidas = [("dap_cm", "DAP", "cm", "diâmetro a 1,30 m do solo"),
               ("ht_m", "Altura total (HT)", "m", "do solo até o ápice"),
               ("hesg_m", "Altura do esgalhamento (HESG)", "m", "do solo até a inserção do primeiro galho vivo"),
               ("hesgcopa_m", "Altura da formação da copa (HESGCOPA)", "m", "do solo até o início da copa"),
               ("hc_m", "Altura comercial (HC)", "m", "do solo até a porção superior utilizável do tronco")]
    for col, nome, un, defin in medidas:
        st_ = reg.get(f"{col}_status") or "AUSENTE"
        cls, rot = _MEDIDA_UI.get(st_, ("blk", "– " + str(st_).lower()))
        motivo = reg.get(f"{col}_motivo") or ""
        orig = reg.get(f"{col}_orig")
        ress = ""
        if col == "dap_cm" and linha_ind is not None and st_ == "MEDIDO" and not bool(linha_ind.get("DAP elegível", True)):
            cls, rot, ress = "warn", "! fora dos cálculos", str(linha_ind.get("motivo exclusão DAP") or "")
        elif motivo and st_ != "MEDIDO":
            ress = str(motivo)
        notas = [f"Definição: {defin}.",
                 f"Valor na planilha original: {orig!s}" if orig is not None and str(orig) != "nan" else "Célula vazia na planilha original.",
                 f"Pista de recuperação: {reg.get(f'{col}_pista')}" if reg.get(f"{col}_pista") else ""]
        valor = reg.get(col) if st_ in ("MEDIDO", "EXTREMO") else None
        f = _ficha_livre(f"ind-{col}", nome, valor, un, cls, rot, base, "", "", notas)
        if f["sem_valor"]:
            f["denominador"] = ress or base
        elif ress:
            f["ressalva"] = ress
        out.append(f)
    if linha_ind is not None:
        g = linha_ind.get("g (m²)")
        out.append(_ficha_livre("ind-g", "Área seccional (g)", g, "m²", "ok", "✓ calculado" if pd.notna(g) else "– requer DAP elegível",
                                base, "g = π · DAP² / 40.000 (DAP em cm)",
                                notas=["Usa somente DAP elegível pela política única de elegibilidade."]))
        vc = linha_ind.get("volume cilíndrico (m³)")
        out.append(_ficha_livre("ind-vc", "Volume cilíndrico", vc, "m³", "warn" if pd.notna(vc) else "blk",
                                "! calculado com ressalva" if pd.notna(vc) else "– requer DAP e HT elegíveis", base,
                                "V = g × HT", ressalva="Volume de cilindro, sem fator de forma." if pd.notna(vc) else ""))
        vs = linha_ind.get("volume Spurr (m³)")
        out.append(_ficha_livre("ind-vs", "Volume comercial (Spurr)", vs, "m³", "warn" if pd.notna(vs) else "blk",
                                "! calculado com ressalva" if pd.notna(vs) else "– requer DAP e HC elegíveis", base,
                                "Vc = 0,106531813 + 5,3372·10⁻⁵ · DAP² · HC (Jorge, 1982)",
                                ressalva="Coeficientes regionais (Mata Atlântica norte ES / sul BA)." if pd.notna(vs) else ""))
    if copa is not None:
        ok = bool(copa.get("copa_elegivel"))
        out.append(_ficha_livre("ind-copa", "Comprimento de copa", copa.get("comprimento_copa_m") if ok else None, "m",
                                "ok", "✓ calculado" if ok else "– não calculado", base if ok else str(copa.get("copa_motivo_exclusao") or base),
                                "comprimento = HT − HESGCOPA",
                                notas=[f"Proporção de copa: {fmt(copa.get('proporcao_copa'), '%')}% da altura total." if ok else ""]))
    return out


# ------------------------------------------------------------ cabeçalho
_topo = st.empty()  # preenchido após a leitura do arquivo

# ------------------------------------------------------------ barra lateral: arquivo
with st.sidebar:
    st.markdown("<h3>Arquivo</h3>", unsafe_allow_html=True)
    up = st.file_uploader("Planilha de dendrometria (.xlsx ou .csv)", type=["xlsx", "xlsm", "csv"],
                          help="O arquivo é lido localmente e nunca é alterado nem enviado à internet.")

data = up.getvalue() if up else None
name = up.name if up else None
_inicial = os.environ.get("ANALISADOR_ARQUIVO_INICIAL")  # opcional: arquivo local aberto ao iniciar
if data is None and _inicial and os.path.isfile(_inicial):
    with open(_inicial, "rb") as fh:
        data, name = fh.read(), os.path.basename(_inicial)
    st.sidebar.caption(f"Arquivo inicial: {name}")
raw = q = res = None
sheet = None
erro_leitura = None
if data is not None:
    try:
        if ingestion.detect_format(name) == "xlsx":
            sheets = c_sheets(data)
            pref = next((s for s in sheets if "dendr" in s.lower()), sheets[0])
            sheet = st.sidebar.selectbox("Planilha", sheets, index=sheets.index(pref))
        raw = c_raw(data, name, sheet)
    except Exception as e:  # falha de leitura ≠ conjunto vazio
        erro_leitura = f"Falha ao ler o arquivo: {e}"

# ------------------------------------------------------------ mapeamento
cmap = None
if raw is not None:
    key = f"map::{raw.meta.sha256}::{sheet}"
    auto = canon.auto_map(raw.headers)
    if key not in st.session_state:
        st.session_state[key] = {cid: auto.originals.get(cid) for cid in CANONICAL_COLUMNS}
    choices = st.session_state[key]
    cmap = canon.manual_map(raw.headers, choices) if any(choices.values()) else auto
    if cmap.is_safe:
        q = c_quality(data, name, sheet, tuple(sorted((k, v) for k, v in choices.items() if v)))

# ------------------------------------------------------------ barra lateral: filtros e parâmetros
filters = Filters()
metodologia = Metodologia()
params = {"largura_classe_cm": 5.0, "incluir_extremos": False, "implantados": 36, "mortalidade_ativa": True}
if q is not None and len(q.records):
    R = q.records
    with st.sidebar:
        with st.expander("Filtros", expanded=False):
            parc = sorted(R["parcela"].dropna().unique(), key=natural_key)
            filters.parcelas = st.multiselect("Parcela", parc, placeholder="Todas")
            esp = sorted(R["especie"].dropna().unique(), key=str.casefold)
            filters.especies = st.multiselect("Espécie", esp, placeholder="Todas")
            arv = sorted(R["arvore"].dropna().unique(), key=natural_key)
            filters.arvores = st.multiselect("Árvore", arv, placeholder="Todas")
            datas = R["data_medicao"].dropna()
            if len(datas):
                d0, d1 = min(datas), max(datas)
                per = st.date_input("Data de medição", (d0, d1), min_value=d0, max_value=d1, format="DD/MM/YYYY")
                if isinstance(per, (tuple, list)) and len(per) == 2 and (per[0] != d0 or per[1] != d1):
                    filters.data_inicio, filters.data_fim = per
            dmax = float(R.loc[R["dap_cm_status"].isin(["MEDIDO", "EXTREMO"]), "dap_cm"].max() or 0)
            if dmax > 0:
                lo, hi = st.slider("Intervalo de DAP (cm)", 0.0, float(round(dmax + 0.5)), (0.0, float(round(dmax + 0.5))), 0.5)
                if (lo, hi) != (0.0, float(round(dmax + 0.5))):
                    filters.dap_min, filters.dap_max = lo, hi
                    filters.manter_sem_dap = st.checkbox("Manter registros sem DAP numérico", True)
            hmax = float(R.loc[R["ht_m_status"] == "MEDIDO", "ht_m"].max() or 0) if "ht_m_status" in R else 0
            if hmax > 0:
                lo, hi = st.slider("Intervalo de HT (m)", 0.0, float(round(hmax + 0.5)), (0.0, float(round(hmax + 0.5))), 0.5)
                if (lo, hi) != (0.0, float(round(hmax + 0.5))):
                    filters.ht_min, filters.ht_max = lo, hi
                    filters.manter_sem_ht = st.checkbox("Manter registros sem HT numérica", True)
            filters.status = st.multiselect("Status de qualidade", list(ESTADOS_REGISTRO), placeholder="Todos",
                                            help="Válidos, com ressalva, inválidos ou inconclusivos.")
            filters.observacao = {"Todos": "todos", "Com observação": "com", "Sem observação": "sem"}[
                st.radio("Observação", ["Todos", "Com observação", "Sem observação"], horizontal=True)]

        with st.expander("Parâmetros", expanded=False):
            params["largura_classe_cm"] = st.number_input("Largura da classe diamétrica (cm)", 0.5, 100.0, 5.0, 0.5,
                                                          help="Exploratório: não é classificação oficial.")
            params["incluir_extremos"] = st.checkbox(
                f"Incluir DAP > {DAP_LIMITE_LEGADO_CM:g} cm nos cálculos", False,
                help="Regra legada NÃO validada metodologicamente. Desmarcado = bloqueado até decisão.")
            modo = st.radio("Indivíduos implantados por parcela", ["Mesmo valor para todas", "Valor por parcela", "Desativar"],
                            help="Denominador de mortalidade/sobrevivência. Não é verdade universal.")
            if modo == "Mesmo valor para todas":
                params["implantados"] = int(st.number_input("Implantados por parcela", 1, 10000, 36))
            elif modo == "Valor por parcela":
                ed = st.data_editor(pd.DataFrame({"parcela": parc, "implantados": 36}), hide_index=True,
                                    disabled=["parcela"], height=220, key="impl_editor")
                params["implantados"] = {p: int(v) for p, v in zip(ed["parcela"], ed["implantados"]) if pd.notna(v)}
            else:
                params["mortalidade_ativa"] = False

        LIT = "Literatura: arboreto ESARM (144 m²)"
        opcoes = ([LIT] if esarm_aplicavel(parc) else []) + ["Não informada", "Mesma área para todas", "Área por parcela"]
        with st.expander("Decisões metodológicas", expanded=False):
            st.markdown("**Área basal por hectare**")
            st.caption("Sem área e desenho amostral, a área basal por hectare fica bloqueada. Toda escolha vai para o manifesto.")
            modo_a = st.radio("Área da parcela", opcoes, key="modo_area",
                              help="A predefinição da literatura só aparece quando as parcelas do arquivo cabem no "
                                   "desenho publicado (1 a 98).")
            if modo_a == LIT:
                metodologia = metodologia_arboreto_esarm()
                st.caption("Parcelas 1–98: 36 plantas, 2 × 2 m → 144 m² (0,0144 ha). Parcelas fora do desenho "
                           "publicado (ex.: PX) ficam fora de G e de A. Fonte: " + ESARM_REFERENCIAS + ".")
            elif modo_a != "Não informada":
                metodologia.unidade_area = st.selectbox("Unidade da área", ["m²", "ha"], key="un_area")
                if modo_a == "Mesma área para todas":
                    a = st.number_input(f"Área de cada parcela ({metodologia.unidade_area})", min_value=0.0, value=0.0,
                                        step=1.0 if metodologia.unidade_area == "m²" else 0.01,
                                        format="%.2f" if metodologia.unidade_area == "m²" else "%.4f",
                                        key="area_unica")
                    metodologia.area_parcela = a if a > 0 else None
                else:
                    ea = st.data_editor(pd.DataFrame({"parcela": parc, "área": [None] * len(parc)}, dtype=object),
                                        hide_index=True, disabled=["parcela"], height=220, key="area_editor",
                                        column_config={"área": st.column_config.NumberColumn(
                                            f"área ({metodologia.unidade_area})", min_value=0.0)})
                    metodologia.area_parcela = {p: float(v) for p, v in zip(ea["parcela"], ea["área"])
                                                if v is not None and pd.notna(v)}
                metodologia.desenho_amostral = st.text_area(
                    "Desenho amostral (obrigatório)", key="desenho",
                    placeholder="ex.: parcelas permanentes de área fixa, alocação sistemática…",
                    help="A extrapolação por hectare pressupõe amostragem adequada e área conhecida.")
                if metodologia.area_parcela is None or metodologia.area_parcela == {}:
                    st.warning("Informe a área (> 0).")
                    metodologia.area_parcela = None
                elif not metodologia.desenho_amostral.strip():
                    st.warning("Descreva o desenho amostral para liberar o cálculo.")
        params["metodologia"] = metodologia.describe()

    res = run_analysis(q.records, q.issues, raw.meta, filters, incluir_extremos=params["incluir_extremos"],
                       largura_classe_cm=params["largura_classe_cm"], implantados=params["implantados"],
                       mortalidade_ativa=params["mortalidade_ativa"], metodologia=metodologia)

with st.sidebar:
    st.divider()
    if st.button("Encerrar aplicação", use_container_width=True):
        st.success("Aplicação encerrada. Pode fechar esta aba.")
        _shutdown()
    st.caption("Todo o processamento ocorre neste computador.")

_topo.markdown(cabecalho(raw, res), unsafe_allow_html=True)

# ------------------------------------------------------------ abas
TABS = ["Início", "Importação", "Qualidade dos dados", "Visão geral", "Dendrometria", "Parcelas", "Espécies",
        "Indivíduos", "Observações", "Registros excluídos", "Exportação", "Metodologia"]
t = dict(zip(TABS, st.tabs(TABS)))


def need_data(tab) -> bool:
    with tab:
        if erro_leitura:
            st.error(erro_leitura)
            return False
        if raw is None:
            st.info("Selecione um arquivo de dendrometria na barra lateral.")
            return False
        if q is None:
            st.warning("Mapeamento de colunas incompleto ou ambíguo. Conclua o mapeamento na aba **Importação**.")
            return False
        if res is None:
            st.warning("O arquivo não possui registros interpretáveis.")
            return False
    return True


# ============================================================ 1. Início
with t["Início"]:
    PASSOS = ("1. Selecione a planilha (**.xlsx** ou **.csv**) na barra lateral.\n"
              "2. Confira o mapeamento de colunas em **Importação**.\n"
              "3. Revise **Qualidade dos dados** e **Registros excluídos**.\n"
              "4. Explore **Visão geral**, **Dendrometria**, **Parcelas**, **Espécies** e **Indivíduos**.\n"
              "5. Baixe resultados e manifesto em **Exportação**.")
    NOTA = ("<p class='nota'>Nenhum dado original é alterado. Valores inválidos não são corrigidos por suposição, "
            "e indicadores sem metodologia definida aparecem sem valor, nunca como zero.</p>")
    if res is None:
        c1, c2 = st.columns([3, 2])
        with c1:
            st.markdown("#### Comece pela planilha")
            st.markdown(PASSOS)
            st.markdown(NOTA, unsafe_allow_html=True)
        with c2:
            if erro_leitura:
                st.error(erro_leitura)
            else:
                st.info("Carregue a planilha na barra lateral à esquerda. O arquivo é lido neste computador e nunca é alterado.")
    else:
        g = res.gerais
        st.markdown("#### Resumo do arquivo")
        cards([get(g, "individuos"), get(g, "parcelas"), get(g, "especies"), get(g, "registros_invalidos")], cols=4)
        st.markdown("#### Situação dos indicadores")
        st.markdown(situacao_indicadores(res.all_indicators()), unsafe_allow_html=True)
        st.markdown("#### O que revisar agora")
        passos = []
        n_dap = (get(g, "dap_invalidos").valor or 0)
        if n_dap:
            passos.append(f"<b>{fmt(n_dap)} DAPs inválidos</b> (por exemplo, número gravado como data) ficaram fora dos cálculos. "
                          "Veja a lista em <b>Registros excluídos</b>.")
        n_inv = get(g, "registros_invalidos").valor or 0
        if n_inv:
            passos.append(f"<b>{fmt(n_inv)} registros inválidos</b>. Os motivos estão em <b>Qualidade dos dados</b>.")
        n_blk = sum(i.status in ESTADOS_SEM_VALOR for i in res.all_indicators())
        if n_blk:
            passos.append(f"<b>{n_blk} indicadores sem valor</b> por falta de dado ou de definição metodológica. "
                          "A aba <b>Metodologia</b> mostra o motivo de cada um.")
        if not passos:
            passos.append("Nenhuma pendência encontrada. Siga para <b>Visão geral</b> e <b>Dendrometria</b>.")
        for ptxt in passos:
            st.markdown(f"<div class='proximo'>{ptxt}</div>", unsafe_allow_html=True)
        with st.expander("Como usar o sistema"):
            st.markdown(PASSOS)
            st.markdown(NOTA, unsafe_allow_html=True)

# ============================================================ 2. Importação
with t["Importação"]:
    if erro_leitura:
        st.error(erro_leitura)
    elif raw is None:
        st.info("Selecione um arquivo na barra lateral.")
    else:
        m = raw.meta
        a, b = st.columns([2, 3])
        with a:
            st.markdown("#### Registro da importação")
            info = pd.DataFrame([
                ("Arquivo", m.nome_arquivo), ("Tamanho", f"{m.tamanho_bytes:,} bytes".replace(",", ".")),
                ("Formato", m.formato.upper()), ("Planilha selecionada", m.planilha or "—"),
                ("Planilhas existentes", ", ".join(m.planilhas_disponiveis) or "—"),
                ("Codificação / separador", f"{m.codificacao or '—'} / {m.separador or '—'}"),
                ("Linhas físicas", m.linhas_fisicas), ("Registros interpretados", m.registros_interpretados),
                ("Linhas vazias ignoradas", m.linhas_vazias_ignoradas),
                ("Data do processamento", m.data_processamento), ("SHA-256", m.sha256),
            ], columns=["campo", "valor"])
            table(info.astype(str))
            for av in m.avisos:
                st.warning(av)
        with b:
            st.markdown("#### Mapeamento de colunas")
            if cmap.is_safe:
                st.success("Mapeamento seguro: todas as colunas obrigatórias foram reconhecidas.")
            else:
                if cmap.missing_required:
                    st.error("Colunas obrigatórias não encontradas: "
                             + ", ".join(LABEL[c] for c in cmap.missing_required)
                             + ". Mapeie manualmente abaixo — a análise só é executada após mapeamento seguro.")
                if cmap.ambiguous:
                    st.error("Mapeamento ambíguo: " + "; ".join(f"{LABEL[k]} ← {v}" for k, v in cmap.ambiguous.items()))
            key = f"map::{m.sha256}::{sheet}"
            opts = ["(não mapear)"] + raw.headers
            with st.expander("Revisar / mapear manualmente", expanded=not cmap.is_safe):
                cols = st.columns(2)
                new = {}
                for k, (cid, (lab, req, _)) in enumerate(CANONICAL_COLUMNS.items()):
                    cur = st.session_state[key].get(cid)
                    sel = cols[k % 2].selectbox(f"{lab}{' *' if req else ''}", opts,
                                                index=opts.index(cur) if cur in opts else 0, key=f"sel_{cid}_{key}")
                    new[cid] = None if sel == "(não mapear)" else sel
                if new != st.session_state[key]:
                    st.session_state[key] = new
                    st.rerun()
            mp = pd.DataFrame([{"coluna canônica": LABEL[c], "obrigatória": "sim" if CANONICAL_COLUMNS[c][1] else "não",
                                "cabeçalho original": cmap.originals.get(c, "—")} for c in CANONICAL_COLUMNS])
            table(mp)
            if cmap.unmapped_headers:
                st.caption("Cabeçalhos não utilizados: " + ", ".join(h or "(vazio)" for h in cmap.unmapped_headers))
        st.markdown("#### Pré-visualização dos dados originais")
        prev = pd.DataFrame([[c.value for c in r.cells] for r in raw.rows[:200]], columns=raw.headers)
        prev.insert(0, "linha", [r.line for r in raw.rows[:200]])
        table(prev.astype(str).replace({"None": ""}), height=320)
        st.caption("Primeiras 200 linhas, valores exatamente como lidos.")

# ============================================================ 3. Qualidade
if need_data(t["Qualidade dos dados"]):
    with t["Qualidade dos dados"]:
        g = res.gerais
        cards([get(g, "registros_validos"), get(g, "registros_ressalva"), get(g, "registros_inconclusivos"),
               get(g, "registros_invalidos")])
        st.markdown("<p class='nota'>Classificação sobre o arquivo completo (sem filtros). A soma das quatro "
                    f"categorias é igual ao total de {len(q.records)} registros interpretados.</p>",
                    unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            cnt = q.records["status_registro"].value_counts().reindex(ESTADOS_REGISTRO, fill_value=0)
            fig = go.Figure(go.Bar(x=cnt.index, y=cnt.values, marker_color=[STATUS_COR[s] for s in cnt.index],
                                   text=cnt.values, textposition="outside",
                                   hovertemplate="%{x}: %{y} registros<extra></extra>"))
            fig.update_layout(title="Qualidade dos registros", yaxis_title="registros", showlegend=False)
            chart(fig, "diagnóstico do analisador", f"{len(q.records)} registros")
        with c2:
            ms = quality.measurement_status_table(q.records)
            cores = {"AUSENTE": CINZA, "INVÁLIDO": VERMELHO, "NÃO APLICÁVEL": AZUL_CLARO, "EXTREMO": AMARELO,
                     "PENDENTE DE REVISÃO": "#8E5A9B"}
            fig = go.Figure()
            for estado, cor in cores.items():
                if estado in ms and ms[estado].sum() > 0:
                    fig.add_bar(y=ms["campo"], x=ms[estado].astype(int), name=estado, orientation="h", marker_color=cor,
                                marker_line_color="#fff", marker_line_width=1,
                                hovertemplate="%{y}: %{x} registros " + estado.lower() + "<extra></extra>")
            fig.update_layout(title="Valores ausentes ou não utilizáveis por campo", barmode="stack",
                              xaxis_title="registros", yaxis=dict(autorange="reversed", title=""), legend_title="",
                              legend=dict(orientation="h", y=-0.2))
            chart(fig, "diagnóstico por campo", f"{int(ms['registros potenciais'].max() if len(ms) else 0)} registros potenciais por campo")
        st.markdown("#### Resumo por diagnóstico e recuperação")
        table(export.quality_report(q))
        st.markdown("#### Ocorrências")
        f1, f2, f3 = st.columns(3)
        iss = q.issues
        sel_sev = f1.multiselect("Severidade", sorted(iss["severidade"].unique()), placeholder="Todas")
        sel_rec = f2.multiselect("Recuperação", sorted(iss["recuperação"].unique()), placeholder="Todas")
        sel_cod = f3.multiselect("Diagnóstico", sorted(iss["código"].unique()), placeholder="Todos")
        v = iss
        if sel_sev:
            v = v[v["severidade"].isin(sel_sev)]
        if sel_rec:
            v = v[v["recuperação"].isin(sel_rec)]
        if sel_cod:
            v = v[v["código"].isin(sel_cod)]
        table(v.drop(columns=["registro"]), height=380)
        st.caption(f"{len(v)} de {len(iss)} ocorrências. 'linha' e 'célula' indicam a posição no arquivo original.")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Valores numéricos armazenados como data")
            cols = []
            for cid in ("dap_cm", "hesg_m", "hesgcopa_m", "hc_m", "ht_m"):
                if f"{cid}_motivo" in q.records:
                    sub = q.records[q.records[f"{cid}_motivo"] == "valor interpretado como data"]
                    for _, r in sub.iterrows():
                        cols.append({"linha": r["_linha"], "campo": LABEL[cid], "parcela": r["parcela"],
                                     "árvore": r["arvore"], "valor armazenado": r[f"{cid}_orig"],
                                     "texto exibido na planilha (pista)": r[f"{cid}_pista"]})
            table(pd.DataFrame(cols), height=300)
            st.caption("Não reconstruídos: '12.05' e '12.5' geram a mesma data. A pista serve apenas à revisão humana.")
        with c2:
            st.markdown("#### Campanhas e duplicidades")
            camp = quality.campaign_summary(q.records)
            table(pd.DataFrame([(k, str(v)) for k, v in camp.items()], columns=["item", "valor"]))
            if q.species_variants:
                st.markdown("**Possíveis variações de grafia (não unificadas)**")
                table(pd.DataFrame({"grafias": [" / ".join(g) for g in q.species_variants]}))

# ============================================================ 4. Visão geral
if need_data(t["Visão geral"]):
    with t["Visão geral"]:
        filtro_banner(res)
        cards(res.gerais, cols=4, titulos={"linhas_importadas": "Linhas importadas"})
        cov = [(LABEL["dap_cm"], get(res.gerais, "cobertura_dap"))] + [
            (LABEL[c], next((i for i in res.alturas.get(c, []) if i.id.endswith("_media")), None))
            for c in ("hesg_m", "hesgcopa_m", "hc_m", "ht_m")]
        cov = [(n, i) for n, i in cov if i is not None and i.cobertura is not None]
        if cov:
            dfc = pd.DataFrame({"variável": [n for n, _ in cov], "cobertura (%)": [i.cobertura * 100 for _, i in cov],
                                "elegíveis": [i.quantidade_elegivel for _, i in cov],
                                "potenciais": [i.quantidade_potencial for _, i in cov]})
            fig = go.Figure(go.Bar(y=dfc["variável"], x=dfc["cobertura (%)"], orientation="h", marker_color=AZUL,
                                   text=[f"{fmt(v, '%')}% ({e}/{p})" for v, e, p in zip(dfc["cobertura (%)"], dfc["elegíveis"], dfc["potenciais"])],
                                   textposition="outside", customdata=dfc[["elegíveis", "potenciais"]],
                                   hovertemplate="%{y}: %{x:.1f}% (%{customdata[0]} de %{customdata[1]})<extra></extra>"))
            fig.update_layout(title="Cobertura das medições", xaxis_title="cobertura (%)", xaxis_range=[0, 115],
                              yaxis=dict(autorange="reversed"))
            chart(fig, "indicadores de cobertura", f"denominador: {dfc['potenciais'].max()} registros potenciais", 320)

# ============================================================ 5. Dendrometria
if need_data(t["Dendrometria"]):
    with t["Dendrometria"]:
        filtro_banner(res)
        s_dap, s_ab, s_alt, s_dist, s_mf = st.tabs(["Diâmetro (DAP)", "Área basal e volumes", "Alturas e copa",
                                                     "Distribuição e maiores", "Multifustes e revisão"])
        with s_dap:
            st.markdown("#### Diâmetro à altura do peito (DAP)")
            cards([i for i in res.dap if i.id != "dap_n"][:4]
                  + [i for i in res.dap if i.id in ("dap_q1", "dap_q3", "dap_dp", "dap_cv")], cols=4)
            st.caption("DAP medido a 1,30 m do solo. Todos os indicadores usam a mesma política de elegibilidade; "
                       "os DAPs fora dela estão em Registros excluídos.")
        with s_ab:
            st.markdown("#### Área basal e volumes")
            cards(res.area_basal[:3] + [res.volumes[0]] + [res.volumes[1]] + res.area_basal[3:], cols=4)
        with s_alt:
            st.markdown("#### Alturas (variáveis tratadas separadamente)")
            medias = [next((i for i in res.alturas.get(c, []) if i.id.endswith("_media")), None)
                      for c in ("hesg_m", "hesgcopa_m", "hc_m", "ht_m")]
            cards([m for m in medias if m is not None], cols=4)
            st.markdown("##### Estatísticas por variável")
            rows = []
            for c in ("hesg_m", "hesgcopa_m", "hc_m", "ht_m"):
                inds = res.alturas.get(c, [])
                if not inds:
                    continue
                by = {i.id.split("_", 1)[1] if not i.id.endswith("_ausentes") else "ausentes": i for i in inds}
                media = next((i for i in inds if i.id.endswith("_media")), None)
                rows.append({"variável": LABEL[c], "indicador de média": media.nome if media else "—",
                             **{k: (by[k].valor if k in by and by[k].disponivel else by[k].status if k in by else "—")
                                for k in ("media", "mediana", "min", "max", "dp")},
                             "elegíveis": media.quantidade_elegivel if media else None,
                             "ausentes": by["ausentes"].valor if "ausentes" in by else None,
                             "cobertura (%)": None if not media or media.cobertura is None else media.cobertura * 100,
                             "status": media.status if media else "—"})
            tab_h = pd.DataFrame(rows).rename(columns={"media": "média (m)", "mediana": "mediana (m)", "min": "mínimo (m)",
                                                       "max": "máximo (m)", "dp": "desvio-padrão (m)"})
            table(tab_h)
            st.caption("'Altura total média' refere-se somente a HT. HESG = altura do esgalhamento (solo até a inserção do "
                       "primeiro galho vivo); HESGCOPA = altura da formação da copa (solo até o início da copa); "
                       "HC = altura comercial (usada no volume de Spurr); HT = altura total (solo até o ápice).")
            st.markdown("#### Copa — derivada de HT e HESGCOPA")
            cards(res.copa, cols=2)
            st.caption("Comprimento de copa = HT − HESGCOPA; proporção = comprimento / HT. Só entram indivíduos com os dois "
                       "valores elegíveis e HESGCOPA ≤ HT; nada é corrigido.")
        with s_dist:
            st.markdown("#### Distribuição diamétrica (exploratória)")
            di = res.distribuicao_info
            c1, c2 = st.columns([3, 2])
            with c1:
                if not res.distribuicao.empty:
                    d = res.distribuicao
                    fig = go.Figure(go.Bar(x=d["centro (cm)"], y=d["frequência absoluta"], width=params["largura_classe_cm"] * 0.92,
                                           marker_color=VERDE, customdata=d[["classe", "frequência relativa (%)"]],
                                           hovertemplate="classe %{customdata[0]} cm<br>%{y} indivíduos (%{customdata[1]:.2f}%)<extra></extra>"))
                    fig.update_layout(title=f"Distribuição diamétrica — classes de {fmt(params['largura_classe_cm'])} cm",
                                      xaxis_title="DAP (cm) — classes [inferior ; superior)", yaxis_title="indivíduos", bargap=0)
                    chart(fig, "DAPs elegíveis pela política única", f"{di['n_elegivel']} elegíveis de {di['n_potencial']} "
                          f"potenciais ({di['n_excluido']} excluídos)")
                else:
                    st.info("Nenhum DAP elegível.")
            with c2:
                table(res.distribuicao.drop(columns=["centro (cm)"]) if not res.distribuicao.empty else res.distribuicao, height=420)
                st.caption("Classes automáticas apenas para exploração visual; não constituem metodologia oficial.")
            st.markdown("#### Maiores indivíduos — rankings separados")
            r1, r2, r3 = st.tabs(["Maiores DAPs", "Maiores alturas totais (HT)", "Maiores áreas basais individuais"])
            for tb, k in ((r1, "dap"), (r2, "ht"), (r3, "g")):
                with tb:
                    table(res.rankings.get(k, pd.DataFrame()))
        with s_mf:
            st.markdown("#### Multifustes — regra de Finger (1992), adotada no Manual de Dendrometria da CEPLAC")
            mf = res.multifustes
            if len(mf):
                n_ext = int((mf["situação"] == "FUSTES EXTRAÍDOS").sum())
                st.markdown(f"<p class='nota'>Fuste bifurcado abaixo de 1,30 m: cada fuste é medido; a área seccional do "
                            f"indivíduo é Σ π·dⱼ²/40000 e o DAP equivalente é √(Σ dⱼ²). Fustes extraídos da observação "
                            f"apenas quando a quantidade declarada é igual à quantidade de valores listados: "
                            f"<b>{n_ext}</b> extraídos, <b>{len(mf) - n_ext}</b> para revisão humana.</p>",
                            unsafe_allow_html=True)
                table(mf.drop(columns=["observação (original)"]), height=360)
            else:
                st.info("Nenhum indício de multifuste no conjunto analisado.")
            ext = res.elegibilidade_dap
            ext = ext[ext["dap_cm_status"] == "EXTREMO"] if len(ext) else ext
            st.markdown(f"#### Revisão: DAP acima de {DAP_LIMITE_LEGADO_CM:g} cm (regra legada não validada)")
            if len(ext):
                table(ext[["_linha", "parcela", "arvore", "especie", "dap_cm", "dap_cm_orig", "dap_elegivel"]])
            else:
                st.success(f"Nenhum DAP acima de {DAP_LIMITE_LEGADO_CM:g} cm no conjunto analisado.")


# ============================================================ 6. Parcelas
if need_data(t["Parcelas"]):
    with t["Parcelas"]:
        filtro_banner(res)
        P = res.parcelas
        n_parc = len(P)
        c1, c2 = st.columns(2)
        with c1:
            pg = P.dropna(subset=["área basal G (m²)"]) if "área basal G (m²)" in P else pd.DataFrame()
            if len(pg):
                fig = go.Figure(go.Bar(x=pg["parcela"].astype(str), y=pg["área basal G (m²)"], marker_color=VERDE,
                                       customdata=pg["DAPs elegíveis"],
                                       hovertemplate="Parcela %{x}<br>G = %{y:.4f} m²<br>%{customdata} DAPs elegíveis<extra></extra>"))
                fig.update_layout(title="Área basal por parcela", xaxis_title="parcela", yaxis_title="área basal G (m²)",
                                  xaxis_type="category")
                chart(fig, "tabela por parcela", f"{int(pg['DAPs elegíveis'].sum())} DAPs elegíveis em {len(pg)} parcelas")
        with c2:
            ind = res.individuos
            dp = ind[ind["DAP elegível"]] if len(ind) else ind
            if len(dp):
                order = sorted(dp["parcela"].unique(), key=natural_key)
                fig = px.box(dp, x="parcela", y="DAP (cm)", category_orders={"parcela": order}, points=False,
                             color_discrete_sequence=[AZUL], title="DAP por parcela")
                fig.update_layout(xaxis_title="parcela", yaxis_title="DAP (cm)", xaxis_type="category")
                chart(fig, "DAPs elegíveis por indivíduo", f"{len(dp)} DAPs elegíveis")
        c1, c2 = st.columns(2)
        with c1:
            if "riqueza observada" in P and len(P):
                fig = go.Figure(go.Bar(x=P["parcela"].astype(str), y=P["riqueza observada"], marker_color=AZUL_CLARO,
                                       hovertemplate="Parcela %{x}: %{y} espécie(s)<extra></extra>"))
                fig.update_layout(title="Riqueza observada por parcela", xaxis_title="parcela",
                                  yaxis_title="espécies (nº)", xaxis_type="category")
                chart(fig, "tabela por parcela", f"{n_parc} parcelas")
        with c2:
            ph = P.dropna(subset=["altura total média HT (m)"]) if "altura total média HT (m)" in P else pd.DataFrame()
            if len(ph):
                fig = go.Figure(go.Bar(x=ph["parcela"].astype(str), y=ph["altura total média HT (m)"], marker_color=AZUL,
                                       hovertemplate="Parcela %{x}: %{y:.2f} m<extra></extra>"))
                fig.update_layout(title="Altura total média (HT) por parcela", xaxis_title="parcela",
                                  yaxis_title="HT média (m)", xaxis_type="category")
                chart(fig, "tabela por parcela", f"{len(ph)} parcelas com HT elegível")
        st.markdown("#### Resultados por parcela")
        table(P, height=420)
        st.markdown("#### Registros de uma parcela")
        if n_parc:
            sel = st.selectbox("Parcela", list(P["parcela"]), key="parc_sel")
            sub = q.records[q.records["parcela"] == sel]
            table(export.original_with_diagnosis(quality.QualityResult(sub, q.issues, q.mapping)))
        st.markdown("#### Mortalidade e sobrevivência")
        cards(res.mortalidade, cols=2)
        st.caption(res.mortalidade[0].formula)
        if not res.mortalidade_tabela.empty:
            table(res.mortalidade_tabela)
        st.markdown("#### Replantio")
        for n in res.replantio_notas:
            st.info(n)
        if not res.replantio.empty:
            table(res.replantio)

# ============================================================ 7. Espécies
if need_data(t["Espécies"]):
    with t["Espécies"]:
        filtro_banner(res)
        S = res.especies
        cards([get(res.gerais, "especies")] + list(res.diversidade), cols=4)
        st.markdown("<p class='nota'>Índices de Shannon (ln), Pielou e Simpson conforme Brower & Zar (1984) e Magurran "
                    "(2004). Em um arboreto plantado descrevem a coleção registrada, não uma comunidade natural.</p>",
                    unsafe_allow_html=True)
        if len(S):
            top = S.head(25)
            c1, c2 = st.columns(2)
            with c1:
                fig = go.Figure(go.Bar(y=top["espécie"], x=top["Abundância por indivíduos únicos"], orientation="h",
                                       marker_color=VERDE, hovertemplate="%{y}: %{x} indivíduos<extra></extra>"))
                fig.update_layout(title="Abundância por indivíduos únicos (25 maiores)", xaxis_title="indivíduos (nº)",
                                  yaxis=dict(autorange="reversed", title=""))
                chart(fig, "tabela por espécie", f"{int(S['Abundância por indivíduos únicos'].sum())} indivíduos com espécie", 620)
            with c2:
                sg = S.dropna(subset=["área basal G (m²)"]).sort_values("área basal G (m²)", ascending=False).head(25)
                fig = go.Figure(go.Bar(y=sg["espécie"], x=sg["área basal G (m²)"], orientation="h", marker_color=AZUL,
                                       customdata=sg["DAPs elegíveis"],
                                       hovertemplate="%{y}: %{x:.4f} m² (%{customdata} DAPs)<extra></extra>"))
                fig.update_layout(title="Área basal por espécie (25 maiores)", xaxis_title="área basal G (m²)",
                                  yaxis=dict(autorange="reversed", title=""))
                chart(fig, "tabela por espécie", f"{int(sg['DAPs elegíveis'].sum())} DAPs elegíveis nas espécies exibidas", 620)
        st.markdown("#### Resultados por espécie")
        table(S, height=460)
        st.caption("'Abundância por indivíduos únicos' = pares Parcela + Árvore distintos. 'Ocorrência em parcelas' = "
                   "parcelas com ao menos um indivíduo da espécie. Parâmetros fitossociológicos (Mueller-Dombois & "
                   "Ellenberg, 1974): DR = nᵢ/N; DoR = Gᵢ/G; FA = parcelas com a espécie / total de parcelas; "
                   "FR = FAᵢ/ΣFA; VI = DR + DoR + FR (0–300). Espécie sem área basal medida não tem DoR nem VI.")

# ============================================================ 8. Indivíduos
if need_data(t["Indivíduos"]):
    with t["Indivíduos"]:
        filtro_banner(res)
        I = res.individuos
        if len(I):
            ids = sorted(I["indivíduo"].dropna().unique(), key=lambda s: tuple(natural_key(x.strip()) for x in s.split("|")))
            c_sel, c_info = st.columns([2, 3])
            with c_sel:
                sel = st.selectbox("Indivíduo (Parcela | Árvore)", ids,
                                   help="Digite para buscar, por exemplo 26 | 4.")
            sub = q.records[q.records["individuo_id"] == sel].sort_values("_linha")
            reg = sub.iloc[-1]
            li = I[I["indivíduo"] == sel]
            linha_ind = li.iloc[-1] if len(li) else None
            ct = dd.crown_table(sub)
            copa = ct.loc[reg.name] if reg.name in ct.index else None
            status_reg = reg.get("status_registro") or (linha_ind.get("status do registro") if linha_ind is not None else "—")
            with c_info:
                st.markdown(
                    f"<div class='ind-cab'><div class='ind-esp'>{html.escape(str(reg.get('especie') or 'Espécie não informada'))}</div>"
                    f"<div class='ind-meta'>Parcela <b>{html.escape(str(reg.get('parcela')))}</b> · Árvore "
                    f"<b>{html.escape(str(reg.get('arvore')))}</b> · {len(sub)} medição(ões) · registro "
                    f"<b>{html.escape(str(status_reg).lower())}</b></div></div>", unsafe_allow_html=True)
            fi = fichas_individuo(reg, linha_ind, copa)
            if fichas_react.disponivel():
                st.markdown("#### Medidas de campo")
                fichas_react.fichas(fi[:5], 5, key=f"ind-med-{sel}")
                st.markdown("#### Calculados a partir das medidas")
                fichas_react.fichas(fi[5:], 4, key=f"ind-calc-{sel}")
            else:
                st.info("Componente de cartões indisponível; os valores estão na tabela abaixo.")
            c_obs, c_oc = st.columns(2)
            with c_obs:
                st.markdown("#### Observação de campo")
                txt = reg.get("observacao")
                if txt and str(txt).strip():
                    st.markdown(f"<div class='obs-campo'>{html.escape(str(txt))}</div>", unsafe_allow_html=True)
                    st.caption("Texto livre: sinaliza, não confirma (ex.: menção a morte não é estado vital).")
                else:
                    st.caption("Sem observação registrada.")
            with c_oc:
                st.markdown("#### Ocorrências de qualidade")
                oc = q.issues[q.issues["registro"].isin(sub["_registro"])]
                if len(oc):
                    itens = "".join(
                        f"<li><b>{html.escape(str(o['campo']))}</b> (célula {html.escape(str(o['célula']))}) — "
                        f"{html.escape(str(o['descrição']))}<br><span>{html.escape(str(o['severidade']).lower())} · "
                        f"{html.escape(str(o['recuperação']).lower())}</span></li>" for _, o in oc.iterrows())
                    st.markdown(f"<ul class='ocorr'>{itens}</ul>", unsafe_allow_html=True)
                else:
                    st.caption("Nenhuma ocorrência para este indivíduo.")
            with st.expander(f"Todas as medições deste indivíduo, com os valores originais ({len(sub)})"):
                table(export.original_with_diagnosis(quality.QualityResult(sub, q.issues, q.mapping)))

        st.markdown("#### Todos os indivíduos")
        busca = st.text_input("Buscar na tabela (parcela, árvore, espécie ou observação)", "")
        v = I
        if busca and len(I):
            b = canon.fold(busca)
            mask = I[["indivíduo", "espécie", "observação"]].astype(str).apply(lambda s: s.map(canon.fold).str.contains(b, regex=False))
            v = I[mask.any(axis=1)]
        table(v, height=440)
        st.caption(f"{len(v)} de {len(I)} registros de indivíduos identificáveis.")

# ============================================================ 9. Observações
if need_data(t["Observações"]):
    with t["Observações"]:
        filtro_banner(res)
        M = res.mencoes
        st.markdown("<p class='nota'>Menções <b>potenciais</b> identificadas por termos. Nenhuma menção é ocorrência "
                    "científica confirmada; todas exigem revisão. Frases negativas ('sem bromélias') são marcadas.</p>",
                    unsafe_allow_html=True)
        sm = obs.mentions_summary(M)
        c1, c2 = st.columns([2, 3])
        with c1:
            table(sm, height=420)
        with c2:
            if len(sm):
                fig = go.Figure()
                fig.add_bar(y=sm["categoria"], x=sm["menções positivas"], name="positiva", orientation="h", marker_color=AZUL)
                fig.add_bar(y=sm["categoria"], x=sm["menções negadas"], name="negada", orientation="h", marker_color=CINZA)
                fig.update_layout(title="Menções potenciais por categoria", barmode="stack", xaxis_title="menções (nº)",
                                  yaxis=dict(autorange="reversed", title=""), legend_title="")
                chart(fig, "campo Observação (texto livre)", f"{int(res.n_registros)} registros analisados", 420)
        cats = st.multiselect("Categoria", sorted(M["categoria"].unique()) if len(M) else [], placeholder="Todas")
        neg = st.radio("Negação", ["Todas", "Somente positivas", "Somente negadas"], horizontal=True)
        v = M
        if cats:
            v = v[v["categoria"].isin(cats)]
        if neg == "Somente positivas":
            v = v[v["negação"] == "não"]
        elif neg == "Somente negadas":
            v = v[v["negação"] == "sim"]
        table(v, height=420)

# ============================================================ 10. Registros excluídos
if need_data(t["Registros excluídos"]):
    with t["Registros excluídos"]:
        filtro_banner(res)
        from analytics import apply_filters
        E = export.excluded_records(apply_filters(q.records, filters), params["incluir_extremos"])
        resumo = E.groupby(["excluído de", "motivo"]).size().reset_index(name="registros") if len(E) else E
        st.markdown("#### Resumo das exclusões")
        table(resumo.sort_values(["excluído de", "registros"], ascending=[True, False]) if len(resumo) else resumo)
        st.markdown("#### Detalhe por registro")
        alvo = st.multiselect("Excluído de", sorted(E["excluído de"].unique()) if len(E) else [], placeholder="Todos")
        table(E[E["excluído de"].isin(alvo)] if alvo else E, height=460)
        st.caption("Todo registro excluído tem motivo. Valores originais preservados.")

# ============================================================ 11. Exportação
if need_data(t["Exportação"]):
    with t["Exportação"]:
        filtro_banner(res)
        man = export.build_manifest(raw.meta, q, res, filters, params)
        tabs = export.export_tables(raw.meta, q, res, params["incluir_extremos"])
        base = os.path.splitext(raw.meta.nome_arquivo)[0]
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
        c1, c2, c3 = st.columns(3)
        c1.download_button("⬇ Pacote completo (XLSX)", export.to_xlsx(tabs, man), f"{base}_resultados_{stamp}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        c2.download_button("⬇ Manifesto (JSON)", export.manifest_json(man), f"{base}_manifesto_{stamp}.json",
                           "application/json", use_container_width=True)
        c3.download_button("⬇ Relatório (HTML)", export.to_html_report(raw.meta, q, res, man),
                           f"{base}_relatorio_{stamp}.html", "text/html", use_container_width=True)
        st.markdown("#### Tabelas individuais (CSV · UTF-8 com BOM · separador ';' · decimal ',')")
        nomes = {"01_originais_diagnostico": "Dados originais com diagnóstico", "02_normalizados": "Dados normalizados",
                 "03_registros_invalidos": "Registros inválidos", "04_registros_excluidos": "Registros excluídos",
                 "05_indicadores_gerais": "Indicadores", "06_resultados_parcela": "Resultados por parcela",
                 "07_resultados_especie": "Resultados por espécie", "08_resultados_individuo": "Resultados por indivíduo",
                 "08b_multifustes": "Multifustes", "09_relatorio_qualidade": "Relatório de qualidade", "09b_ocorrencias_qualidade": "Ocorrências de qualidade"}
        cols = st.columns(3)
        for k, (key, lab) in enumerate(nomes.items()):
            cols[k % 3].download_button(f"{lab} ({len(tabs[key])})", export.to_csv(tabs[key]), f"{base}_{key}.csv",
                                        "text/csv", use_container_width=True, key=f"dl_{key}")
        with st.expander("Ver manifesto"):
            st.json(man, expanded=False)
        st.caption("Os arquivos exportados refletem os filtros e parâmetros atuais (registrados no manifesto). "
                   "Dados originais, normalizados e qualidade referem-se ao arquivo completo.")

# ============================================================ 12. Metodologia
with t["Metodologia"]:
    st.markdown("#### Fórmulas e critérios")
    formulas = pd.DataFrame([
        ("Área seccional individual", "g = π · DAP² / 40000", "m²", "DAP elegível (política única)"),
        ("Área basal total", "G = Σ gᵢ", "m²", "soma absoluta da amostra; não é por hectare"),
        ("Área basal por hectare", "ABₕₐ = G / A ;  A = Σ aⱼ (ha) ;  F = 1 / aⱼ", "m²/ha",
         "exige área + desenho amostral: predefinição da literatura (arboreto ESARM, 144 m²) ou informada pelo usuário"),
        ("Área basal com multifustes", "gᵢ = Σⱼ π·dᵢⱼ²/40000 ;  d_eq = √(Σ dᵢⱼ²)", "m² / cm",
         "Finger (1992) via Manual CEPLAC; Stewart & Salazar (1992); só fustes extraídos por padrão estrutural"),
        ("Média aritmética do DAP", "x̄ = Σ DAPᵢ / n", "cm", "não é 'diâmetro médio oficial'"),
        ("Diâmetro quadrático médio", "dg = √(Σ DAPᵢ² / n) = √(40000 · Ḡ / π)", "cm",
         "literatura (Finger, 1992; Soares et al., 2011); separado da média aritmética; 'oficial' = decisão M5"),
        ("Shannon / Pielou / Simpson", "H' = −Σ pᵢ ln pᵢ ; J' = H'/ln S ; 1 − Σ nᵢ(nᵢ−1)/[N(N−1)]", "nats / —",
         "Brower & Zar (1984); Magurran (2004); nᵢ = indivíduos únicos; arboreto plantado (ressalva)"),
        ("Parâmetros fitossociológicos", "DR = nᵢ/N ; DoR = Gᵢ/G ; FA = Pᵢ/P ; FR = FAᵢ/ΣFA ; VI = DR+DoR+FR",
         "%", "Mueller-Dombois & Ellenberg (1974)"),
        ("Limite físico de altura", "altura > 120 m → EXTREMO (fora do cálculo, preservado)", "m",
         "maior árvore viva medida: Hyperion, 115,92 m (116,07 m em 2019)"),
        ("Alturas (siglas do projeto)", "HESG: solo → 1º galho vivo ; HESGCOPA: solo → início da copa ; HC: solo → topo utilizável ; HT: solo → ápice", "m",
         "referencias/WhatsApp Image 2026-11-17 17.35.09 (nota (*) de HESGCOPA não fornecida)"),
        ("Copa", "comprimento = HT − HESGCOPA ; proporção = (HT − HESGCOPA)/HT × 100", "m / %",
         "derivado das definições do projeto; indivíduos com HT e HESGCOPA elegíveis e HESGCOPA ≤ HT"),
        ("Coerência entre alturas", "HC, HESG, HESGCOPA ≤ HT", "m",
         "definição de altura total (Manual CEPLAC; Soares et al., 2007); violação gera advertência"),
        ("Desvio-padrão amostral", "s = √[Σ(xᵢ − x̄)² / (n − 1)]", "cm / m", "n ≥ 2; algoritmo de duas passagens"),
        ("Coeficiente de variação", "CV = s / x̄ × 100", "%", "indisponível se x̄ = 0 ou n < 2"),
        ("Quartis e mediana", "interpolação linear (Hyndman & Fan tipo 7)", "cm / m", "igual ao QUARTIL.INC do Excel"),
        ("Volume cilíndrico", "v = g · HT", "m³", "sem fator de forma; informado como cilíndrico"),
        ("Volume comercial (Spurr)", "Vc = 0,106531813 + 5,3372·10⁻⁵ · DAP² · HC", "m³",
         "Jorge (1982); somente com HC; coeficientes regionais"),
        ("Cobertura", "elegíveis / potenciais", "%", "potenciais = registros identificáveis"),
        ("Mortalidade / sobrevivência", "mortos / implantados × 100 ; vivos / implantados × 100", "%",
         "somente com estado vital estruturado; denominador configurável (36 padrão)"),
    ], columns=["indicador", "fórmula", "unidade", "critério / observação"])
    table(formulas)
    st.markdown("#### Política de elegibilidade e decisões em uso")
    for d in export.DECISOES_METODOLOGICAS:
        st.markdown(f"- {d}")
    if res is not None and res.metodologia.decisoes():
        st.markdown("**Decisões informadas pelo usuário nesta execução**")
        for d in res.metodologia.decisoes():
            st.markdown(f"- ⚠️ {d}")
    st.markdown("#### Tolerâncias numéricas (|produzido − esperado| ≤ atol + rtol·|esperado|)")
    table(pd.DataFrame([(k, v.atol, v.rtol, v.justificativa) for k, v in TOLERANCIAS.items()],
                       columns=["grandeza", "atol", "rtol", "justificativa"]))
    st.markdown("#### Indicadores pendentes de definição")
    table(pd.DataFrame([(n, "PENDENTE DE DEFINIÇÃO", m) for n, m in PENDENTES], columns=["indicador", "status", "motivo"]))
    if res is not None:
        bl = [i for i in res.all_indicators() if i.status in ESTADOS_SEM_VALOR]
        if bl:
            st.markdown("#### Indicadores bloqueados nesta análise")
            table(pd.DataFrame(indicadores_para_tabela(bl))[["indicador", "status", "observações", "fórmula"]])
        st.markdown("#### Todos os indicadores desta análise")
        table(pd.DataFrame(indicadores_para_tabela(res.all_indicators())), height=420)
    st.markdown("#### Referências")
    st.markdown(
        "- *Fórmulas Dendrométricas — PTMC* (Camila): DAP, área seccional, área basal, AB/ha e equação de Spurr.\n"
        "- Barazetti, V. M. et al. Arboreto da Ceplac. *Unoesc & Ciência – ACET*, 2(1):31-46, 2011 (desenho do arboreto ESARM).\n"
        "- Gama-Rodrigues, A. C.; Barros, N. F.; Mendonça, E. S. *R. Bras. Ci. Solo*, 23:581-592, 1999 (parcelas de 144 m², 2 × 2 m).\n"
        "- Finger, C. A. G. *Fundamentos de Biometria Florestal*. UFSM, 1992 (bifurcação abaixo de 1,30 m; dg).\n"
        "- Soares, C. P. B.; Paula Neto, F.; Souza, A. L. *Dendrometria e Inventário Florestal*. UFV, 2007/2011.\n"
        "- Stewart, J. L.; Salazar, R. (1992): DAP equivalente de árvores multifuste.\n"
        "- Mueller-Dombois, D.; Ellenberg, H. *Aims and Methods of Vegetation Ecology*. Wiley, 1974.\n"
        "- Brower, J. E.; Zar, J. H. *Field and Laboratory Methods for General Ecology*, 1984; Magurran, A. E. "
        "*Measuring Biological Diversity*, 2004.\n"
        "- Sillett et al. / Redwood National Park: Hyperion (*Sequoia sempervirens*), 115,92 m.\n"
        "- *Manual de Dendrometria* — CEPLAC (D. É. Lobão, 2013): DAP a 1,30 m, alturas, bifurcação.\n"
        "- Orientação em áudio (17/11/2026): volume cilíndrico sempre; volume comercial (Spurr) quando houver HC.\n"
        "- Burden, R. L.; Faires, J. D. *Análise Numérica*: erro absoluto/relativo, tolerância, estabilidade.\n"
        "- OpenSpec `reorganizar-validar-coleta-e-analises-agroflorestais` (decisões M1–M15).")
