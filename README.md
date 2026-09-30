# Yıldız Haritası Stüdyosu — Starmap Studio

Yummy Light Store için mobil öncelikli yıldız haritası önizleme + üretim dosyası uygulaması.
Kullanıcı konum ve tarih girer → gerçek gökyüzü hesaplanır → ürün şablonunda canlı önizleme →
kişiselleştirme → PDF (baskı) ve DXF (lazer kesim, 5 katman) export.

## Kurulum

### 1) Backend (Python 3.10+)
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Not: PDF üretimi reportlab ile yapılır (saf Python) — sistem kütüphanesi gerekmez.

### 2) Frontend (Node 18+)
```bash
cd frontend
npm install
npm run dev
```
Tarayıcıda: http://localhost:3000  (API çağrıları otomatik olarak :8000'e yönlenir)

## Mimari özeti
- `backend/app/astro.py` — Julian Date → Yerel Yıldız Zamanı → alt/az → stereografik projeksiyon.
  Sabit yıldızlar için Skyfield ile aynı sonucu veren saf matematik (presesyon düzeltmeli).
  Doğrulandı: Polaris yüksekliği = gözlemci enlemi ✓
- `backend/data/stars.6.json` — d3-celestial yıldız kataloğu (mag ≤ 6, ~5000 yıldız)
- `frontend/lib/tr-il-ilce.json` — 81 il ve 973 ilçe (PTT verisi, [turkey-neighbourhoods](https://github.com/muratgozel/turkey-neighbourhoods), MIT)
- `backend/app/template.py` — şablon geometrisi TEK yerde; önizleme = PDF = DXF (gördüğün = alacağın)
- `backend/app/exporters.py` — DXF katmanları: CUT / STAR_MAP / CONSTELLATIONS / TEXT / GUIDE

## API
```
POST /api/geocode      → il/ilçe → lat/lon (Nominatim + 81 il offline yedek)
POST /api/preview      → kompoze SVG (canlı önizleme)
POST /api/export/pdf   → 20×30 cm vektörel PDF
POST /api/export/dxf   → lazer kesim DXF
GET  /api/templates    → şablon listesi
```

## Yeni şablon ekleme
`backend/app/template.py` içindeki `TEMPLATES` sözlüğüne yeni bir `Template` ekle:
daire konumu/yarıçapı, baskı boyutu (mm) ve metin slotlarını tanımla — frontend otomatik uyum sağlar.

## v2 fikirleri
- Skyfield ile Ay/gezegen konumları
- Birden fazla şablon (yatay, yuvarlak lamba yüzü)
- İlçe autocomplete (TR ilçe listesi)
- Sepete ekle → Shopify entegrasyonu
