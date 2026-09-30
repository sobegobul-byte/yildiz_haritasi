# ikas kod bileşeni: YildizHaritasiTasarim

ikas Studio'da ürün sayfasına sürükleyip bırakılan bir **bölüm (section)**. İçinde tasarım
iframe'i vardır. Müşteri tasarımı onaylayınca:

1. Ürünün **Tasarım No** kişiselleştirme alanına tasarım numarasını yazar,
2. Ahşap kazıma seçildiyse **Ahşap…** seçeneğini işaretler (onay kutusu veya "Evet/Hayır" listesi),
3. Ürünü **sepete ekler**, sonra müşterinin bastığı düğmeye göre:
   - **Sepete Ekle** → sepet sayfasına (`/cart`, ayarlanabilir)
   - **Hızlı Satın Al** → doğrudan ikas ödeme sayfasına (`getCheckoutUrlFromCartStore`)

ikas'ın kendi mağaza API'si kullanılır (`setTextValue`, `setCheckboxValue`, `addItemToCart`).
Sayfa yapısını tahmin eden bir script yöntemi değildir.

## Kurulum (ikas CLI projende)

```bash
cd ~/ikas-projen                      # ikas.config.json'un olduğu klasör
bash /yol/yildiz_haritasi/ikas-bilesen/kur.sh
```

Script bileşeni ikas CLI ile tanımlar (ayarlar ve metinler), kodu kopyalar, tip kontrolü yapar ve derler.

## Deneme (geliştirme modu)

```bash
npm run dev
```

1. ikas editöründe **Dev Components** panelinden geliştirme sunucusuna bağlan.
2. **Ürün sayfası** şablonuna `YildizHaritasiTasarim` bölümünü ekle (ürün detayının altına).
3. Bölüm ayarlarında **Tasarım adresi (tünel)** alanına tünel adresini yaz
   (örn. `https://xxxx.trycloudflare.com`). **Ürün** alanı ürün sayfasının ürününe bağlı olmalı.
4. Önizlemede tasarla → Sipariş ver → onayla → ürün sepete eklenmeli.

Canlıya almak için: `npx ikas-component publish` (veya `import`) ve editörde yayınla.

## Ürün ayarı (ikas panel → Ürünler → Kişiselleştirme)

| Ad | Tür | Fiyat | Zorunlu |
|---|---|---|---|
| `Tasarım No` | Yazı | 0 | Evet |
| `Ahşap Tabana Yazı Kazıma` | Onay kutusu (veya Evet/Hayır seçimi) | 49,90 | Hayır |

Adları farklı verirsen bölüm ayarlarındaki "seçenek adı" alanlarını ona göre değiştir.
