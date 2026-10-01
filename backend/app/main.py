"""FastAPI uygulamasi. Calistirma: uvicorn app.main:app --reload --port 8000"""
from __future__ import annotations
import json
import secrets
from datetime import datetime
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .models import LocationQuery, PreviewRequest, ExportRequest
from .template import (TEMPLATES, compose_svg, compose_mockup_svg, layout_text,
                       layout_wood_text)
from .starmap import render_star_layer
from .exporters import build_pdf, build_dxf, build_wood_dxf
from .geocode import geocode, format_coords
from . import ikas_sync

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
# Durum klasorleri (tasarim klasoru durum degistikce tasinir):
#   backend/orders/pending/<no>/    tasarim onaylandi
#   backend/orders/cart/<no>/       musteri sepete ekledi / hizli satin al'a bast
#   backend/orders/completed/<no>/  satin alindi (ikas'ta odeme tamamlaninca otomatik)
# Icerik: siparis.json, lamba.pdf, lamba.dxf, ahsap-yazi.dxf (varsa), onizleme.svg
# ---------------------------------------------------------------------------
ORDERS_DIR = Path(__file__).resolve().parent.parent / "orders"
STATUSES = ("pending", "cart", "completed")
WOOD_ENGRAVING_PRICE = 49.90


def _find_order(order_id: str) -> tuple[str, Path] | None:
    if not order_id.replace("-", "").isalnum():      # yol enjeksiyonuna karsi
        return None
    for st in STATUSES:
        d = ORDERS_DIR / st / order_id
        if d.is_dir():
            return st, d
    return None


def _log_status(d: Path, status: str, **extra):
    f = d / "siparis.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    data["status"] = status
    data.setdefault("history", []).append(
        {"status": status, "at": datetime.now().isoformat(timespec="seconds"), **extra})
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


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
    d = ORDERS_DIR / "pending" / order_id
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
        json.dumps({**summary, "status": "pending", "request": req.model_dump()},
                   ensure_ascii=False, indent=2),
        encoding="utf-8")
    _log_status(d, "pending")
    return summary


class StatusUpdate(BaseModel):
    status: Literal["cart", "completed"]
    action: Literal["add-to-cart", "buy-now", "manual"] = "manual"


def _move_order(order_id: str, status: str, **extra) -> str | None:
    """Tasarim klasorunu durum klasorune tasir; durum yalnizca ileri gider.
    Tasidiysa yeni durumu, tasimadiysa None doner."""
    found = _find_order(order_id)
    if not found:
        return None
    cur, d = found
    if STATUSES.index(status) <= STATUSES.index(cur):
        return None
    target = ORDERS_DIR / status / order_id
    target.parent.mkdir(parents=True, exist_ok=True)
    d.rename(target)
    _log_status(target, status, **extra)
    return status


def _is_local(request: Request) -> bool:
    """Tunel -> Next.js uzerinden gelen istekler x-forwarded-* basligi tasir."""
    return not any(h in request.headers for h in ("x-forwarded-for", "x-forwarded-host"))


@app.post("/api/orders/{order_id}/status")
def api_order_status(order_id: str, body: StatusUpdate, request: Request):
    """Tasarim klasorunu durum klasorune tasir.
    - cart: musterinin tarayicisindan (Sepete Ekle / Hizli Satin Al) gelir.
    - completed: ikas'ta odeme tamamlaninca otomatik (ikas_sync) ya da sadece
      BU bilgisayardan dogrudan (127.0.0.1:8000); tunelden gelen istek reddedilir.
    Durum yalnizca ileri gider: pending -> cart -> completed."""
    found = _find_order(order_id)
    if not found:
        raise HTTPException(status_code=404, detail="Tasarım bulunamadı")
    if body.status == "completed" and not _is_local(request):
        raise HTTPException(status_code=403, detail="Tamamlandı durumu yalnızca yerelden işaretlenir")
    moved = _move_order(order_id, body.status, action=body.action)
    return {"order_id": order_id, "status": moved or _find_order(order_id)[0]}


# ---------------------------------------------------------------------------
# ikas: odemesi tamamlanan siparislerin tasarimlari otomatik completed/'a tasinir
# (backend/ikas-ayar.txt varsa birkac dakikada bir kontrol edilir)
# ---------------------------------------------------------------------------
def _complete_from_ikas(order_id: str, ikas_order: str) -> str | None:
    return _move_order(order_id, "completed", action="ikas-paid", ikas_order=ikas_order)


@app.on_event("startup")
def _start_ikas_sync():
    ikas_sync.start(_complete_from_ikas)


@app.get("/api/ikas/sync")
def api_ikas_sync(request: Request):
    """Simdi kontrol et (yalnizca bu bilgisayardan): http://127.0.0.1:8000/api/ikas/sync"""
    if not _is_local(request):
        raise HTTPException(status_code=403, detail="Yalnızca yerelden")
    return {**ikas_sync.sync_once(_complete_from_ikas),
            "last_run": ikas_sync.state["last_run"],
            "recent": ikas_sync.state["completed"]}
