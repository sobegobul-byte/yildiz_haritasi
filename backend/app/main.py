"""FastAPI uygulamasi. Calistirma: uvicorn app.main:app --reload --port 8000"""
from __future__ import annotations
import json
import secrets
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .models import LocationQuery, PreviewRequest, ExportRequest
from .template import (TEMPLATES, compose_svg, compose_mockup_svg, layout_text,
                       layout_wood_text)
from .starmap import render_star_layer
from .exporters import build_pdf, build_dxf, build_wood_dxf
from .geocode import geocode, format_coords

app = FastAPI(title="Starmap Studio API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # prod'da frontend domainine daralt
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/templates")
def list_templates():
    return [{"id": t.id, "name": t.name, "width": t.width, "height": t.height}
            for t in TEMPLATES.values()]


@app.post("/api/geocode")
async def api_geocode(q: LocationQuery):
    try:
        res = await geocode(q.country, q.province, q.district)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    res["coords_text"] = format_coords(res["lat"], res["lon"])
    return res


def _compose(req: PreviewRequest, view: str = "flat") -> str:
    tpl = TEMPLATES.get(req.template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")
    c = req.config
    # bos birakilan koordinat/tarih yazilarini otomatik doldur
    p = req.personalization
    if not p.coords_text.content.strip():
        p.coords_text.content = format_coords(c.location.lat, c.location.lon)
    if not p.date_text.content.strip():
        d = datetime.fromisoformat(c.date)
        p.date_text.content = d.strftime("%d.%m.%Y") + (f" • {c.time}" if c.time else "")
    star_layer = render_star_layer(
        tpl, c.location.lat, c.location.lon, c.date, c.time,
        c.location.timezone_offset_hours, c.mag_limit, c.show_constellations)
    if view == "mockup" and tpl.shape == "lamp":
        return compose_mockup_svg(tpl, star_layer, p)
    return compose_svg(tpl, star_layer, p)


@app.post("/api/preview")
def api_preview(req: PreviewRequest):
    svg = _compose(req, req.view)
    # yazi en kucuk boyutta bile sigmiyorsa on yuz musteriyi uyarir
    _, overflow = layout_text(TEMPLATES[req.template_id], req.personalization)
    p = req.personalization
    wood_overflow = p.wood_engraving and layout_wood_text(p.wood_text)[2]
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"X-Text-Overflow": "1" if overflow else "0",
                             "X-Wood-Overflow": "1" if wood_overflow else "0"})


def _reject_overflow(req: ExportRequest):
    """Yazilar en kucuk boyutta bile sigmiyorsa uretim dosyasi verilmez.
    _compose'dan SONRA cagrilir (otomatik tarih/koordinat satirlari dahil olsun)."""
    if layout_text(TEMPLATES[req.template_id], req.personalization)[1]:
        raise HTTPException(status_code=422, detail="Yazılar lamba alanına sığmıyor")


@app.post("/api/export/pdf")
def api_export_pdf(req: ExportRequest):
    tpl = TEMPLATES[req.template_id]
    _compose(req)  # bos koordinat/tarih alanlarini otomatik doldurur
    _reject_overflow(req)
    pdf = build_pdf(tpl, req.config, req.personalization)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="starmap.pdf"'})


@app.post("/api/export/dxf")
def api_export_dxf(req: ExportRequest):
    tpl = TEMPLATES[req.template_id]
    _compose(req)  # otomatik alan doldurma yan etkisi icin
    _reject_overflow(req)
    dxf = build_dxf(tpl, req.config, req.personalization)
    return Response(content=dxf, media_type="application/dxf",
                    headers={"Content-Disposition": 'attachment; filename="starmap.dxf"'})


@app.post("/api/export/wood-dxf")
def api_export_wood_dxf(req: ExportRequest):
    p = req.personalization
    if not p.wood_engraving or not p.wood_text.strip():
        raise HTTPException(status_code=400, detail="Ahşap yazı kazıma seçilmedi")
    if layout_wood_text(p.wood_text)[2]:
        raise HTTPException(status_code=422, detail="Ahşap yazısı alana sığmıyor")
    return Response(content=build_wood_dxf(p), media_type="application/dxf",
                    headers={"Content-Disposition": 'attachment; filename="ahsap-yazi.dxf"'})


# ---------------------------------------------------------------------------
# Siparis: musteri tasarimi onaylayinca uretim dosyalari bu bilgisayara kaydedilir.
# backend/orders/<siparis-no>/ : siparis.json, lamba.pdf, lamba.dxf,
# ahsap-yazi.dxf (varsa), onizleme.svg (musterinin onayladigi urun gorunumu)
# ---------------------------------------------------------------------------
ORDERS_DIR = Path(__file__).resolve().parent.parent / "orders"
WOOD_ENGRAVING_PRICE = 49.90


@app.post("/api/orders")
def api_create_order(req: PreviewRequest):
    tpl = TEMPLATES.get(req.template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")
    mockup = _compose(req, "mockup")          # bos tarih/koordinat satirlarini da doldurur
    p = req.personalization
    if layout_text(tpl, p)[1]:
        raise HTTPException(status_code=422, detail="Yazılar lamba alanına sığmıyor")
    wood = p.wood_engraving and bool(p.wood_text.strip())
    if wood and layout_wood_text(p.wood_text)[2]:
        raise HTTPException(status_code=422, detail="Ahşap yazısı alana sığmıyor")

    now = datetime.now()
    order_id = now.strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(2).upper()
    d = ORDERS_DIR / order_id
    d.mkdir(parents=True, exist_ok=False)

    (d / "onizleme.svg").write_text(mockup, encoding="utf-8")
    (d / "lamba.pdf").write_bytes(build_pdf(tpl, req.config, p))
    (d / "lamba.dxf").write_bytes(build_dxf(tpl, req.config, p))
    if wood:
        (d / "ahsap-yazi.dxf").write_bytes(build_wood_dxf(p))

    extra = WOOD_ENGRAVING_PRICE if wood else 0.0
    summary = {
        "order_id": order_id,
        "created_at": now.isoformat(timespec="seconds"),
        "location": req.config.location.display,
        "lat": req.config.location.lat,
        "lon": req.config.location.lon,
        "date": req.config.date,
        "time": req.config.time,
        "lamp_lines": [el.content for el in (p.title, p.subtitle, p.names, p.message)
                       if el.visible and el.content.strip()],
        "wood_engraving": wood,
        "wood_text": p.wood_text.strip() if wood else "",
        "extra_price": extra,
    }
    (d / "siparis.json").write_text(
        json.dumps({**summary, "request": req.model_dump()}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return summary
