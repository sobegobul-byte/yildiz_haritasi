"""
Ulke/il/ilce -> koordinat.
Birincil: OpenStreetMap Nominatim (ucretsiz, API anahtari gerektirmez).
Yedek: 81 il merkezinin offline koordinatlari (internet yoksa veya Nominatim yanit vermezse).
"""
from __future__ import annotations
import httpx

TR_PROVINCES = {
    "adana": (37.0000, 35.3213), "adıyaman": (37.7648, 38.2786), "afyonkarahisar": (38.7507, 30.5567),
    "ağrı": (39.7191, 43.0503), "amasya": (40.6499, 35.8353), "ankara": (39.9208, 32.8541),
    "antalya": (36.8969, 30.7133), "artvin": (41.1828, 41.8183), "aydın": (37.8560, 27.8416),
    "balıkesir": (39.6484, 27.8826), "bilecik": (40.1451, 29.9799), "bingöl": (38.8854, 40.4980),
    "bitlis": (38.4001, 42.1095), "bolu": (40.7397, 31.6113), "burdur": (37.7203, 30.2908),
    "bursa": (40.1885, 29.0610), "çanakkale": (40.1553, 26.4142), "çankırı": (40.6013, 33.6134),
    "çorum": (40.5506, 34.9556), "denizli": (37.7765, 29.0864), "diyarbakır": (37.9144, 40.2306),
    "edirne": (41.6818, 26.5623), "elazığ": (38.6810, 39.2264), "erzincan": (39.7500, 39.5000),
    "erzurum": (39.9000, 41.2700), "eskişehir": (39.7767, 30.5206), "gaziantep": (37.0662, 37.3833),
    "giresun": (40.9128, 38.3895), "gümüşhane": (40.4386, 39.5086), "hakkari": (37.5744, 43.7408),
    "hatay": (36.4018, 36.3498), "ısparta": (37.7648, 30.5566), "mersin": (36.8000, 34.6333),
    "istanbul": (41.0082, 28.9784), "izmir": (38.4192, 27.1287), "kars": (40.6013, 43.0975),
    "kastamonu": (41.3887, 33.7827), "kayseri": (38.7312, 35.4787), "kırklareli": (41.7333, 27.2167),
    "kırşehir": (39.1425, 34.1709), "kocaeli": (40.8533, 29.8815), "konya": (37.8667, 32.4833),
    "kütahya": (39.4167, 29.9833), "malatya": (38.3552, 38.3095), "manisa": (38.6191, 27.4289),
    "kahramanmaraş": (37.5858, 36.9371), "mardin": (37.3212, 40.7245), "muğla": (37.2153, 28.3636),
    "muş": (38.9462, 41.7539), "nevşehir": (38.6939, 34.6857), "niğde": (37.9667, 34.6833),
    "ordu": (40.9839, 37.8764), "rize": (41.0201, 40.5234), "sakarya": (40.6940, 30.4358),
    "samsun": (41.2928, 36.3313), "siirt": (37.9333, 41.9500), "sinop": (42.0231, 35.1531),
    "sivas": (39.7477, 37.0179), "tekirdağ": (40.9833, 27.5167), "tokat": (40.3167, 36.5500),
    "trabzon": (41.0015, 39.7178), "tunceli": (39.3074, 39.4388), "şanlıurfa": (37.1591, 38.7969),
    "uşak": (38.6823, 29.4082), "van": (38.4891, 43.4089), "yozgat": (39.8181, 34.8147),
    "zonguldak": (41.4564, 31.7987), "aksaray": (38.3687, 34.0370), "bayburt": (40.2552, 40.2249),
    "karaman": (37.1759, 33.2287), "kırıkkale": (39.8468, 33.5153), "batman": (37.8812, 41.1351),
    "şırnak": (37.4187, 42.4918), "bartın": (41.6344, 32.3375), "ardahan": (41.1105, 42.7022),
    "iğdır": (39.8880, 44.0048), "yalova": (40.6500, 29.2667), "karabük": (41.2061, 32.6204),
    "kilis": (36.7184, 37.1212), "osmaniye": (37.0742, 36.2478), "düzce": (40.8438, 31.1565),
}


def _norm(s: str) -> str:
    """Il adi normalizasyonu: kucuk harf + Turkce karakterleri sadelestir.
    'Kahramanmaraş', 'KAHRAMANMARAS', 'kahramanmaras' hepsi ayni anahtara iner."""
    s = s.strip().lower().replace("i̇", "i")
    return s.translate(str.maketrans("çğıöşü", "cgiosu"))


_PROVINCES_NORM = {_norm(k): v for k, v in TR_PROVINCES.items()}


async def geocode(country: str, province: str, district: str) -> dict:
    q = ", ".join(p for p in [district, province, country] if p.strip())
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            r = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": q, "format": "json", "limit": 1},
                headers={"User-Agent": "starmap-studio/0.1"},
            )
            data = r.json()
            if data:
                return {
                    "lat": float(data[0]["lat"]),
                    "lon": float(data[0]["lon"]),
                    "display": data[0].get("display_name", q),
                    "source": "nominatim",
                }
    except Exception:
        pass

    # Offline yedek: il merkezi (Turkce karakter/buyuk-kucuk harf duyarsiz)
    key = _norm(province)
    if key in _PROVINCES_NORM:
        lat, lon = _PROVINCES_NORM[key]
        return {"lat": lat, "lon": lon, "display": f"{province.title()}, Türkiye", "source": "offline"}

    raise ValueError(f"Konum bulunamadı: {q}")


def format_coords(lat: float, lon: float) -> str:
    ns = "K" if lat >= 0 else "G"
    ew = "D" if lon >= 0 else "B"
    return f"{abs(lat):.4f}°{ns}  {abs(lon):.4f}°{ew}"
