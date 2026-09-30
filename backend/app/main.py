"""FastAPI uygulamasi. Calistirma: uvicorn app.main:app --reload --port 8000"""
from __future__ import annotations
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .models import LocationQuery, PreviewRequest, ExportRequest
from .template import TEMPLATES, compose_svg, compose_mockup_svg
from .starmap import render_star_layer
from .exporters import build_pdf, build_dxf
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
    return Response(content=svg, media_type="image/svg+xml")


@app.post("/api/export/pdf")
def api_export_pdf(req: ExportRequest):
    tpl = TEMPLATES[req.template_id]
    _compose(req)  # bos koordinat/tarih alanlarini otomatik doldurur
    pdf = build_pdf(tpl, req.config, req.personalization)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="starmap.pdf"'})


@app.post("/api/export/dxf")
def api_export_dxf(req: ExportRequest):
    tpl = TEMPLATES[req.template_id]
    _compose(req)  # otomatik alan doldurma yan etkisi icin
    dxf = build_dxf(tpl, req.config, req.personalization)
    return Response(content=dxf, media_type="application/dxf",
                    headers={"Content-Disposition": 'attachment; filename="starmap.dxf"'})
