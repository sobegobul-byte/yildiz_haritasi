# Yıldız Haritası Stüdyosu — Başka Bilgisayara Kurulum

## 1) Gerekli programlar (bir kez kurulur)

1. **Python 3.10 veya üzeri** — https://www.python.org/downloads/
   - Kurulumda **"Add Python to PATH"** kutusunu MUTLAKA işaretleyin.
2. **Node.js 18 veya üzeri (LTS)** — https://nodejs.org/
   - Varsayılan ayarlarla "İleri, İleri" kurun.

## 2) Projeyi kopyalayın

`starmap-studio` klasörünü (bu klasörü) USB/paylaşım ile yeni bilgisayara
kopyalayın. Örn: `C:\StarMap\starmap-studio`

## 3) Bağımlılıkları kurun (bir kez, internet gerekir)

Proje klasöründe adres çubuğuna `cmd` yazıp Enter'a basın, açılan siyah
pencereye sırayla şunları yazın:

```
cd backend
pip install -r requirements.txt
cd ..\frontend
npm install
```

(Birkaç dakika sürebilir.)

## 4) Çalıştırın

Proje klasöründeki **baslat.bat** dosyasına çift tıklayın.
İki siyah pencere açılır ve tarayıcıda http://localhost:3000 açılır.

- Siyah pencereleri kapatırsanız site durur; tekrar baslat.bat'a tıklayın.
- "Konum bulunamadı / sunucuya ulaşılamıyor" derse: baslat.bat'ı çalıştırın.

## Sık sorunlar

- **"python tanınmıyor"**: Python kurulumunda PATH işaretlenmemiş.
  Python'u kaldırıp "Add Python to PATH" işaretli şekilde yeniden kurun.
- **"npm tanınmıyor"**: Node.js kurulu değil veya bilgisayar yeniden
  başlatılmamış. Node kurup bilgisayarı yeniden başlatın.
- **PDF'te yazı fontu farklı görünüyor**: Windows'ta Georgia fontu yoksa
  Times New Roman kullanılır; görünüm çok az değişir, sorun değildir.
