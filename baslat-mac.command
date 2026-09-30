#!/bin/bash
# Yıldız Haritası Stüdyosu — Mac başlatıcı (çift tıkla).
# Backend + frontend (üretim modu) + varsa Cloudflare tüneli başlatır.
# Kapatmak için bu pencerede Ctrl+C'ye bas ya da pencereyi kapat.
set -e
cd "$(dirname "$0")"
ROOT="$(pwd)"

echo "== Yıldız Haritası Stüdyosu =="

# 1) Backend bağımlılıkları (ilk seferde kurulur)
if [ ! -d backend/.venv ]; then
  echo "-> Python ortamı kuruluyor (ilk sefer)..."
  python3 -m venv backend/.venv
  backend/.venv/bin/pip install -q -r backend/requirements.txt
fi

# 2) Frontend bağımlılıkları + üretim derlemesi (güncellemeler her başlatmada derlenir)
cd frontend
if [ ! -d node_modules ]; then
  echo "-> Node paketleri kuruluyor (ilk sefer)..."
  npm install --no-audit --no-fund
fi
echo "-> Site derleniyor..."
npm run build > /dev/null
cd "$ROOT"

# Pencere kapanınca hepsini durdur
PIDS=()
cleanup() { echo; echo "Durduruluyor..."; kill "${PIDS[@]}" 2>/dev/null; exit 0; }
trap cleanup INT TERM EXIT

# 3) Sunucular (backend yalnızca bu bilgisayardan erişilebilir: 127.0.0.1)
backend/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend &
PIDS+=($!)
(cd frontend && npx next start -p 3000) &
PIDS+=($!)

# Mac uyku moduna geçmesin (site açık kaldığı sürece)
caffeinate -i -w $$ &
PIDS+=($!)

sleep 3
echo
echo "Site hazır: http://localhost:3000"
echo "Siparişler: $ROOT/backend/orders/"

# 4) Tünel: cloudflared kuruluysa. 'tunel-adi.txt' varsa kalıcı tünel, yoksa geçici adres.
if command -v cloudflared > /dev/null; then
  if [ -f tunel-adi.txt ]; then
    NAME="$(tr -d '[:space:]' < tunel-adi.txt)"
    echo "-> Kalıcı tünel başlatılıyor: $NAME"
    cloudflared tunnel run "$NAME" &
  else
    echo "-> Geçici tünel başlatılıyor (adres aşağıda 'trycloudflare.com' ile biter)"
    cloudflared tunnel --url http://localhost:3000 &
  fi
  PIDS+=($!)
else
  echo "(cloudflared kurulu değil — tünel başlatılmadı. Kurulum: brew install cloudflared)"
fi

wait
