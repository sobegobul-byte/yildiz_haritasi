"""
Export mantigi:
- PDF: reportlab ile dogrudan vektor cizim (cairo/sistem kutuphanesi gerektirmez).
  Onizleme ile ayni geometri: kesim konturu + yildiz alani + yildizlar + metinler.
- DXF: ayni geometri -> ezdxf, 5 katman (CUT / STAR_MAP / CONSTELLATIONS / TEXT / GUIDE).
  DXF koordinatlari mm cinsinden ve Y ekseni ters cevrilir (SVG yukaridan asagi, DXF asagidan yukari).
  Dosya boyutu icin: setup=False, koordinatlar mikron hassasiyetine yuvarlanir.
"""
from __future__ import annotations
import io
import math
import os

import ezdxf

from .template import (Template, lamp_cut_entities_mm, resolve_text_positions)
from .starmap import get_sky_data, mag_to_radius

MM2PT = 72.0 / 25.4


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

_PDF_FONT: str | None = None


def _pdf_font() -> str:
    """Turkce karakter destekli TTF font kaydet (Windows sistem fontlari)."""
    global _PDF_FONT
    if _PDF_FONT:
        return _PDF_FONT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    for name, path in (("Georgia", r"C:\Windows\Fonts\georgia.ttf"),
                       ("TimesNewRoman", r"C:\Windows\Fonts\times.ttf"),
                       ("Arial", r"C:\Windows\Fonts\arial.ttf")):
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                _PDF_FONT = name
                return _PDF_FONT
            except Exception:
                continue
    _PDF_FONT = "Times-Roman"   # son care (Turkce karakterler eksik kalabilir)
    return _PDF_FONT


def _outline_path_pdf(c, tpl: Template):
    """Kesim konturu path'i (PDF koordinatlari: pt, y yukari)."""
    p = c.beginPath()
    if tpl.shape == "lamp":
        first = True
        for ent in lamp_cut_entities_mm():
            if ent[0] == "line":
                (x1, y1), (x2, y2) = ent[1], ent[2]
                if first:
                    p.moveTo(x1 * MM2PT, y1 * MM2PT)
                    first = False
                p.lineTo(x2 * MM2PT, y2 * MM2PT)
            else:
                (cx, cy), r, a1, a2 = ent[1], ent[2], ent[3], ent[4]
                sx = cx + r * math.cos(math.radians(a1))
                sy = cy + r * math.sin(math.radians(a1))
                if first:
                    p.moveTo(sx * MM2PT, sy * MM2PT)
                    first = False
                p.arcTo((cx - r) * MM2PT, (cy - r) * MM2PT,
                        (cx + r) * MM2PT, (cy + r) * MM2PT,
                        a1, (a2 - a1) % 360.0)
        p.close()
    else:
        p.rect(0, 0, tpl.print_w_mm * MM2PT, tpl.print_h_mm * MM2PT)
    return p


def _star_area_path_pdf(c, tpl: Template, u2pt: float):
    """Yildiz alani path'i: daire ya da alttan kirisle kesik daire (pt, y yukari)."""
    p = c.beginPath()
    cx, cy_up = tpl.circle_cx * u2pt, (tpl.height - tpl.circle_cy) * u2pt
    r = tpl.circle_r * u2pt
    if tpl.chord_y is None:
        p.circle(cx, cy_up, r)
        return p
    dyc = tpl.chord_y - tpl.circle_cy
    dxc = math.sqrt(tpl.circle_r ** 2 - dyc ** 2)
    a = math.degrees(math.atan2(dyc, dxc))
    sx = cx + dxc * u2pt
    sy = cy_up - dyc * u2pt
    p.moveTo(sx, sy)
    p.arcTo(cx - r, cy_up - r, cx + r, cy_up + r, -a, (180.0 + 2.0 * a) % 360.0)
    p.close()   # kiris cizgisi
    return p


def build_pdf(tpl: Template, config, personalization) -> bytes:
    """Onizlemeyle birebir ayni gorunumde vektorel PDF (urun provasi)."""
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.colors import HexColor, Color
    from reportlab.pdfbase.pdfmetrics import stringWidth

    u2pt = (tpl.print_w_mm / tpl.width) * MM2PT     # template birimi -> pt
    W, H = tpl.print_w_mm * MM2PT, tpl.print_h_mm * MM2PT

    def X(x: float) -> float:
        return x * u2pt

    def Y(y: float) -> float:
        return (tpl.height - y) * u2pt

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(W, H))
    c.setTitle("Yildiz Haritasi")

    fg = HexColor(tpl.fg_color)

    # 1) urun konturu (arkaplan)
    outline = _outline_path_pdf(c, tpl)
    c.setFillColor(HexColor(tpl.bg_color))
    c.drawPath(outline, stroke=0, fill=1)
    c.setStrokeColor(Color(fg.red, fg.green, fg.blue, alpha=0.35))
    c.setLineWidth(0.25 * MM2PT)
    c.drawPath(_outline_path_pdf(c, tpl), stroke=1, fill=0)

    # 2) yildiz alani zemini
    area = _star_area_path_pdf(c, tpl, u2pt)
    c.setFillColor(HexColor("#070b1d"))
    c.drawPath(area, stroke=0, fill=1)

    # 3) yildizlar + takimyildizlar (alan ile kirpilir)
    points, polylines = get_sky_data(
        tpl, config.location.lat, config.location.lon,
        config.date, config.time, config.location.timezone_offset_hours,
        config.mag_limit)

    c.saveState()
    c.clipPath(_star_area_path_pdf(c, tpl, u2pt), stroke=0, fill=0)
    lc = HexColor(tpl.line_color)
    if config.show_constellations:
        c.setStrokeColor(Color(lc.red, lc.green, lc.blue, alpha=0.55))
        c.setLineWidth(0.7 * u2pt)
        for pl in polylines:
            p = c.beginPath()
            p.moveTo(X(pl[0][0]), Y(pl[0][1]))
            for x, y in pl[1:]:
                p.lineTo(X(x), Y(y))
            c.drawPath(p, stroke=1, fill=0)
    c.setFillColor(HexColor(tpl.star_color))
    for x, y, mag in points:
        c.circle(X(x), Y(y), mag_to_radius(mag) * u2pt, stroke=0, fill=1)
    c.restoreState()

    # 4) yildiz alani cercevesi
    c.setStrokeColor(Color(fg.red, fg.green, fg.blue, alpha=0.85))
    c.setLineWidth(1.6 * u2pt if tpl.chord_y is not None else 2.0 * u2pt)
    c.drawPath(_star_area_path_pdf(c, tpl, u2pt), stroke=1, fill=0)

    # 5) metinler (onizlemeyle ayni konum fonksiyonu)
    font = _pdf_font()
    c.setFillColor(fg)
    for key, (sx0, sy0) in resolve_text_positions(tpl, personalization).items():
        el = getattr(personalization, key)
        if not el.visible or not el.content.strip():
            continue
        fs = el.font_size * u2pt
        cs = el.letter_spacing * u2pt
        for i, line in enumerate(el.content.split("\n")):
            if not line.strip():
                continue
            bx = X(sx0 + el.dx)
            by = Y(sy0 + el.dy + i * el.font_size * 1.35)
            w = stringWidth(line, font, fs) + cs * max(0, len(line) - 1)
            if el.align == "middle":
                bx -= w / 2.0
            elif el.align == "end":
                bx -= w
            t = c.beginText(bx, by)
            t.setFont(font, fs)
            t.setCharSpace(cs)   # 0 dahil her zaman yaz: Tc PDF'te bloklar arasi kalicidir
            t.textOut(line)
            c.drawText(t)

    c.showPage()
    c.save()
    return buf.getvalue()


# ---------------------------------------------------------------------------
# DXF
# ---------------------------------------------------------------------------

LAYERS = {
    "CUT":            {"color": 7},   # siyah/beyaz — kesim (dis cizgi)
    "STAR_MAP":       {"color": 5},   # mavi — yildizlar
    "CONSTELLATIONS": {"color": 5},   # mavi — takimyildiz cizgileri
    "TEXT":           {"color": 1},   # kirmizi — yazilar
    "GUIDE":          {"color": 5},   # mavi — kesilmez, hizalama
}


def build_dxf(tpl: Template, config, personalization) -> bytes:
    sx = tpl.print_w_mm / tpl.width     # SVG birimi -> mm
    sy = tpl.print_h_mm / tpl.height

    def tx(x: float) -> float:
        return round(x * sx, 3)

    def ty(y: float) -> float:
        return round((tpl.height - y) * sy, 3)    # Y eksenini cevir

    doc = ezdxf.new("R2010")            # setup=False: gereksiz stil/cizgi tipi tablolari yok
    doc.header["$INSUNITS"] = 4         # birim: milimetre
    doc.header["$MEASUREMENT"] = 1      # metrik
    msp = doc.modelspace()
    for name, attrs in LAYERS.items():
        doc.layers.add(name, color=attrs["color"])

    # CUT: dis kontur — lamba profili (yay + cizgi) ya da dikdortgen
    if tpl.shape == "lamp":
        for ent in lamp_cut_entities_mm():
            if ent[0] == "line":
                (x1, y1), (x2, y2) = ent[1], ent[2]
                msp.add_line((round(x1, 3), round(y1, 3)),
                             (round(x2, 3), round(y2, 3)),
                             dxfattribs={"layer": "CUT"})
            else:
                (cx, cy), r, a1, a2 = ent[1], ent[2], ent[3], ent[4]
                msp.add_arc(center=(round(cx, 3), round(cy, 3)), radius=round(r, 3),
                            start_angle=round(a1, 4), end_angle=round(a2, 4),
                            dxfattribs={"layer": "CUT"})
    else:
        msp.add_lwpolyline(
            [(0, 0), (tpl.print_w_mm, 0), (tpl.print_w_mm, tpl.print_h_mm), (0, tpl.print_h_mm)],
            close=True, dxfattribs={"layer": "CUT"})

    # GUIDE: yalnizca yildiz alaninin alt kirisi (daire siniri cizilmez — kesim
    # cizgisi yeterli; referans urun dosyalariyla ayni sade gorunum)
    if tpl.chord_y is not None:
        dyc = tpl.chord_y - tpl.circle_cy
        dxc = (tpl.circle_r ** 2 - dyc ** 2) ** 0.5
        msp.add_line((tx(tpl.circle_cx - dxc), ty(tpl.chord_y)),
                     (tx(tpl.circle_cx + dxc), ty(tpl.chord_y)),
                     dxfattribs={"layer": "GUIDE"})

    # Gokyuzu verisi
    points, polylines = get_sky_data(
        tpl, config.location.lat, config.location.lon,
        config.date, config.time, config.location.timezone_offset_hours,
        config.mag_limit)

    # STAR_MAP: yildizlar (yildiz alani icinde kalanlar: daire + varsa alt kiris)
    chord = tpl.chord_y
    for x, y, mag in points:
        dxm = (x - tpl.circle_cx)
        dym = (y - tpl.circle_cy)
        if dxm * dxm + dym * dym > tpl.circle_r ** 2:
            continue
        if chord is not None and y > chord:
            continue
        r_mm = mag_to_radius(mag) * sx
        msp.add_circle((tx(x), ty(y)), max(0.15, round(r_mm, 3)),
                       dxfattribs={"layer": "STAR_MAP"})

    # CONSTELLATIONS: cizgiler (alana kirpilmis kaba yaklasim: disari tasan noktalar atlanir)
    if config.show_constellations:
        r2 = tpl.circle_r ** 2
        for pl in polylines:
            seg = []
            for x, y in pl:
                inside = (x - tpl.circle_cx) ** 2 + (y - tpl.circle_cy) ** 2 <= r2
                if inside and chord is not None and y > chord:
                    inside = False
                if inside:
                    seg.append((tx(x), ty(y)))
                else:
                    if len(seg) >= 2:
                        msp.add_lwpolyline(seg, dxfattribs={"layer": "CONSTELLATIONS"})
                    seg = []
            if len(seg) >= 2:
                msp.add_lwpolyline(seg, dxfattribs={"layer": "CONSTELLATIONS"})

    # TEXT: kisisellestirme yazilari (konumlar onizlemeyle ayni fonksiyondan)
    positions = resolve_text_positions(tpl, personalization)
    for key, (sx0, sy0) in positions.items():
        el = getattr(personalization, key)
        if not el.visible or not el.content.strip():
            continue
        h_mm = round(el.font_size * sy * 0.72, 3)   # SVG font-size -> yaklasik buyuk harf yuksekligi
        align_map = {"start": 0, "middle": 1, "end": 2}  # ezdxf halign: LEFT/CENTER/RIGHT
        x_mm = tx(sx0 + el.dx)
        y_mm = ty(sy0 + el.dy)
        for i, line in enumerate(el.content.split("\n")):
            t = msp.add_text(line, dxfattribs={
                "layer": "TEXT", "height": h_mm, "style": "Standard",
            })
            t.set_placement((x_mm, round(y_mm - i * h_mm * 1.5, 3)),
                            align=ezdxf.enums.TextEntityAlignment(
                                {0: ezdxf.enums.TextEntityAlignment.LEFT,
                                 1: ezdxf.enums.TextEntityAlignment.CENTER,
                                 2: ezdxf.enums.TextEntityAlignment.RIGHT}[align_map[el.align]].value))

    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")
