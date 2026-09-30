"""
Astronomi hesaplama cekirdegi.
Sabit yildizlar icin: RA/Dec (J2000) -> yerel yildiz zamani -> alt/az -> stereografik projeksiyon.
Harici efemeris gerektirmez; Skyfield'in sabit yildizlar icin yaptigi hesabin dogrudan uygulamasi.
"""
from __future__ import annotations
import math
from datetime import datetime, timezone
from dataclasses import dataclass

D2R = math.pi / 180.0
R2D = 180.0 / math.pi


def julian_date(dt_utc: datetime) -> float:
    """UTC datetime -> Julian Date."""
    y, m = dt_utc.year, dt_utc.month
    d = (dt_utc.day
         + dt_utc.hour / 24.0
         + dt_utc.minute / 1440.0
         + dt_utc.second / 86400.0)
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5


def gmst_deg(jd: float) -> float:
    """Greenwich Mean Sidereal Time (derece)."""
    t = (jd - 2451545.0) / 36525.0
    gmst = (280.46061837
            + 360.98564736629 * (jd - 2451545.0)
            + 0.000387933 * t * t
            - t * t * t / 38710000.0)
    return gmst % 360.0


def lst_deg(jd: float, lon_deg: float) -> float:
    """Yerel yildiz zamani (derece). Dogu boylami pozitif."""
    return (gmst_deg(jd) + lon_deg) % 360.0


def precess_j2000_to_date(ra_deg: float, dec_deg: float, jd: float) -> tuple[float, float]:
    """Basit presesyon duzeltmesi J2000 -> gozlem tarihi (yeterli hassasiyet: ~1')."""
    t = (jd - 2451545.0) / 36525.0
    ra, dec = ra_deg * D2R, dec_deg * D2R
    m = (3.07496 + 0.00186 * t) * 15.0 / 3600.0 * D2R  # rad/yil (RA)
    n = (20.0431 - 0.0085 * t) / 3600.0 * D2R           # rad/yil (Dec)
    years = t * 100.0
    dra = (m + n * math.sin(ra) * math.tan(dec)) * years
    ddec = (n * math.cos(ra)) * years
    return (ra + dra) * R2D, (dec + ddec) * R2D


def altaz(ra_deg: float, dec_deg: float, lat_deg: float, lst_degrees: float) -> tuple[float, float]:
    """RA/Dec -> yukseklik(alt) / azimut(az), derece. Az: kuzeyden saat yonu."""
    ha = (lst_degrees - ra_deg) * D2R  # saat acisi
    lat = lat_deg * D2R
    dec = dec_deg * D2R
    sin_alt = math.sin(dec) * math.sin(lat) + math.cos(dec) * math.cos(lat) * math.cos(ha)
    alt = math.asin(max(-1.0, min(1.0, sin_alt)))
    cos_az = (math.sin(dec) - math.sin(alt) * math.sin(lat)) / (math.cos(alt) * math.cos(lat) + 1e-12)
    az = math.acos(max(-1.0, min(1.0, cos_az)))
    if math.sin(ha) > 0:
        az = 2 * math.pi - az
    return alt * R2D, az * R2D


@dataclass
class Projector:
    """Ortografik projeksiyon: zenit merkezde, ufuk cember kenarinda.
    Gok kuresine uzaktan bakis — ufka yakin yildizlar kenarda sikisir;
    yildiz haritasi urunlerindeki standart gorunum (referans sablonla birebir).
    cx, cy: dairenin merkezi; r: yaricap (SVG birimi)."""
    cx: float
    cy: float
    r: float

    def project(self, alt_deg: float, az_deg: float) -> tuple[float, float] | None:
        if alt_deg < 0:
            return None
        # ortografik: rho = sin(z) = cos(alt); 0 (zenit) .. 1 (ufuk)
        rho = math.cos(alt_deg * D2R)
        theta = az_deg * D2R
        # Gokyuzu haritasi konvansiyonu: kuzey yukarida, dogu SOLDA (yukari bakis)
        x = self.cx - self.r * rho * math.sin(theta)
        y = self.cy - self.r * rho * math.cos(theta)
        return x, y


def compute_sky(stars: list[dict], lines: list[list[list[float]]],
                lat: float, lon: float, dt_utc: datetime,
                proj: Projector, mag_limit: float = 6.0):
    """Katalogdan gorunur yildizlari ve takimyildiz cizgilerini projeksiyonla hesaplar.

    stars: [{ra, dec, mag}, ...]  (J2000, derece)
    lines: takimyildiz cizgileri, her biri [[ra,dec], [ra,dec], ...] polyline
    Donus: (points, polylines)
      points: [(x, y, mag), ...]
      polylines: [[(x,y), (x,y), ...], ...]  (ufuk altinda kalan parcalar atilir)
    """
    jd = julian_date(dt_utc)
    lst = lst_deg(jd, lon)

    points = []
    for s in stars:
        if s["mag"] > mag_limit:
            continue
        ra, dec = precess_j2000_to_date(s["ra"], s["dec"], jd)
        alt, az = altaz(ra, dec, lat, lst)
        p = proj.project(alt, az)
        if p:
            points.append((p[0], p[1], s["mag"]))

    polylines = []
    for line in lines:
        segment = []
        for ra_raw, dec in line:
            ra = ra_raw % 360.0
            ra_p, dec_p = precess_j2000_to_date(ra, dec, jd)
            alt, az = altaz(ra_p, dec_p, lat, lst)
            p = proj.project(alt, az)
            if p:
                segment.append(p)
            else:
                if len(segment) >= 2:
                    polylines.append(segment)
                segment = []
        if len(segment) >= 2:
            polylines.append(segment)
    return points, polylines
