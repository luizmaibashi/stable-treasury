"""Camada de design do dashboard (redesign visual + didático).
Mantém CSS, hero e cards fora do app.py. Assinatura visual: a LINHA DE PEG — o
depeg real do USDC no colapso do SVB (mar/2023), dado real da DefiLlama.
"""
import base64

import streamlit as st

# --- dado real: depeg do USDC no SVB (mar/2023), amostra 6h da DefiLlama ---
_SVB_USDC = [
    1.0, 1.001, 1.0, 0.9997, 1.001, 1.001, 1.0, 1.0007, 0.9999, 1.0, 1.001,
    0.9998, 1.001, 1.002, 1.001, 1.001, 1.0, 1.0, 1.001, 1.001, 1.001, 1.0003,
    1.0019, 1.0032, 0.9941, 0.9361, 0.9044, 0.9354, 0.9603, 0.9619, 0.9529,
    0.9632, 0.9928, 0.9832, 0.991, 1.001, 0.9989, 0.9982, 0.9997, 0.9975,
    0.9986, 0.9992, 1.003, 1.003, 1.003, 1.003, 1.005, 1.006, 1.0051, 1.0054,
    1.0041, 1.0058, 1.0018, 1.0026, 1.0046, 1.003, 1.004, 1.004, 1.003, 1.003,
]


def _peg_svg() -> str:
    # desenha a série real como polyline + régua tracejada no peg (1,00) + marcador no fundo.
    w, h, top, bot = 640, 150, 18, 128
    pmax, pmin = 1.008, 0.895
    def y(p): return top + (pmax - p) / (pmax - pmin) * (bot - top)
    def x(i): return i / (len(_SVB_USDC) - 1) * w
    pts = " ".join(f"{x(i):.1f},{y(p):.1f}" for i, p in enumerate(_SVB_USDC))
    y_peg = y(1.0)
    imin = _SVB_USDC.index(min(_SVB_USDC))
    xmin, ymin = x(imin), y(min(_SVB_USDC))
    area = f"0,{bot} " + pts + f" {w},{bot}"
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'preserveAspectRatio="none">'
        f'<defs><linearGradient id="pegfill" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="#37D9A0" stop-opacity="0.22"/>'
        f'<stop offset="100%" stop-color="#37D9A0" stop-opacity="0"/></linearGradient></defs>'
        f'<line x1="0" y1="{y_peg:.1f}" x2="{w}" y2="{y_peg:.1f}" stroke="#3B4C69" '
        f'stroke-width="1" stroke-dasharray="4 4"/>'
        f'<text x="6" y="{y_peg-7:.1f}" fill="#6B7A93" font-family="monospace" '
        f'font-size="11">PEG · US$ 1,0000</text>'
        f'<polygon points="{area}" fill="url(#pegfill)"/>'
        f'<polyline points="{pts}" fill="none" stroke="#37D9A0" stroke-width="2" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'<circle cx="{xmin:.1f}" cy="{ymin:.1f}" r="4.5" fill="#FF5D5D"/>'
        f'<text x="{xmin+10:.1f}" y="{ymin+4:.1f}" fill="#FF8A8A" font-family="monospace" '
        f'font-size="11">US$ 0,90 — depeg</text></svg>'
    )
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return (
        f'<img class="peg-svg" alt="Preço do USDC rompendo a paridade no colapso do SVB, '
        f'mar/2023" src="data:image/svg+xml;base64,{b64}"/>'
    )


_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  --ink:#0E1522; --surface:#172033; --surface2:#1F2A40; --line:#2A3852;
  --text:#EAEEF6; --muted:#94A0B6; --peg:#37D9A0; --warn:#F2B03D; --depeg:#FF5D5D;
}
html, body, .stApp, [class*="css"] { font-family:'IBM Plex Sans',system-ui,sans-serif; }
h1,h2,h3,h4 { font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.01em; }

/* números e dados em mono — leitura de terminal/instrumento */
[data-testid="stMetricValue"], .mono { font-family:'IBM Plex Mono',monospace !important; }
[data-testid="stMetricValue"] { font-size:1.5rem; color:var(--text); }
[data-testid="stMetricLabel"] { color:var(--muted); text-transform:uppercase;
  font-size:.68rem; letter-spacing:.08em; }

/* --- HERO --- */
.hero { border:1px solid var(--line); border-radius:16px; padding:30px 34px 26px;
  background:linear-gradient(180deg,#172033 0%,#111a29 100%); margin-bottom:8px; }
.hero .eyebrow { font-family:'IBM Plex Mono',monospace; color:var(--peg);
  font-size:.72rem; letter-spacing:.16em; text-transform:uppercase; margin-bottom:12px; }
.hero h1 { font-size:2.15rem; line-height:1.08; margin:0 0 14px; color:var(--text);
  font-weight:700; }
.hero h1 .em { color:var(--peg); }
.hero .lede { color:#C3CBDA; font-size:1.02rem; line-height:1.55; max-width:64ch; margin:0; }
.hero .lede b { color:var(--text); font-weight:600; }

.peg-svg { width:100%; height:150px; display:block; margin:18px 0 6px; }
.peg-lbl { font-family:'IBM Plex Mono',monospace; font-size:11px; fill:#6B7A93; letter-spacing:.05em; }
.depeg-lbl { font-family:'IBM Plex Mono',monospace; font-size:11px; fill:#FF8A8A; font-weight:500; }

.chip { display:inline-flex; align-items:center; gap:8px; font-family:'IBM Plex Mono',monospace;
  font-size:.78rem; color:var(--warn); background:rgba(242,176,61,.10);
  border:1px solid rgba(242,176,61,.35); border-radius:999px; padding:6px 14px; }

/* --- passos "como funciona" --- */
.steps { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:20px 0 4px; }
.step { border:1px solid var(--line); border-left:3px solid var(--peg); border-radius:10px;
  padding:14px 16px; background:var(--surface); }
.step .k { font-family:'IBM Plex Mono',monospace; font-size:.7rem; color:var(--peg); letter-spacing:.1em; }
.step .t { font-family:'Space Grotesk',sans-serif; font-weight:600; color:var(--text);
  font-size:.98rem; margin:6px 0 3px; }
.step .d { color:var(--muted); font-size:.82rem; line-height:1.4; }
@media (max-width:820px){ .steps{ grid-template-columns:1fr 1fr; } }

/* --- card didático no topo de cada aba --- */
.didatic { border:1px solid var(--line); border-radius:12px; padding:16px 20px;
  background:var(--surface); margin:2px 0 20px; position:relative; overflow:hidden; }
.didatic::before { content:""; position:absolute; left:0; top:0; bottom:0; width:3px;
  background:linear-gradient(180deg,var(--peg),transparent); }
.didatic .lead { font-family:'Space Grotesk',sans-serif; font-weight:600; font-size:1.05rem;
  color:var(--text); margin:0 0 6px; }
.didatic p { color:#C3CBDA; font-size:.9rem; line-height:1.55; margin:0 0 8px; }
.didatic .read { color:var(--muted); font-size:.84rem; line-height:1.5; margin:0; }
.didatic .read b { color:var(--peg); font-weight:600; }
.didatic .term { font-family:'IBM Plex Mono',monospace; color:var(--peg); font-size:.85em; }

/* tabs mais legíveis */
button[data-baseweb="tab"] { font-family:'Space Grotesk',sans-serif; font-weight:600; }
[data-baseweb="tab-list"] { gap:4px; }

/* botões primários na cor do peg */
.stButton>button[kind="primary"] { background:var(--peg); color:#08130E; border:0; font-weight:600; }
.stButton>button[kind="primary"]:hover { background:#2FC993; color:#08130E; }
</style>
"""


def aplicar_estilo() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def hero() -> None:
    st.markdown(
        f"""
        <div class="hero">
          <div class="eyebrow">Painel de tesouraria · pagamentos cross-border</div>
          <h1>Uma stablecoin vale <span class="em">US$ 1,00</span> — até o dia em que não vale.</h1>
          <p class="lede">Pagar um fornecedor no exterior por <b>stablecoin</b> (um dólar digital)
          custa cerca de <b>90% menos</b> que uma transferência bancária internacional (Wire).
          Mas essa moeda pode <b>romper a paridade</b> a qualquer hora — foi o que aconteceu com o
          USDC na quebra do banco SVB, abaixo — e a economia tem <b>prazo para acabar</b>. Este
          painel mede as duas coisas: <b>quanto você economiza</b> e <b>quanto risco corre</b>.</p>
          {_peg_svg()}
          <div class="chip">⏳ A brecha regulatória fecha em out/2026 — Resolução BCB 561</div>
          <div class="steps">
            <div class="step"><div class="k">01 · RISCO</div><div class="t">A moeda está confiável agora?</div><div class="d">Mede o risco de romper a paridade (VaR/ES) sobre o histórico real.</div></div>
            <div class="step"><div class="k">02 · CAIXA</div><div class="t">Como dividir o dinheiro?</div><div class="d">Aloca reserva, hedge em dólar e giro — com regras de tesouraria real.</div></div>
            <div class="step"><div class="k">03 · CUSTO</div><div class="t">Qual via paga menos?</div><div class="d">Compara PIX, Wire, USDT e USDC pelo custo total da operação.</div></div>
            <div class="step"><div class="k">04 · LEI</div><div class="t">Isso é permitido?</div><div class="d">Valida a operação contra as regras do Banco Central.</div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def intro(lead: str, oque: str, como_ler: str) -> None:
    # card didático padrão no topo de cada aba: o que é + como ler o resultado.
    st.markdown(
        f"""<div class="didatic">
          <p class="lead">{lead}</p>
          <p>{oque}</p>
          <p class="read"><b>Como ler:</b> {como_ler}</p>
        </div>""",
        unsafe_allow_html=True,
    )
