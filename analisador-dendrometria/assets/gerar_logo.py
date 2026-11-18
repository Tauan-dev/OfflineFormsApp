"""Gera logo.png, logo.svg e icone.ico (rode: python assets/gerar_logo.py). Requer Pillow."""
from pathlib import Path
from PIL import Image, ImageDraw

AQUI = Path(__file__).parent
S = 1024  # desenho em alta resolucao


def desenhar(n=S):
    k = n / 1024
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    P = lambda *v: [x * k for x in v]
    d.rounded_rectangle(P(32, 32, 992, 992), radius=210 * k, fill="#0F3D2E")
    d.rounded_rectangle(P(32, 32, 992, 992), radius=210 * k, outline="#1F7A57", width=max(1, int(14 * k)))
    # copa (tres circulos)
    for cx, cy, r, c in [(512, 330, 215, "#2FA36B"), (380, 440, 160, "#27895A"), (645, 440, 160, "#27895A")]:
        d.ellipse(P(cx - r, cy - r, cx + r, cy + r), fill=c)
    d.ellipse(P(512 - 120, 250 - 120, 512 + 120, 250 + 120), fill="#5CC98F")
    # tronco
    d.polygon(P(462, 520, 562, 520, 590, 840, 434, 840), fill="#8A5A33")
    # fita dendrometrica (DAP) em torno do tronco
    d.rounded_rectangle(P(440, 640, 584, 684), radius=22 * k, fill="#F2C94C")
    for x in range(458, 584, 26):
        d.line(P(x, 640, x, 662), fill="#0F3D2E", width=max(1, int(6 * k)))
    # base / barras de classes diamétricas
    for i, h in enumerate([70, 120, 170, 120, 70]):
        x = 262 + i * 100
        d.rounded_rectangle(P(x, 905 - h, x + 70, 905), radius=12 * k, fill="#E8F5EE" if i == 2 else "#9ED8B8")
    return im


img = desenhar()
img.save(AQUI / "logo.png")
img.save(AQUI / "icone.ico", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
desenhar(256).save(AQUI / "logo_256.png")
(AQUI / "logo.svg").write_text('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
<rect x="32" y="32" width="960" height="960" rx="210" fill="#0F3D2E" stroke="#1F7A57" stroke-width="14"/>
<circle cx="512" cy="330" r="215" fill="#2FA36B"/><circle cx="380" cy="440" r="160" fill="#27895A"/>
<circle cx="645" cy="440" r="160" fill="#27895A"/><circle cx="512" cy="250" r="120" fill="#5CC98F"/>
<polygon points="462,520 562,520 590,840 434,840" fill="#8A5A33"/>
<rect x="440" y="640" width="144" height="44" rx="22" fill="#F2C94C"/>
<g fill="#9ED8B8"><rect x="262" y="835" width="70" height="70" rx="12"/><rect x="362" y="785" width="70" height="120" rx="12"/>
<rect x="562" y="785" width="70" height="120" rx="12"/><rect x="662" y="835" width="70" height="70" rx="12"/></g>
<rect x="462" y="735" width="70" height="170" rx="12" fill="#E8F5EE"/></svg>''', encoding="utf-8")
print("ok")
