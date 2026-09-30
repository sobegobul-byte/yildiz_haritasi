# Web sitesine iframe ile ekleme (Mac + Cloudflare Tunnel)

Uygulama senin Mac'inde çalışır, Cloudflare Tunnel ile internete açılır ve web sitene
iframe olarak eklenir. Müşteri tasarımı onaylayınca üretim dosyaları **senin Mac'ine**
kaydedilir ve web sitene bir mesaj gider.

## 1) Bir kez kurulum

1. Homebrew yoksa: https://brew.sh adresindeki komutu Terminal'e yapıştır.
2. Tünel programı:
   ```
   brew install cloudflared
   ```

## 2) Çalıştırma

Proje klasöründeki **`baslat-mac.command`** dosyasına çift tıkla.
(İlk seferde macOS "açılamıyor" derse: dosyaya sağ tık → **Aç** → **Aç**.)

Pencere şunları yapar: bağımlılıkları kurar (ilk sefer), siteyi derler, backend + site +
tüneli başlatır ve Mac'in uyumasını engeller. **Pencere açık kaldığı sürece site yayında.**

## 3) Tünel adresi

- **Geçici (deneme için):** `tunel-adi.txt` yoksa pencerede
  `https://xxxx.trycloudflare.com` gibi bir adres çıkar. Her başlatmada **değişir**.
- **Kalıcı (canlı kullanım için):** alan adın Cloudflare'deyse bir kez:
  ```
  cloudflared tunnel login
  cloudflared tunnel create yildiz-haritasi
  cloudflared tunnel route dns yildiz-haritasi harita.alanadin.com
  ```
  Sonra `~/.cloudflared/config.yml` dosyasını oluştur:
  ```
  tunnel: yildiz-haritasi
  credentials-file: /Users/KULLANICI_ADIN/.cloudflared/<tünel-id>.json
  ingress:
    - hostname: harita.alanadin.com
      service: http://localhost:3000
    - service: http_status:404
  ```
  ve proje klasörüne içinde sadece `yildiz-haritasi` yazan **`tunel-adi.txt`** koy.
  Artık adres hep `https://harita.alanadin.com` olur.

## 4) Web sitene ekleme

`web-sitesi/iframe-ornek.html` dosyası hazır bir örnektir. Özü:

```html
<iframe id="yildiz-haritasi" src="https://harita.alanadin.com"
        style="width:100%;height:100vh;min-height:760px;border:0"></iframe>
<script>
  window.addEventListener("message", function (e) {
    if (e.origin !== "https://harita.alanadin.com") return;
    var m = e.data || {};
    if (m.source === "yildiz-haritasi" && m.type === "approved") {
      // m.order.order_id, m.order.extra_price (ahşap kazıma: 49.90), m.order.lamp_lines ...
      // -> burada sepete ekle / sipariş sayfasına geç
    }
  });
</script>
```

Sayfa iframe içinde açılınca **müşteri modu**ndadır: PDF/DXF düğmeleri gizlenir.
`http://localhost:3000` adresinden kendin açınca imalat düğmeleri görünür.

## 5) Siparişler

Her onay `backend/orders/<tasarım-no>/` klasörüne kaydedilir:

| Dosya | İçerik |
|---|---|
| `siparis.json` | konum, tarih, yazılar, ahşap yazısı, ek ücret |
| `lamba.pdf` | baskı/prova PDF'i |
| `lamba.dxf` | lazer kesim + gravür (akrilik) |
| `ahsap-yazi.dxf` | ahşap taban kazıması (seçildiyse) |
| `onizleme.svg` | müşterinin onayladığı ürün görünümü |

Web sitendeki siparişi, sitenin aldığı **tasarım no** ile bu klasörle eşleştirirsin.

## 6) İsteğe bağlı güvenlik ayarları

`frontend/.env.local` dosyası oluştur (sonraki başlatmada geçerli olur):

```
# Sadece kendi sitenin iframe ile gömebilmesi için
FRAME_ANCESTORS=https://alanadin.com https://www.alanadin.com
# Onay mesajı sadece kendi sitene gitsin
NEXT_PUBLIC_PARENT_ORIGIN=https://alanadin.com
```

## Bilinmesi gerekenler

- Mac kapanırsa, uyku moduna geçerse ya da internet kesilirse site de kapanır.
- Konum koordinatları için OpenStreetMap kullanılır. İnternet yoksa il merkezi kullanılır.

---

# ikas entegrasyonu

Müşteri ürün sayfasında tasarlar → onaylar → ikas'taki **Tasarım No** alanı otomatik dolar
(ahşap kazıma seçildiyse o seçenek de işaretlenir, +49,90 TL'yi ikas ekler) → **Sepete Ekle**.

## 1) Ürün (ikas panel → Ürünler)

"Yıldız Haritası Gece Lambası" ürününe **Kişiselleştirme** ekle:

| Ad | Tür | Fiyat | Zorunlu |
|---|---|---|---|
| `Tasarım No` | Yazı / metin | 0 | **Evet** (tasarım onaylanmadan sepete eklenemez) |
| `Ahşap Tabana Yazı Kazıma` | Seçenek / onay kutusu | **49,90** | Hayır |

Adlar önemli: script alanları bu başlıklardan bulur ("Tasarım No" ve "Ahşap" kelimesi).

## 2) Script (ikas panel → Satış Kanalları → mağaza → Eklentiler → Scriptler → Script Ekle)

`web-sitesi/ikas-script.js` dosyasının tamamını `<script>` ... `</script>` arasına yapıştır ve
en üstteki iki ayarı değiştir:

```js
HARITA_ADRESI: "https://harita.alanadin.com",        // tünel adresin
URUN_YOLU: "/yildiz-haritasi-gece-lambasi",          // ürün sayfası adresindeki kısım
```

## 3) Test

1. Mac'te `baslat-mac.command` çalışıyor olsun, tünel adresi `HARITA_ADRESI` ile aynı olsun.
2. Ürün sayfasını aç: ürün bilgisinin altında tasarım ekranı görünmeli.
3. Tasarla → Sipariş ver → onayla: sayfa Sepete Ekle'ye kayar, Tasarım No dolmuş olur.
4. Sepete ekle → siparişte **Tasarım No** görünür → dosyalar `backend/orders/<Tasarım No>/`.

Tasarım ekranı görünmezse / alan dolmazsa: tarayıcıda F12 → Console'da `[yildiz-haritasi]`
satırlarına bak. Yeri elle seçmek için `YER_SECICI` ayarına bir CSS seçici yazılabilir.
