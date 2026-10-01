# Yıldız Haritası Stüdyosu — Başka Bilgisayara Kurulum

## 1) Gerekli programlar (bir kez kurulur)

1. **Python 3.10 veya üzeri** — https://www.python.org/downloads/
   - Kurulumda **"Add Python to PATH"** kutusunu MUTLAKA işaretleyin.
2. **Node.js 18 veya üzeri (LTS)** — https://nodejs.org/
   - Varsayılan ayarlarla "İleri, İleri" kurun.

## 2) Projeyi kopyalayın

`starmap-studio` klasörünü (bu klasörü) USB/paylaşım ile yeni bilgisayara
kopyalayın. Örn: `C:\StarMap\starmap-studio`

## 3) Tünel programı (bir kez, sitede iframe için)

Başlat menüsünde **cmd** açıp şunu yazın:

```
winget install --id Cloudflare.cloudflared
```

## 4) Çalıştırın

Proje klasöründeki **baslat.bat** dosyasına çift tıklayın. Pencere sırayla:

1. İlk seferde Python ortamını ve Node paketlerini kurar (birkaç dakika, internet gerekir),
2. Siteyi derler,
3. Backend ve siteyi küçültülmüş iki pencerede başlatır,
4. cloudflared kuruluysa tüneli açar: `https://xxxx.trycloudflare.com` adresi bu pencerede görünür.

- Bu adres her başlatmada **değişir**; ikas'taki `YUMMY_STARMAP_URL` adresini güncellemek gerekir.
  Kalıcı adres için proje klasörüne içinde tünel adı yazan **tunel-adi.txt** koyun (bkz. IFRAME-KURULUM.md).
- Kapatmak için: bu pencereyi ve görev çubuğundaki **Yildiz Backend** ile **Yildiz Site** pencerelerini kapatın.
- Siparişler: `backend\orders\pending`, `cart`, `completed` klasörleri.
- Bilgisayar uykuya geçerse site de durur: Ayarlar → Sistem → Güç → uyku: **Hiçbir zaman**.

## Sık sorunlar

- **"python tanınmıyor"**: Python kurulumunda PATH işaretlenmemiş.
  Python'u kaldırıp "Add Python to PATH" işaretli şekilde yeniden kurun.
- **"npm tanınmıyor"**: Node.js kurulu değil veya bilgisayar yeniden
  başlatılmamış. Node kurup bilgisayarı yeniden başlatın.
- **PDF'te yazı fontu farklı görünüyor**: Windows'ta Georgia fontu yoksa
  Times New Roman kullanılır; görünüm çok az değişir, sorun değildir.
