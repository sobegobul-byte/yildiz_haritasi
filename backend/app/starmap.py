"""Yildiz katalogunu yukler ve yildiz alani SVG katmanini uretir."""
from __future__ import annotations
import json
import math
import hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from .astro import Projector, compute_sky
from .template import Template

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def load_catalog():
    """d3-celestial verisi: stars.6.json (GeoJSON, koordinat = [ra(-180..180), dec])."""
    raw = json.loads((DATA_DIR / "stars.6.json").read_text())
    stars = []
    for f in raw["features"]:
        lon, dec = f["geometry"]["coordinates"]
        stars.append({"ra": lon % 360.0, "dec": dec, "mag": float(f["properties"]["mag"])})

    raw_lines = json.loads((DATA_DIR / "constellations.lines.json").read_text())
    lines = []
    for f in raw_lines["features"]:
        geom = f["geometry"]
        if geom["type"] == "MultiLineString":
            lines.extend(geom["coordinates"])
        elif geom["type"] == "LineString":
            lines.append(geom["coordinates"])
    return stars, lines


def mag_to_radius(mag: float, scale: float = 1.0) -> float:
    """Parlaklik -> nokta yaricapi. mag -1 (Sirius) ~3.2, mag 6 ~0.35."""
    r = 2.6 * math.pow(1.35, -mag) + 0.3
    return max(0.35, min(4.0, r)) * scale


def local_to_utc(date_str: str, time_str: str, tz_offset_hours: float) -> datetime:
    dt_local = datetime.fromisoformat(f"{date_str}T{time_str or '21:00'}")
    return (dt_local - timedelta(hours=tz_offset_hours)).replace(tzinfo=timezone.utc)


def sky_cache_key(lat: float, lon: float, date: str, time: str, mag: float, cons: bool) -> str:
    return hashlib.md5(f"{lat:.4f}|{lon:.4f}|{date}|{time}|{mag}|{cons}".encode()).hexdigest()


_SKY_CACHE: dict[str, str] = {}


def render_star_layer(tpl: Template, lat: float, lon: float,
                      date_str: str, time_str: str, tz_offset: float,
                      mag_limit: float = 5.5, show_constellations: bool = True) -> str:
    """Yildiz alaninin SVG grubunu uretir (clip disinda konumsuz, template icine gomulur)."""
    key = sky_cache_key(lat, lon, date_str, time_str, mag_limit, show_constellations)
    if key in _SKY_CACHE:
        return _SKY_CACHE[key]

    stars, lines = load_catalog()
    proj = Projector(cx=tpl.circle_cx, cy=tpl.circle_cy, r=tpl.circle_r)
    dt_utc = local_to_utc(date_str, time_str, tz_offset)
    points, polylines = compute_sky(stars, lines, lat, lon, dt_utc, proj, mag_limit)

    parts = []
    if show_constellations:
        for pl in polylines:
            d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pl)
            parts.append(f'<path d="{d}" fill="none" stroke="{tpl.line_color}" '
                         f'stroke-width="0.7" opacity="0.55"/>')
    for x, y, mag in points:
        r = mag_to_radius(mag)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{tpl.star_color}"/>')

    svg = f'<g id="starmap">{"".join(parts)}</g>'
    if len(_SKY_CACHE) > 200:
        _SKY_CACHE.clear()
    _SKY_CACHE[key] = svg
    return svg


def get_sky_data(tpl: Template, lat: float, lon: float, date_str: str, time_str: str,
                 tz_offset: float, mag_limit: float = 5.5):
    """DXF export icin ham nokta/cizgi verisi."""
    stars, lines = load_catalog()
    proj = Projector(cx=tpl.circle_cx, cy=tpl.circle_cy, r=tpl.circle_r)
    dt_utc = local_to_utc(date_str, time_str, tz_offset)
    return compute_sky(stars, lines, lat, lon, dt_utc, proj, mag_limit)
