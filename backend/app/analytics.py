"""Anonim kullanim analizi: tasarim aracindaki adimlar kaydedilir ve ozetlenir.

Kayit: backend/analytics/olaylar-YYYY-MM.jsonl (git'e girmez, bu bilgisayarda kalir)
Kisisel veri tutulmaz: isim/e-posta/IP yok; oturum kimligi tarayicida uretilen rastgele
bir degerdir ve sekme kapaninca yenilenir. Lambaya yazilan metinler kaydedilmez.
"""
from __future__ import annotations
import json
import threading
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal, Union

from pydantic import BaseModel, Field, field_validator

DATA_DIR = Path(__file__).resolve().parent.parent / "analytics"
_lock = threading.Lock()

# Huni adimlari (sirali) ve panelde gorunen adlari
STEPS = [
    ("open", "Uygulamayı açtı"),
    ("location", "Konum seçti"),
    ("date", "Tarih girdi (harita oluştu)"),
    ("text", "Yazı yazdı"),
    ("approved", "Tasarımı onayladı"),
    ("cart", "Sepete ekledi / Hızlı satın al"),
    ("purchase", "Satın aldı (ödeme tamamlandı)"),
]
EventName = Literal["open", "location", "date", "text", "approved", "cart", "purchase"]

OCCASIONS = ["Yıldönümü", "Sevgililer Günü", "Doğum günü", "Evlilik / Nişan",
             "Yeni doğan bebek", "Anma / Özlem", "Mezuniyet", "Diğer"]

Scalar = Union[bool, int, float, str]


class Event(BaseModel):
    name: EventName
    sid: str = Field(..., pattern=r"^[A-Za-z0-9-]{8,40}$")
    mobile: bool = False
    embedded: bool = False
    props: dict[str, Scalar] = Field(default_factory=dict)

    @field_validator("props")
    @classmethod
    def _small(cls, v: dict) -> dict:
        if len(v) > 12:
            raise ValueError("cok fazla alan")
        out = {}
        for k, val in v.items():
            if len(k) > 30:
                raise ValueError("alan adi uzun")
            out[k] = val[:80] if isinstance(val, str) else val
        return out


def record(ev: Event | dict):
    """Olayi aylik dosyaya ekler."""
    data = ev.model_dump() if isinstance(ev, Event) else dict(ev)
    now = datetime.now()
    data["ts"] = now.isoformat(timespec="seconds")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(data, ensure_ascii=False) + "\n"
    with _lock, open(DATA_DIR / f"olaylar-{now:%Y-%m}.jsonl", "a", encoding="utf-8") as f:
        f.write(line)


def _load(since: datetime) -> list[dict]:
    events = []
    if not DATA_DIR.exists():
        return events
    first_month = since.strftime("%Y-%m")
    for f in sorted(DATA_DIR.glob("olaylar-*.jsonl")):
        if f.stem.split("-", 1)[1] < first_month:
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("ts", "") >= since.isoformat(timespec="seconds"):
                events.append(e)
    return events


def _bucket(v, edges: list[tuple[float, str]], default: str) -> str:
    for upper, label in edges:
        if v <= upper:
            return label
    return default


def summary(days: int = 30) -> dict:
    """Panel icin ozet. days=0 -> tum zamanlar."""
    since = datetime.now() - timedelta(days=days) if days > 0 else datetime(2000, 1, 1)
    events = _load(since)

    reached: dict[str, set] = defaultdict(set)        # adim -> oturumlar
    last: dict[str, dict[str, dict]] = defaultdict(dict)  # adim -> oturum -> son props
    mobile: dict[str, bool] = {}
    daily: dict[str, dict[str, set]] = defaultdict(lambda: defaultdict(set))
    for e in events:
        n, sid, p = e.get("name"), e.get("sid"), e.get("props") or {}
        if not n or not sid:
            continue
        reached[n].add(sid)
        last[n][sid] = p
        if n == "open":
            mobile[sid] = bool(e.get("mobile"))
        daily[e["ts"][:10]][n].add(sid)

    # huni: bir adima ulasan oturum, oncekilere de ulasmis sayilir (adim atlanmaz)
    funnel_sets = []
    acc: set = set()
    for key, _ in reversed(STEPS):
        acc = acc | reached.get(key, set())
        funnel_sets.append(acc)
    funnel_sets.reverse()
    funnel = [{"key": k, "label": lbl, "count": len(s)} for (k, lbl), s in zip(STEPS, funnel_sets)]

    # konum: oturum basina son secim
    prov = Counter()
    dist: dict[str, Counter] = defaultdict(Counter)
    for p in last["location"].values():
        pv = p.get("province") or "?"
        prov[pv] += 1
        dist[pv][p.get("district") or "?"] += 1
    provinces = [{"name": k, "count": c,
                  "districts": [{"name": d, "count": n} for d, n in dist[k].most_common(5)]}
                 for k, c in prov.most_common(15)]

    # tarih: oturum basina son harita
    kinds, months, years_ago, to_anniv, occ = Counter(), Counter(), Counter(), Counter(), Counter()
    for p in last["date"].values():
        kinds[p.get("kind", "?")] += 1
        if isinstance(p.get("month"), int):
            months[p["month"]] += 1
        ya = p.get("years_ago")
        if isinstance(ya, (int, float)) and ya >= 0:
            years_ago[_bucket(ya, [(0, "Bu yıl"), (1, "1 yıl"), (5, "2–5 yıl"),
                                   (10, "6–10 yıl"), (25, "11–25 yıl")], "25+ yıl")] += 1
        da = p.get("days_to_anniv")
        if isinstance(da, (int, float)):
            to_anniv[_bucket(da, [(0, "Bugün"), (7, "1–7 gün"), (30, "8–30 gün"),
                                  (90, "31–90 gün")], "90+ gün")] += 1
    # hediye amaci: onay aninda (yoksa harita aninda) secilen
    for sid in reached.get("date", set()) | reached.get("approved", set()):
        p = last["approved"].get(sid) or last["date"].get(sid) or {}
        occ[p.get("occasion") or "Belirtilmedi"] += 1
    other_texts = Counter(p.get("occasion_other", "").strip().lower()
                          for p in list(last["approved"].values()) + list(last["date"].values())
                          if p.get("occasion") == "Diğer" and p.get("occasion_other"))

    month_names = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
                   "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    approved = last["approved"]
    wood = sum(1 for p in approved.values() if p.get("wood"))

    start = since.date() if days > 0 else (min((e["ts"][:10] for e in events), default=None))
    series = []
    if start:
        d = start if not isinstance(start, str) else datetime.fromisoformat(start).date()
        end = datetime.now().date()
        while d <= end:
            k = d.isoformat()
            series.append({"day": k, "open": len(daily[k]["open"]),
                           "approved": len(daily[k]["approved"]),
                           "purchase": len(daily[k]["purchase"])})
            d += timedelta(days=1)

    order = ["Bu yıl", "1 yıl", "2–5 yıl", "6–10 yıl", "11–25 yıl", "25+ yıl"]
    aorder = ["Bugün", "1–7 gün", "8–30 gün", "31–90 gün", "90+ gün"]
    occ_order = OCCASIONS + ["Belirtilmedi"]
    return {
        "days": days,
        "funnel": funnel,
        "provinces": provinces,
        "occasions": [{"name": k, "count": occ[k]} for k in occ_order if occ[k]],
        "occasion_other": [{"name": k, "count": c} for k, c in other_texts.most_common(10)],
        "date_kind": [{"name": {"past": "Geçmiş bir tarih", "future": "Gelecek bir tarih",
                                "today": "Bugün"}.get(k, k), "count": c}
                      for k, c in kinds.most_common()],
        "months": [{"name": month_names[m - 1], "count": months[m]} for m in range(1, 13)],
        "years_ago": [{"name": k, "count": years_ago[k]} for k in order if years_ago[k]],
        "days_to_anniv": [{"name": k, "count": to_anniv[k]} for k in aorder if to_anniv[k]],
        "wood": {"approved": len(approved), "with_wood": wood},
        "devices": {"mobile": sum(mobile.values()), "desktop": len(mobile) - sum(mobile.values())},
        "daily": series,
    }
