/*
 * Yıldız Haritası Stüdyosu — ikas ürün sayfası entegrasyonu
 *
 * ikas panel: Satış Kanalları → (mağaza) → Eklentiler → Scriptler → Script Ekle
 * Bu dosyanın TAMAMINI <script> ... </script> arasına yapıştır.
 *
 * Ne yapar:
 *  1) Sadece yıldız haritası ürün sayfasında, "Sepete Ekle" düğmesinin bulunduğu
 *     bölümün altına tasarım iframe'ini ekler.
 *  2) Müşteri tasarımı onaylayınca ikas'taki kişiselleştirme alanlarını doldurur:
 *       - "Tasarım No" metin alanı  -> tasarım numarası
 *       - "Ahşap" seçeneği          -> ahşap kazıma seçildiyse işaretlenir (+49,90 TL'yi ikas ekler)
 *     ve sayfayı "Sepete Ekle" düğmesine kaydırır.
 */
(function () {
  var AYAR = {
    // Tünel adresi (sonunda / olmadan). Örn. "https://harita.alanadin.com"
    HARITA_ADRESI: "https://BURAYA-TUNEL-ADRESI",
    // Yıldız haritası ürününün adres yolunda geçen kısım. Örn. "/yildiz-haritasi-gece-lambasi"
    URUN_YOLU: "/BURAYA-URUN-ADRESI",
    // ikas kişiselleştirme alanlarının başlıkları (panelde verdiğin adla aynı olmalı)
    TASARIM_NO_BASLIK: "Tasarım No",
    AHSAP_BASLIK: "Ahşap",
    IFRAME_YUKSEKLIK: "min(100vh, 900px)",
    // Otomatik yer uymazsa: iframe'in içine ekleneceği öğenin CSS seçicisi (örn. "#urun-aciklama")
    YER_SECICI: "",
    // Sepet sayfasının adresi (ikas varsayılanı /cart)
    SEPET_ADRESI: "/cart",
    // Sepete ekleme isteğinin tamamlanması için beklenecek süre (ms), sonra yönlendirilir
    BEKLEME_MS: 2000,
    // Hızlı Satın Al: sepet sayfasında tıklanacak ödeme düğmesinin metninde geçen kelimeler
    ODEME_DUGMESI_METINLERI: ["ödemeye geç", "alışverişi tamamla", "siparişi tamamla", "satın al", "ödeme"],
  };

  var LOG = function () { try { console.log.apply(console, ["[yildiz-haritasi]"].concat([].slice.call(arguments))); } catch (e) {} };

  function urunSayfasiMi() {
    return decodeURIComponent(location.pathname).indexOf(AYAR.URUN_YOLU) !== -1;
  }

  function metinIceren(secici, aranan) {
    aranan = aranan.toLocaleLowerCase("tr");
    return [].slice.call(document.querySelectorAll(secici)).filter(function (el) {
      return (el.textContent || "").toLocaleLowerCase("tr").indexOf(aranan) !== -1;
    });
  }

  function sepeteEkleDugmesi() {
    var d = metinIceren("button", "sepete ekle");
    return d.length ? d[0] : null;
  }

  // React kontrollü input'a değer yazmak için yerel setter + input olayı gerekir
  function degerYaz(input, deger) {
    var proto = input.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, "value").set.call(input, deger);
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }

  // Başlığı verilen kişiselleştirme alanının kutusunu bul (başlığa en yakın input/select)
  function alanBul(baslik, secici) {
    var adaylar = metinIceren("label, span, p, div, h3, h4", baslik)
      .filter(function (el) { return el.children.length <= 2; });   // en içteki başlık öğeleri
    for (var i = 0; i < adaylar.length; i++) {
      var kap = adaylar[i];
      for (var k = 0; k < 4 && kap; k++, kap = kap.parentElement) {
        var el = kap.querySelector(secici);
        if (el) return el;
      }
    }
    return null;
  }

  function ikasAlanlariniDoldur(siparis) {
    var sonuc = { tasarimNo: false, ahsap: !siparis.wood_engraving };

    var metin = alanBul(AYAR.TASARIM_NO_BASLIK, "input[type=text], input:not([type]), textarea");
    if (metin) { degerYaz(metin, siparis.order_id); sonuc.tasarimNo = true; }

    if (siparis.wood_engraving) {
      var kutu = alanBul(AYAR.AHSAP_BASLIK, "input[type=checkbox], input[type=radio]");
      var liste = alanBul(AYAR.AHSAP_BASLIK, "select");
      if (kutu) {
        if (!kutu.checked) kutu.click();
        sonuc.ahsap = true;
      } else if (liste) {
        var secenek = [].slice.call(liste.options).filter(function (o) {
          return /evet|var|ekle|kaz/i.test(o.textContent);
        })[0];
        if (secenek) {
          Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, "value").set.call(liste, secenek.value);
          liste.dispatchEvent(new Event("change", { bubbles: true }));
          sonuc.ahsap = true;
        }
      }
    }
    LOG("alanlar dolduruldu", sonuc);
    return sonuc;
  }

  function bilgiKutusu(kap, siparis, sonuc) {
    var eski = document.getElementById("yh-bilgi");
    if (eski) eski.remove();
    var b = document.createElement("div");
    b.id = "yh-bilgi";
    b.style.cssText = "margin:12px 0;padding:12px 14px;border-radius:10px;font:14px/1.5 system-ui,sans-serif;" +
      (sonuc.tasarimNo && sonuc.ahsap ? "background:#f3faf3;border:1px solid #9ccf9c;color:#1d4d1d"
                                     : "background:#fff6e5;border:1px solid #f0c36d;color:#6b4a00");
    var html = "✓ Tasarımınız onaylandı.";
    if (!sonuc.tasarimNo) html += "<br>Lütfen <b>" + siparis.order_id + "</b> numarasını <b>" + AYAR.TASARIM_NO_BASLIK + "</b> alanına yazın.";
    if (!sonuc.ahsap) html += "<br>Lütfen <b>Ahşap tabana yazı kazıma</b> seçeneğini işaretleyin.";
    html += (sonuc.tasarimNo && sonuc.ahsap) ? "<br>Sepetinize ekleniyor…" : "<br>Ardından <b>Sepete Ekle</b> ile devam edin.";
    b.innerHTML = html;
    kap.parentNode.insertBefore(b, kap);
  }

  function kur() {
    if (!urunSayfasiMi() || document.getElementById("yh-iframe")) return false;
    var dugme = sepeteEkleDugmesi();
    if (!dugme) return false;

    // Yer: Sepete Ekle'nin bulunduğu sütundan yukarı çıkıp, sütunları (görsel + bilgi)
    // içeren satırı bul ve iframe'i o satırın hemen altına tam genişlikte ekle.
    // Mobilde (tek sütun) böyle bir satır yoksa Sepete Ekle'nin altına eklenir.
    var hedef = null, sonra = null;
    if (AYAR.YER_SECICI) {
      hedef = document.querySelector(AYAR.YER_SECICI);
      if (!hedef) return false;
    } else {
      var sutun = dugme, satir = null;
      while (sutun.parentElement && sutun.parentElement !== document.body) {
        var cw = sutun.getBoundingClientRect().width;
        var pw = sutun.parentElement.getBoundingClientRect().width;
        if (cw >= window.innerWidth * 0.3 && pw >= cw * 1.3) { satir = sutun.parentElement; break; }
        sutun = sutun.parentElement;
      }
      sonra = satir || dugme.parentElement;
    }
    var kap = document.createElement("div");
    kap.style.cssText = "width:100%;max-width:1280px;margin:24px auto;padding:0 12px;box-sizing:border-box";
    var iframe = document.createElement("iframe");
    iframe.id = "yh-iframe";
    iframe.src = AYAR.HARITA_ADRESI;
    iframe.title = "Yıldız Haritası Tasarla";
    iframe.style.cssText = "width:100%;height:" + AYAR.IFRAME_YUKSEKLIK + ";border:0;border-radius:16px;display:block;background:#0b1026";
    kap.appendChild(iframe);
    if (hedef) hedef.appendChild(kap);
    else sonra.parentNode.insertBefore(kap, sonra.nextSibling);
    LOG("iframe eklendi");
    return true;
  }

  // Uygulamadaki düğmeler:
  //   action "add-to-cart" -> alanları doldur, ikas Sepete Ekle'ye bas, sepet sayfasına git
  //   action "buy-now"     -> aynısı + sepet sayfasında ödeme düğmesine otomatik bas
  window.addEventListener("message", function (e) {
    if (e.origin !== AYAR.HARITA_ADRESI) return;
    var m = e.data || {};
    if (m.source !== "yildiz-haritasi" || m.type !== "approved" || !m.order) return;
    var sonuc = ikasAlanlariniDoldur(m.order);
    var dugme = sepeteEkleDugmesi();
    if (!dugme) return;
    bilgiKutusu(dugme, m.order, sonuc);
    dugme.scrollIntoView({ behavior: "smooth", block: "center" });
    if (!m.action || !sonuc.tasarimNo || !sonuc.ahsap) return;   // eksik varsa müşteri elle tamamlar

    // React'in alan değişikliklerini işlemesi için kısa bekle, sonra sepete ekle
    setTimeout(function () {
      dugme.click();
      LOG("sepete ekle tıklandı", m.action);
      setTimeout(function () {
        try {
          if (m.action === "buy-now") sessionStorage.setItem("yh-hizli-satin-al", "1");
        } catch (err) {}
        location.href = AYAR.SEPET_ADRESI;
      }, AYAR.BEKLEME_MS);
    }, 300);
  });

  // Hızlı Satın Al: sepet sayfasına gelince ödeme düğmesine bir kez bas
  function odemeyeGec() {
    var bayrak = null;
    try { bayrak = sessionStorage.getItem("yh-hizli-satin-al"); } catch (err) {}
    if (!bayrak || location.pathname.indexOf(AYAR.SEPET_ADRESI) !== 0) return false;
    var adaylar = [].slice.call(document.querySelectorAll("button, a"));
    for (var i = 0; i < AYAR.ODEME_DUGMESI_METINLERI.length; i++) {
      var aranan = AYAR.ODEME_DUGMESI_METINLERI[i];
      var d = adaylar.filter(function (el) {
        return (el.textContent || "").toLocaleLowerCase("tr").indexOf(aranan) !== -1 && el.offsetParent !== null;
      })[0];
      if (d) {
        try { sessionStorage.removeItem("yh-hizli-satin-al"); } catch (err) {}
        LOG("ödeme düğmesine basıldı:", aranan);
        d.click();
        return true;
      }
    }
    return false;
  }
  setInterval(odemeyeGec, 700);

  // ikas sayfaları sonradan yüklenir ve sayfa geçişleri JS ile olur (SPA):
  // ürün sayfasına her gelindiğinde iframe'i ekle (zaten varsa hiçbir şey yapmaz)
  setInterval(kur, 700);
  kur();
})();
