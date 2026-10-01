/*
 * Yıldız Haritası -> GA4 + Meta Pixel olay iletimi (ikas ürün sayfası)
 *
 * ikas panel: Satış Kanalları → (mağaza) → Eklentiler → Scriptler → Script Ekle
 * Bu dosyanın TAMAMINI <script> ... </script> arasına yapıştır (yer: body sonu).
 *
 * Tasarım aracı (iframe) her adımda üst sayfaya mesaj gönderir; bu script onları
 * ikas'ın zaten yüklediği GA4 (gtag / dataLayer) ve Meta Pixel'e (fbq) iletir.
 * Kişisel veri gönderilmez (lamba yazıları, isim vb. yok).
 * Çerez onayı: GA4 ikas'ın onay moduna uyar; Meta Pixel ikas tarafından ancak onay
 * verilince yüklenir, yüklenmemişse (fbq yoksa) hiçbir şey gönderilmez.
 */
(function () {
  var HARITA_ADRESI = "https://harita.yummylightstore.com";

  // uygulama olayı -> [GA4 olay adı, Meta özel olay adı, Meta standart olay (varsa)]
  var OLAYLAR = {
    open:     ["yildiz_haritasi_acildi",  "YildizHaritasiAcildi"],
    location: ["yildiz_haritasi_konum",   "YildizHaritasiKonum"],
    date:     ["yildiz_haritasi_tarih",   "YildizHaritasiTarih"],
    text:     ["yildiz_haritasi_yazi",    "YildizHaritasiYazi"],
    approved: ["yildiz_haritasi_onay",    "YildizHaritasiOnay", "CustomizeProduct"],
    cart:     ["yildiz_haritasi_sepet",   "YildizHaritasiSepet"]
  };

  function temizle(p) {
    var o = {};
    for (var k in p || {}) {
      var v = p[k];
      if (typeof v === "string") o[k] = v.slice(0, 80);
      else if (typeof v === "number" || typeof v === "boolean") o[k] = v;
    }
    return o;
  }

  window.addEventListener("message", function (e) {
    if (e.origin !== HARITA_ADRESI) return;
    var m = e.data || {};
    if (m.source !== "yildiz-haritasi" || m.type !== "event" || !OLAYLAR[m.name]) return;
    var ad = OLAYLAR[m.name], p = temizle(m.params);
    try {
      if (typeof window.gtag === "function") window.gtag("event", ad[0], p);
      else if (Array.isArray(window.dataLayer)) window.dataLayer.push(Object.assign({ event: ad[0] }, p));
    } catch (err) {}
    try {
      if (typeof window.fbq === "function") {
        window.fbq("trackCustom", ad[1], p);
        if (ad[2]) window.fbq("track", ad[2]);
      }
    } catch (err) {}
  });
})();
