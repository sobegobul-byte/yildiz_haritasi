"""Pydantic veri modelleri — API sozlesmesinin tek kaynagi."""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field


class LocationQuery(BaseModel):
    country: str = "Türkiye"
    province: str = ""          # il
    district: str = ""          # ilce (opsiyonel)


class ResolvedLocation(BaseModel):
    lat: float
    lon: float
    display: str = ""
    timezone_offset_hours: float = 3.0   # TR varsayilani; frontend geocode sonucuyla gunceller


class MapConfig(BaseModel):
    location: ResolvedLocation
    date: str                    # "2026-02-14"
    time: str = "21:00"          # opsiyonel saat, varsayilan aksam
    mag_limit: float = Field(6.0, ge=2.0, le=6.5)
    show_constellations: bool = True


Align = Literal["start", "middle", "end"]   # SVG text-anchor: sol / orta / sag


class TextElement(BaseModel):
    content: str = Field("", max_length=300)
    font_size: float = 20.0      # SVG birimi (px @ 600 genislik)
    align: Align = "middle"
    dx: float = 0.0              # yatay ofset (slot merkezine gore)
    dy: float = 0.0              # dikey ofset
    letter_spacing: float = 0.0
    visible: bool = True


class Personalization(BaseModel):
    title: TextElement = TextElement(content="GÖKYÜZÜ", font_size=40, letter_spacing=6)
    subtitle: TextElement = TextElement(content="tam o anda, tam orada", font_size=16)
    names: TextElement = TextElement(content="", font_size=24)
    coords_text: TextElement = TextElement(content="", font_size=21, letter_spacing=2)
    date_text: TextElement = TextElement(content="", font_size=18, letter_spacing=2)
    message: TextElement = TextElement(content="", font_size=16)
    # ek hizmet: ahsap tabanin on yuzune yazi kazima (+49,90 TL)
    wood_engraving: bool = False
    wood_text: str = Field("", max_length=120)


class PreviewRequest(BaseModel):
    config: MapConfig
    personalization: Personalization = Personalization()
    template_id: str = "yummy-lamp"
    # "mockup" = isikli urun gorunumu (sadece onizleme), "flat" = uretim cizimi
    view: Literal["flat", "mockup"] = "flat"


class ExportRequest(PreviewRequest):
    format: Literal["pdf", "dxf"] = "pdf"
