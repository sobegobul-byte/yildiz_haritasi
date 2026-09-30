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


# ---------------------------------------------------------------------------
# Metin yerlesimi: otomatik satir kaydirma + otomatik yazi boyutu.
# Yazilar kesim cizgisinin icinde kalir: lamba sablonunda bant, yildiz alaninin
# alt kirisi ile omuz cubugu arasidir ve genisligi her satirin yuksekligindeki
# kesim dairesi genisligidir (daire asagi indikce daralir).
# Onizleme, PDF ve DXF ayni yerlesimi kullanir.
# ---------------------------------------------------------------------------
TEXT_FLOW = ("title", "subtitle", "names", "message", "date_text", "coords_text")
NO_WRAP = {"date_text", "coords_text"}   # bolunmez; sigmazsa kuculur
MIN_FONT = 13.0          # template birimi; lamba icin ~2.2 mm buyuk harf (lazerde okunur)
TEXT_MARGIN = 22.0       # kesim cizgisine yatay guvenlik payi (~5.5 mm)
LINE_H = 1.22            # satir yuksekligi (font boyutunun kati)
ASCENT, DESCENT = 0.90, 0.24
FIELD_GAP = 0.18         # alanlar arasi ek bosluk (font boyutunun kati)
# Olcum Times-Roman metrikleriyle yapilir; Georgia daha genistir -> guvenli pay
_GEORGIA_FACTOR = 1.15
_TR_ASCII = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


@dataclass
class TextLine:
    key: str
    text: str
    x: float             # yatay merkez
    y: float             # taban cizgisi
    font_size: float
    letter_spacing: float


def text_width(s: str, font_size: float, letter_spacing: float = 0.0) -> float:
    """Satirin tahmini genisligi (template birimi), Georgia icin guvenli tarafta."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    w = stringWidth(s.translate(_TR_ASCII), "Times-Roman", font_size) * _GEORGIA_FACTOR
    return w + letter_spacing * max(0, len(s) - 1)


def _text_band(tpl: Template) -> tuple[float, float]:
    if tpl.chord_y is not None:
        top = tpl.chord_y + 8
        bottom = (LAMP_MM["bar_top"] * _K - 6) if tpl.shape == "lamp" else tpl.height - 8
    else:
        top = tpl.circle_cy + tpl.circle_r + 40
        bottom = tpl.height - 30
    return top, bottom


def available_width(tpl: Template, y_top: float, y_bot: float) -> float:
    """y_top..y_bot yuksekligindeki bir satirin kullanabilecegi genislik."""
    if tpl.shape != "lamp":
        return tpl.width - 2 * TEXT_MARGIN
    R, cy = LAMP_MM["outer_r"] * _K, LAMP_MM["outer_cy"] * _K
    d = max(abs(y_top - cy), abs(y_bot - cy))
    if d >= R:
        return 0.0
    return 2 * math.sqrt(R * R - d * d) - 2 * TEXT_MARGIN


def _line_fits(tpl: Template, ln: "TextLine") -> bool:
    top = ln.y - ASCENT * ln.font_size
    bot = ln.y + DESCENT * ln.font_size
    return text_width(ln.text, ln.font_size, ln.letter_spacing) <= available_width(tpl, top, bot)


def _flow(tpl: Template, fields, scale: float, y0: float) -> tuple[list, float]:
    """Alanlari y0'dan baslayarak yukaridan asagi dizer, kelime kelime kaydirir."""
    cx = tpl.width / 2
    lines: list[TextLine] = []
    y = y0
    for i, (key, el) in enumerate(fields):
        fs = max(MIN_FONT, el.font_size * scale)
        ls = el.letter_spacing * scale
        if i > 0:
            y += fs * FIELD_GAP
        for para in el.content.split("\n"):
            words = [para.strip()] if key in NO_WRAP else para.split()
            cur = ""
            for w in words:
                cand = f"{cur} {w}" if cur else w
                width = available_width(tpl, y, y + (ASCENT + DESCENT) * fs)
                if not cur or text_width(cand, fs, ls) <= width:
                    cur = cand
                else:
                    lines.append(TextLine(key, cur, cx, y + ASCENT * fs, fs, ls))
                    y += fs * LINE_H
                    cur = w
            if cur:
                lines.append(TextLine(key, cur, cx, y + ASCENT * fs, fs, ls))
                y += fs * LINE_H
    return lines, y - y0


def layout_text(tpl: Template, personalization) -> tuple[list, bool]:
    """Kisisellestirme yazilarinin nihai yerlesimi.
    Once satirlar kaydirilir; sigmazsa tum yazilar birlikte orantili kuculur
    (en az MIN_FONT). Bant icinde dikeyde ortalanir. Ikinci deger True ise
    en kucuk boyutta bile sigmadi (musteri yaziyi kisaltmali)."""
    fields = [(k, getattr(personalization, k)) for k in TEXT_FLOW
              if hasattr(personalization, k)]
    fields = [(k, el) for k, el in fields if el.visible and el.content.strip()]
    if not fields:
        return [], False

    top, bottom = _text_band(tpl)
    band = bottom - top
    lines: list[TextLine] = []
    scale = 1.0
    while True:
        # En genis yer bandin tepesi: satirlar orada kaydirilir, sonra dikeyde
        # ortalanir. Ortalanmis hali (asagisi daha dar) tasiyorsa ust hizali kalir.
        lines, h = _flow(tpl, fields, scale, top)
        if h <= band + 0.5:
            shift = (band - h) / 2
            moved = [TextLine(l.key, l.text, l.x, l.y + shift, l.font_size, l.letter_spacing)
                     for l in lines]
            if all(_line_fits(tpl, l) for l in moved):
                return moved, False
            if all(_line_fits(tpl, l) for l in lines):
                return lines, False
        if all(max(MIN_FONT, el.font_size * scale) <= MIN_FONT for _, el in fields):
            # en kucuk boyutta da sigmadi: tasan satirlar cizime HIC konmaz
            # (kesim cizgisi asilmaz); musteri uyarilir, export engellenir
            kept = [l for l in lines
                    if l.y + DESCENT * l.font_size <= bottom and _line_fits(tpl, l)]
            return kept, True
        scale *= 0.96


def render_text_layer(tpl: Template, personalization) -> str:
    """Kisisellestirme metinleri (SVG): otomatik yerlesimden, ortalanmis."""
    lines, _ = layout_text(tpl, personalization)
    parts = []
    for ln in lines:
        ls = f' letter-spacing="{ln.letter_spacing:.2f}"' if ln.letter_spacing else ""
        parts.append(
            f'<text x="{ln.x:.2f}" y="{ln.y:.2f}" text-anchor="middle" '
            f'font-size="{ln.font_size:.2f}" fill="{tpl.fg_color}" '
            f'font-family="Georgia, \'Times New Roman\', serif"{ls}>{_esc(ln.text)}</text>'
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


# ---------------------------------------------------------------------------
# Ahsap taban yazi kazima (ek hizmet): on yuzde 65 x 13 mm alan (taban 16 mm).
# Kisa yazi tek satir; uzun yazi dengeli 2 satira bolunur, boyut otomatik.
# ---------------------------------------------------------------------------
WOOD_MM = {"w": 65.0, "h": 13.0, "base_h": 16.0}
WOOD_FONT_MAX_1 = 8.0      # tek satir en buyuk font (mm) ~5.5 mm buyuk harf
WOOD_FONT_MAX_2 = 5.4      # iki satirda en buyuk font (mm): 2 satir 13 mm'ye sigar
WOOD_FONT_MIN = 3.0        # bunun altinda kazima okunmaz -> tasma
WOOD_ONE_LINE_MIN = 4.5    # tek satir bundan kucuk kalacaksa 2 satira bolunur
WOOD_LINE_H = 1.2
_CAP_MID = 0.35            # satirin gorsel ortasi: taban cizgisinin ~0.35 font ustu


def layout_wood_text(text: str) -> tuple[list, float, bool]:
    """Ahsap yazisi: ([(satir, alan merkezine gore taban cizgisi dy_mm)], font_mm, tasma)."""
    text = " ".join(text.split())
    if not text:
        return [], 0.0, False
    W = WOOD_MM["w"]

    def fit(lines: list[str], fmax: float) -> float:
        widest = max(text_width(ln, 1.0) for ln in lines)   # 1 mm font genisligi
        return min(fmax, W / widest) if widest > 0 else fmax

    lines, fs = [text], fit([text], WOOD_FONT_MAX_1)
    words = text.split()
    if fs < WOOD_ONE_LINE_MIN and len(words) > 1:
        # en dengeli bolme noktasi (uzun satirin en kisa oldugu)
        best = min(range(1, len(words)),
                   key=lambda i: max(text_width(" ".join(words[:i]), 1.0),
                                     text_width(" ".join(words[i:]), 1.0)))
        two = [" ".join(words[:best]), " ".join(words[best:])]
        fs2 = fit(two, WOOD_FONT_MAX_2)
        if fs2 > fs:
            lines, fs = two, fs2
    n = len(lines)
    placed = [(ln, _CAP_MID * fs + (i - (n - 1) / 2) * WOOD_LINE_H * fs)
              for i, ln in enumerate(lines)]
    return placed, fs, fs < WOOD_FONT_MIN


def _wood_text_svg(personalization, cx: float, cy: float, k: float) -> str:
    """Urun gorunumu: tabanin on yuzunde kazinmis yazi (koyu oyuk + alt kenarda isik)."""
    if not getattr(personalization, "wood_engraving", False):
        return ""
    placed, fs, _ = layout_wood_text(personalization.wood_text)
    out = []
    for ln, dy in placed:
        y = cy + dy * k
        common = (f'x="{cx:.2f}" text-anchor="middle" font-size="{fs * k:.2f}" '
                  f'font-family="Georgia, \'Times New Roman\', serif"')
        out.append(f'<text {common} y="{y + 0.7:.2f}" fill="#f6d7a8" opacity="0.35">{_esc(ln)}</text>'
                   f'<text {common} y="{y:.2f}" fill="#4a2810" opacity="0.88">{_esc(ln)}</text>')
    return "<!-- ahsap yazi kazima -->" + "".join(out)


def compose_mockup_svg(tpl: Template, star_layer_svg: str, personalization) -> str:
    """Musteriye gosterilen isikli urun gorunumu (sadece onizleme).
    Ayni kesim/yildiz/metin geometrisi kullanilir; yalnizca gorunum farklidir:
    LED ile aydinlanan akrilik, sicak parlama, ahsap taban ve loş oda ortami.
    Uretim dosyalari (PDF/DXF) bundan etkilenmez."""
    k = tpl.width / tpl.print_w_mm
    outline = lamp_cut_path(k)
    area = star_area_path(tpl)
    text_layer = render_text_layer(tpl, personalization)

    cx = tpl.width / 2
    slot_y = LAMP_MM["bar_bot"] * k + 4          # akrilik tabana bu cizgide girer
    # kayin ahsap LED taban: yuvarlak uclu oval (stadyum), ustte akrilik yarigi.
    # Hafif yukaridan bakis: ust yuzey basik, uclar eliptik gorunur.
    base_l, base_r = 8 * k, (LAMP_MM["W"] - 8) * k
    base_w = base_r - base_l
    end_rx, top_ry = 92, 26                      # uc yarim dairelerin perspektif yaricaplari
    top_y = slot_y - top_ry                      # ust yuzey ust kenari
    side_h = WOOD_MM["base_h"] * k               # taban yan yuzu: gercek 1.6 cm
    front_b = slot_y + side_h + top_ry           # taban alt kenari (en on nokta)
    slot_l, slot_r = LAMP_MM["tab_l"] * k - 16, LAMP_MM["tab_r"] * k + 16
    top_face = (f"M {base_l + end_rx},{top_y} H {base_r - end_rx} "
                f"A {end_rx} {top_ry} 0 0 1 {base_r - end_rx},{slot_y + top_ry} "
                f"H {base_l + end_rx} A {end_rx} {top_ry} 0 0 1 {base_l + end_rx},{top_y} Z")
    side_face = (f"M {base_l},{slot_y} V {slot_y + side_h} "
                 f"A {end_rx} {top_ry} 0 0 0 {base_l + end_rx},{front_b} "
                 f"H {base_r - end_rx} A {end_rx} {top_ry} 0 0 0 {base_r},{slot_y + side_h} "
                 f"V {slot_y} Z")

    # tuval: urunun cevresinde ortam icin bosluk
    vx, vy = -60, -50
    vw, vh = tpl.width + 120, front_b + 90 - vy

    return f'''<svg xmlns="http://www.w3.org/2000/svg" class="lamp-mockup"
     viewBox="{vx} {vy} {vw} {vh}" width="{vw}" height="{vh}">
  <defs>
    <style>
      .lamp-mockup .stars circle {{ fill: #fff6e2; }}
      .lamp-mockup .stars path {{ stroke: #ffe1ad; stroke-width: 1.3; opacity: 0.85; }}
      .lamp-mockup .txt text {{ fill: #fff3dc; }}
    </style>
    <radialGradient id="mRoom" cx="50%" cy="42%" r="75%">
      <stop offset="0" stop-color="#3b2413"/>
      <stop offset="0.45" stop-color="#1c110a"/>
      <stop offset="1" stop-color="#0a0604"/>
    </radialGradient>
    <radialGradient id="mHalo" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="#ffb866" stop-opacity="0.34"/>
      <stop offset="0.6" stop-color="#ff9a3c" stop-opacity="0.10"/>
      <stop offset="1" stop-color="#ff9a3c" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="mAcrylic" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffe6c0" stop-opacity="0.05"/>
      <stop offset="0.7" stop-color="#ffd49a" stop-opacity="0.09"/>
      <stop offset="1" stop-color="#ffc47a" stop-opacity="0.22"/>
    </linearGradient>
    <linearGradient id="mWoodFront" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#8f5f34"/>
      <stop offset="0.3" stop-color="#c38d56"/>
      <stop offset="0.55" stop-color="#d4a068"/>
      <stop offset="0.85" stop-color="#b07a44"/>
      <stop offset="1" stop-color="#83552e"/>
    </linearGradient>
    <linearGradient id="mWoodShade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#000" stop-opacity="0"/>
      <stop offset="1" stop-color="#000" stop-opacity="0.35"/>
    </linearGradient>
    <linearGradient id="mWoodTop" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#c99459"/>
      <stop offset="0.5" stop-color="#ebc08b"/>
      <stop offset="1" stop-color="#c99459"/>
    </linearGradient>
    <radialGradient id="mSlotGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="#ffd08a" stop-opacity="0.75"/>
      <stop offset="1" stop-color="#ffb060" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="mTable" cx="50%" cy="0%" r="100%">
      <stop offset="0" stop-color="#ffb866" stop-opacity="0.22"/>
      <stop offset="1" stop-color="#ffb866" stop-opacity="0"/>
    </radialGradient>
    <filter id="mGlow" x="-5%" y="-5%" width="110%" height="110%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="2.4" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="mEdge" x="-10%" y="-10%" width="120%" height="120%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="mSoft"><feGaussianBlur stdDeviation="18"/></filter>
    <filter id="mGrain" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="0.012 0.35" numOctaves="2" seed="7"/>
      <feColorMatrix values="0 0 0 0 0.35  0 0 0 0 0.19  0 0 0 0 0.07  0 0 0 0.8 -0.38"/>
      <feComposite in2="SourceGraphic" operator="in"/>
    </filter>
    <clipPath id="mStarArea"><path d="{area}"/></clipPath>
    <clipPath id="mAboveSlot"><rect x="{vx}" y="{vy}" width="{vw}" height="{slot_y - vy}"/></clipPath>
  </defs>

  <!-- oda ortami -->
  <rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" fill="url(#mRoom)"/>
  <ellipse cx="{cx}" cy="{tpl.circle_cy}" rx="{tpl.circle_r * 1.55}" ry="{tpl.circle_r * 1.45}" fill="url(#mHalo)"/>
  <!-- masa yuzeyine vuran isik ve golge -->
  <ellipse cx="{cx}" cy="{front_b}" rx="{base_w * 0.85}" ry="70" fill="url(#mTable)"/>
  <ellipse cx="{cx}" cy="{front_b - 4}" rx="{base_w * 0.5}" ry="14" fill="#000" opacity="0.55" filter="url(#mSoft)"/>

  <!-- kayin ahsap taban: yan yuz + ust yuz + akrilik yarigi -->
  <path d="{side_face}" fill="url(#mWoodFront)"/>
  <path d="{side_face}" fill="#000" filter="url(#mGrain)" opacity="0.6"/>
  <path d="{side_face}" fill="url(#mWoodShade)"/>
  <path d="{top_face}" fill="url(#mWoodTop)"/>
  <path d="{top_face}" fill="#000" filter="url(#mGrain)" opacity="0.45"/>
  <path d="{top_face}" fill="none" stroke="#f3d3a6" stroke-width="1" opacity="0.5"/>
  <rect x="{slot_l}" y="{slot_y - 5}" width="{slot_r - slot_l}" height="10" rx="5" fill="#2b170a"/>
  <ellipse cx="{cx}" cy="{slot_y}" rx="{base_w * 0.38}" ry="{top_ry * 1.1}" fill="url(#mSlotGlow)"/>

  {_wood_text_svg(personalization, cx, slot_y + top_ry + side_h / 2, k)}

  <!-- akrilik plaka: tabana giren tirnak gizlenir -->
  <g clip-path="url(#mAboveSlot)">
    <path d="{outline}" fill="url(#mAcrylic)"/>

    <!-- gravur: yildizlar ve takimyildiz cizgileri (LED ile isiyor) -->
    <g class="stars" clip-path="url(#mStarArea)" filter="url(#mGlow)">
      {star_layer_svg}
    </g>
    <path d="{area}" fill="none" stroke="#ffe4b8" stroke-width="1.6" opacity="0.8" filter="url(#mGlow)"/>

    <!-- gravur: kisisellestirme metinleri -->
    <g class="txt" filter="url(#mGlow)">
      {text_layer}
    </g>

    <!-- akrilik kenarlari: LED isigi kenarlarda en parlak -->
    <path d="{outline}" fill="none" stroke="#ffcf8c" stroke-width="3.2" opacity="0.9" filter="url(#mEdge)"/>
    <path d="{outline}" fill="none" stroke="#fff3dc" stroke-width="1" opacity="0.9"/>
  </g>
  <line x1="{LAMP_MM['tab_l'] * k}" y1="{slot_y}" x2="{LAMP_MM['tab_r'] * k}" y2="{slot_y}"
        stroke="#fff0d0" stroke-width="3" opacity="0.9" filter="url(#mEdge)"/>
</svg>'''
