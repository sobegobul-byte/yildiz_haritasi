"""ikas'ta odemesi tamamlanan siparisleri bulup tasarim klasorunu completed/'a tasir.

ikas Admin API (ozel uygulama, client_credentials) ile birkac dakikada bir son
siparisler okunur; siparis satirindaki "Tasarim No" degeri bizim tasarim numaramizdir.
Ayar dosyasi: backend/ikas-ayar.txt (git'e girmez)
    MAGAZA=magazaadi            (magazaadi.myikas.com)
    CLIENT_ID=...
    CLIENT_SECRET=...
Dosya yoksa hicbir sey yapilmaz.
"""
from __future__ import annotations
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

import httpx

CONFIG_FILE = Path(__file__).resolve().parent.parent / "ikas-ayar.txt"
GRAPHQL_URL = "https://api.myikas.com/api/v1/admin/graphql"
INTERVAL_S = 120                 # kac saniyede bir kontrol edilir
LOOKBACK_DAYS = 30               # bu kadar gun icindeki siparislere bakilir
PAID = ("PAID", "OVER_PAID")
ORDER_ID_RE = re.compile(r"\b\d{8}-\d{6}-[0-9A-F]{4}\b")   # 20260101-123045-AB12

QUERY = """
query ($since: Timestamp, $page: Int) {
  listOrder(
    orderedAt: { gte: $since }
    orderPaymentStatus: { in: [PAID, OVER_PAID] }
    pagination: { page: $page, limit: 50 }
    sort: "-orderedAt"
  ) {
    hasNext
    data {
      id
      orderNumber
      orderPaymentStatus
      status
      orderLineItems { options { name values { value } } }
    }
  }
}
"""

state = {"enabled": False, "last_run": None, "last_error": None, "completed": []}
_token: dict = {"value": None, "exp": 0.0}


def _config() -> dict | None:
    if not CONFIG_FILE.exists():
        return None
    cfg = {}
    for line in CONFIG_FILE.read_text(encoding="utf-8-sig").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            cfg[k.strip().upper()] = v.strip()
    if not all(cfg.get(k) for k in ("MAGAZA", "CLIENT_ID", "CLIENT_SECRET")):
        return None
    cfg["MAGAZA"] = cfg["MAGAZA"].replace("https://", "").split(".myikas.com")[0].strip("/")
    return cfg


def _access_token(cfg: dict, client: httpx.Client) -> str:
    if _token["value"] and time.time() < _token["exp"] - 60:
        return _token["value"]
    r = client.post(f"https://{cfg['MAGAZA']}.myikas.com/api/admin/oauth/token",
                    data={"grant_type": "client_credentials",
                          "client_id": cfg["CLIENT_ID"],
                          "client_secret": cfg["CLIENT_SECRET"]})
    if r.status_code != 200:
        raise RuntimeError(f"ikas giris hatasi ({r.status_code}): {r.text[:200]}")
    data = r.json()
    _token["value"] = data["access_token"]
    _token["exp"] = time.time() + float(data.get("expires_in", 3600))
    return _token["value"]


def _paid_orders(cfg: dict, client: httpx.Client):
    since = int((time.time() - LOOKBACK_DAYS * 86400) * 1000)    # ikas Timestamp = ms
    page = 1
    while True:
        r = client.post(GRAPHQL_URL,
                        json={"query": QUERY, "variables": {"since": since, "page": page}},
                        headers={"Authorization": f"Bearer {_access_token(cfg, client)}"})
        body = r.json()
        if r.status_code != 200 or body.get("errors"):
            raise RuntimeError(f"ikas siparis sorgusu hatasi ({r.status_code}): "
                               f"{str(body.get('errors') or body)[:300]}")
        res = body["data"]["listOrder"]
        yield from res["data"]
        if not res.get("hasNext") or page >= 20:
            break
        page += 1


def design_numbers(order: dict) -> set[str]:
    """Siparis satirlarindaki kisisellestirme degerlerinden tasarim numaralari."""
    found = set()
    for line in order.get("orderLineItems") or []:
        for opt in line.get("options") or []:
            for v in opt.get("values") or []:
                found.update(ORDER_ID_RE.findall(str(v.get("value", "")).upper()))
    return found


def sync_once(move: Callable[..., str | None]) -> dict:
    """Bir kez kontrol eder. move(tasarim_no, ikas_siparis_no) -> yeni durum ya da None."""
    cfg = _config()
    state["enabled"] = cfg is not None
    if not cfg:
        return {"enabled": False, "info": f"{CONFIG_FILE.name} yok ya da eksik"}
    moved = []
    try:
        with httpx.Client(timeout=30) as client:
            for order in _paid_orders(cfg, client):
                if order.get("orderPaymentStatus") not in PAID:
                    continue
                for no in design_numbers(order):
                    if move(no, order.get("orderNumber") or order.get("id")):
                        moved.append({"design": no, "ikas_order": order.get("orderNumber")})
        state["last_error"] = None
    except Exception as e:                       # ag/yetki hatasi: bir sonraki turda tekrar
        state["last_error"] = str(e)
    state["last_run"] = datetime.now().isoformat(timespec="seconds")
    state["completed"] = (moved + state["completed"])[:50]
    if moved:
        print(f"[ikas] tamamlandi olarak isaretlendi: {moved}", flush=True)
    if state["last_error"]:
        print(f"[ikas] {state['last_error']}", flush=True)
    return {"enabled": True, "moved": moved, "error": state["last_error"]}


def start(move: Callable[..., str | None]):
    def loop():
        while True:
            sync_once(move)
            time.sleep(INTERVAL_S)
    threading.Thread(target=loop, name="ikas-sync", daemon=True).start()
