"""
Urun sablonu ve SVG yerlesim sistemi.
Sablon geometrisi tek yerde tanimlidir; onizleme, PDF ve DXF ayni geometriden uretilir.
Birimler: SVG kullanici birimi. classic-portrait: 600 x 900 (2:3 oran, 20x30 cm baskiya birebir).
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field


@dataclass
class TextSlot:
    x: float
    y: float


@dataclass
class Template:
    id: str
    name: str
    width: float
    height: float
    # yildiz dairesi
    circle_cx: float
    circle_cy: float
    circle_r: float
    # fiziksel baski boyutu (mm) — PDF/DXF olceklemesi icin
    print_w_mm: float
    print_h_mm: float
    # yildiz alaninin alt kirisi (template birimi, y): None = tam daire
    chord_y: float | None = None
    # kesim konturu: "rect" (dikdortgen) | "lamp" (Yummy lamba profili)
    shape: str = "rect"
    bg_color: str = "#0b1026"        # gece mavisi
    fg_color: str = "#f5f1e6"        # sicak beyaz (ahsap uzeri lazer gravur hissi)
    star_color: str = "#f5f1e6"
    line_color: str = "#8a93b8"
    slots: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Yummy lamba kesim geometrisi — musteri sablonundan (yıldzsablon.svg) 1:1 mm.
# Siyah cizgi = kesim, mavi daire (r=70, alti kirisle kesik) = yildiz alani.
# Daire altinda yuvarlak uclu omuz cubugu, ortasinda LED tabana giren tirnak.
# ---------------------------------------------------------------------------
LAMP_MM = {
    "W": 143.5, "H": 155.0,
    "outer_cx": 71.75, "outer_cy": 71.75, "outer_r": 71.75,   # kesim dairesi
    "star_cx": 71.75, "star_cy": 71.5, "star_r": 70.0,        # yildiz alani (mavi)
    "chord_dy": 31.336,       # yildiz alani alt kirisi (daire merkezinden asagi)
    "bar_top": 140.125, "bar_bot": 144.475,                   # omuz cubugu ust/alt
    "cap_r": 2.175,           # omuz uclarindaki yarim daire yaricapi
    "cap_lx": 22.583, "cap_rx": 120.916,                      # uc yarim daire merkezleri (x)
    "tab_l": 29.752, "tab_r": 113.747,                        # taban tirnagi (y: bar_bot -> H)
}


def _lamp_shoulder_x() -> tuple[float, float]:
    """Kesim dairesinin omuz ust cizgisini kestigi x'ler (mm)."""
    m = LAMP_MM
    dy = m["bar_top"] - m["outer_cy"]
    dx = math.sqrt(m["outer_r"] ** 2 - dy ** 2)
    return m["outer_cx"] - dx, m["outer_cx"] + dx


def lamp_cut_path(k: float) -> str:
    """Kesim konturunun SVG path'i. k = template birimi / mm."""
    m = LAMP_MM
    l1x, r1x = (v * k for v in _lamp_shoulder_x())
    top, bot = m["bar_top"] * k, m["bar_bot"] * k
    clx, crx = m["cap_lx"] * k, m["cap_rx"] * k
    tl, tr, hgt = m["tab_l"] * k, m["tab_r"] * k, m["H"] * k
    R, cr = m["outer_r"] * k, m["cap_r"] * k
    return (
        f"M {r1x:.3f},{top:.3f} "
        f"A {R:.3f} {R:.3f} 0 1 0 {l1x:.3f},{top:.3f} "      # buyuk yay (tepe uzerinden)
        f"L {clx:.3f},{top:.3f} "
        f"A {cr:.3f} {cr:.3f} 0 0 0 {clx:.3f},{bot:.3f} "    # sol omuz ucu (yarim daire)
        f"L {tl:.3f},{bot:.3f} L {tl:.3f},{hgt:.3f} "
        f"L {tr:.3f},{hgt:.3f} L {tr:.3f},{bot:.3f} "
        f"L {crx:.3f},{bot:.3f} "
        f"A {cr:.3f} {cr:.3f} 0 0 0 {crx:.3f},{top:.3f} "    # sag omuz ucu
        "Z"
    )


def lamp_cut_entities_mm() -> list:
    """DXF kesim konturu: mm cinsinden, y YUKARI (DXF ekseni).
    Eleman bicimi: ("line", (x1,y1), (x2,y2)) | ("arc", (cx,cy), r, bas_aci, bit_aci)
    Yaylar DXF kuralinca bas acidan bit aciya SAAT YONU TERSI cizilir."""
    m = LAMP_MM
    H = m["H"]
    l1x, r1x = _lamp_shoulder_x()
    yt, yb = H - m["bar_top"], H - m["bar_bot"]
    cy = H - m["outer_cy"]
    ang = math.degrees(math.atan2(cy - yt, r1x - m["outer_cx"]))  # omuz kesisiminin merkeze acisi
    cap_cy = (yt + yb) / 2.0
    return [
        ("arc", (m["outer_cx"], cy), m["outer_r"], -ang % 360, (180 + ang) % 360),
        ("line", (l1x, yt), (m["cap_lx"], yt)),
        ("arc", (m["cap_lx"], cap_cy), m["cap_r"], 90.0, 270.0),
        ("line", (m["cap_lx"], yb), (m["tab_l"], yb)),
        ("line", (m["tab_l"], yb), (m["tab_l"], 0.0)),
        ("line", (m["tab_l"], 0.0), (m["tab_r"], 0.0)),
        ("line", (m["tab_r"], 0.0), (m["tab_r"], yb)),
        ("line", (m["tab_r"], yb), (m["cap_rx"], yb)),
        ("arc", (m["cap_rx"], cap_cy), m["cap_r"], 270.0, 90.0),
        ("line", (m["cap_rx"], yt), (r1x, yt)),
    ]


def star_area_path(tpl: Template) -> str:
    """Yildiz alani siniri: alttan kirisle kesilmis daire (SVG path)."""
    dy = tpl.chord_y - tpl.circle_cy
    dx = math.sqrt(tpl.circle_r ** 2 - dy ** 2)
    x1, x2 = tpl.circle_cx - dx, tpl.circle_cx + dx
    r = tpl.circle_r
    return (f"M {x1:.3f},{tpl.chord_y:.3f} "
            f"A {r:.3f} {r:.3f} 0 1 1 {x2:.3f},{tpl.chord_y:.3f} Z")


# Template birimi = mm x 4 (574 x 620) — font olcekleri classic ile uyumlu kalsin diye.
_K = 4.0

TEMPLATES: dict[str, Template] = {
    "yummy-lamp": Template(
        id="yummy-lamp",
        name="Yummy Lamba (14.35×15.5 cm)",
        width=LAMP_MM["W"] * _K, height=LAMP_MM["H"] * _K,
        circle_cx=LAMP_MM["star_cx"] * _K,
        circle_cy=LAMP_MM["star_cy"] * _K,
        circle_r=LAMP_MM["star_r"] * _K,
        chord_y=(LAMP_MM["star_cy"] + LAMP_MM["chord_dy"]) * _K,
        shape="lamp",
        print_w_mm=LAMP_MM["W"], print_h_mm=LAMP_MM["H"],
        slots={
            "title":       TextSlot(287, 440),   # 1. satir
            "subtitle":    TextSlot(287, 468),   # 2. satir
            "names":       TextSlot(287, 496),   # 3. satir
            "message":     TextSlot(287, 520),   # 4. satir (mesaj)
            "date_text":   TextSlot(287, 538),
            "coords_text": TextSlot(287, 558),   # koordinat her zaman en altta
        },
    ),
    "classic-portrait": Template(
        id="classic-portrait",
        name="Klasik Dikey (20×30)",
        width=600, height=900,
        circle_cx=300, circle_cy=300, circle_r=240,
        print_w_mm=200, print_h_mm=300,
        slots={
            "title":       TextSlot(300, 620),
            "subtitle":    TextSlot(300, 655),
            "names":       TextSlot(300, 705),
            "coords_text": TextSlot(300, 745),
            "date_text":   TextSlot(300, 772),
            "message":     TextSlot(300, 820),
        },
    ),
}


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def resolve_text_positions(tpl: Template, personalization) -> dict:
    """Her metin alaninin efektif konumu {key: (x, y)}.
    Lamba sablonunda TUM dolu satirlar (1-4, tarih, koordinat — bu sirayla,
    koordinat her zaman en altta) kiris ile omuz arasindaki banda dikeyde
    ortalanarak dagitilir. Banda sigmazsa satir araliklari oransal daralir.
    Onizleme ve DXF ayni fonksiyonu kullanir."""
    pos = {k: (s.x, s.y) for k, s in tpl.slots.items()}
    if tpl.chord_y is None:
        return pos

    flow = [k for k in ("title", "subtitle", "names", "message",
                        "date_text", "coords_text") if k in tpl.slots]
    items = []
    for k in flow:
        el = getattr(personalization, k)
        if not el.visible or not el.content.strip():
            continue
        n_lines = len(el.content.split("\n"))
        items.append((k, el.font_size, el.font_size * 1.35 * n_lines))
    if not items:
        return pos

    top = tpl.chord_y + 8
    bottom = LAMP_MM["bar_top"] * _K - 6 if tpl.shape == "lamp" else tpl.height - 8
    band = bottom - top

    total = sum(h for _, _, h in items)
    squeeze = min(1.0, band / total) if total > 0 else 1.0   # sigmazsa daralt
    y = top + max(0.0, (band - total * squeeze) / 2.0)
    for k, fs, h in items:
        pos[k] = (tpl.slots[k].x, y + fs)   # ilk satirin taban cizgisi
        y += h * squeeze
    return pos


def render_text_layer(tpl: Template, personalization) -> str:
    """Kisisellestirme metinlerini slotlara yerlestirir."""
    parts = []
    positions = resolve_text_positions(tpl, personalization)
    for key, (sx, sy) in positions.items():
        el = getattr(personalization, key)
        if not el.visible or not el.content.strip():
            continue
        x = sx + el.dx
        y = sy + el.dy
        ls = f' letter-spacing="{el.letter_spacing}"' if el.letter_spacing else ""
        # cok satirli mesaj destegi
        lines = el.content.split("\n")
        if len(lines) == 1:
            parts.append(
                f'<text x="{x}" y="{y}" text-anchor="{el.align}" '
                f'font-size="{el.font_size}" fill="{tpl.fg_color}" '
                f'font-family="Georgia, \'Times New Roman\', serif"{ls}>{_esc(el.content)}</text>'
            )
        else:
            tspans = "".join(
                f'<tspan x="{x}" dy="{0 if i == 0 else el.font_size * 1.35}">{_esc(ln)}</tspan>'
                for i, ln in enumerate(lines)
            )
            parts.append(
                f'<text x="{x}" y="{y}" text-anchor="{el.align}" '
                f'font-size="{el.font_size}" fill="{tpl.fg_color}" '
                f'font-family="Georgia, \'Times New Roman\', serif"{ls}>{tspans}</text>'
            )
    return "\n".join(parts)


def compose_svg(tpl: Template, star_layer_svg: str, personalization) -> str:
    """Tam kompoze SVG: arkaplan + yildiz alani (clip'li) + dekor + metinler."""
    text_layer = render_text_layer(tpl, personalization)

    # yildiz alani: tam daire ya da alttan kirisle kesilmis daire
    if tpl.chord_y is not None:
        area = star_area_path(tpl)
        clip_shape = f'<path d="{area}"/>'
        star_bg = f'<path d="{area}" fill="#070b1d"/>'
        frame = (f'<path d="{area}" fill="none" stroke="{tpl.fg_color}" '
                 f'stroke-width="1.6" opacity="0.85"/>')
    else:
        circ = f'cx="{tpl.circle_cx}" cy="{tpl.circle_cy}" r="{tpl.circle_r}"'
        clip_shape = f'<circle {circ}/>'
        star_bg = f'<circle {circ} fill="#070b1d"/>'
        frame = (f'<circle {circ} fill="none" stroke="{tpl.fg_color}" stroke-width="2"/>'
                 f'<circle cx="{tpl.circle_cx}" cy="{tpl.circle_cy}" r="{tpl.circle_r + 8}"'
                 f' fill="none" stroke="{tpl.fg_color}" stroke-width="0.6" opacity="0.5"/>'
                 f'<line x1="{tpl.width * 0.3}" y1="580" x2="{tpl.width * 0.7}" y2="580"'
                 f' stroke="{tpl.fg_color}" stroke-width="0.8" opacity="0.6"/>')

    # arkaplan: lamba sablonunda urunun kesim konturu, digerlerinde tam dikdortgen
    if tpl.shape == "lamp":
        outline = lamp_cut_path(tpl.width / tpl.print_w_mm)
        background = (f'<path d="{outline}" fill="{tpl.bg_color}"/>'
                      f'<path d="{outline}" fill="none" stroke="{tpl.fg_color}"'
                      f' stroke-width="1" opacity="0.35"/>')
    else:
        background = f'<rect width="{tpl.width}" height="{tpl.height}" fill="{tpl.bg_color}"/>'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {tpl.width} {tpl.height}"
     width="{tpl.width}" height="{tpl.height}">
  <defs>
    <clipPath id="starArea">
      {clip_shape}
    </clipPath>
  </defs>

  <!-- arkaplan / urun konturu -->
  {background}

  <!-- yildiz haritasi: SADECE yildiz alani icinde gorunur -->
  <g clip-path="url(#starArea)">
    {star_bg}
    {star_layer_svg}
  </g>

  <!-- yildiz alani cercevesi -->
  {frame}

  <!-- kisisellestirme metin katmani -->
  {text_layer}
</svg>'''
