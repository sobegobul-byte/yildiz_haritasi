"use client";
import { useState } from "react";
import PreviewCanvas from "@/components/PreviewCanvas";
import {
  CheckoutAction, MapConfig, OrderSummary, Personalization, PreviewView, WOOD_ENGRAVING_PRICE, formatTL,
} from "@/lib/api";

// 3. adım: müşteri tasarımı büyük önizlemede kontrol edip onaylar.
// Masaüstünde önizleme solda büyük, özet sağda; mobilde önizleme üstte.
export default function ReviewPanel({
  svg, loading, error, view, onViewChange, config, pers, approved, order, onBack, onApprove,
  embedded, onCheckout,
}: {
  svg: string;
  loading: boolean;
  error: string;
  view: PreviewView;
  onViewChange: (v: PreviewView) => void;
  config: MapConfig;
  pers: Personalization;
  approved: boolean;
  order: OrderSummary | null;   // müşteriye gösterilmez, sadece ikas'a iletilir
  onBack: () => void;
  onApprove: () => Promise<void>;
  embedded: boolean;
  onCheckout: (action: CheckoutAction) => Promise<void>;
}) {
  const [sent, setSent] = useState<CheckoutAction | null>(null);
  const checkout = async (action: CheckoutAction) => {
    setSent(action);
    await onCheckout(action);
    // mağaza sayfası yönlendirmezse (hata vb.) düğmeler tekrar kullanılabilsin
    setTimeout(() => setSent(null), 8000);
  };
  const [checked, setChecked] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const approve = async () => {
    setBusy(true);
    setErr("");
    try {
      await onApprove();
    } catch (e: any) {
      setErr(e.message || "Sipariş oluşturulamadı");
    } finally {
      setBusy(false);
    }
  };
  const [y, m, d] = config.date.split("-");
  const lines = [pers.title, pers.subtitle, pers.names, pers.message]
    .map((el) => el.content.trim())
    .filter(Boolean);
  const wood = pers.wood_engraving && pers.wood_text.trim();

  const row = "flex justify-between gap-4 py-2 border-b border-cream/10 text-sm";

  return (
    <div className="mx-auto max-w-md px-4 space-y-4 md:max-w-6xl md:grid md:grid-cols-[1fr_380px] md:gap-8 md:space-y-0 md:items-start">
      <section className="md:sticky md:top-4">
        <PreviewCanvas
          svg={svg} loading={loading} error={error} hasConfig large
          view={view} onViewChange={onViewChange}
        />
      </section>

      <section className="rounded-2xl border border-cream/10 bg-nightdeep/50 p-5 space-y-4">
        <div className="flex items-center gap-2">
          <span className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold ${
            approved ? "bg-starlight text-night" : "border border-starlight text-starlight"
          }`}>{approved ? "✓" : "3"}</span>
          <h2 className="text-xs tracking-[0.2em] uppercase text-starlight/80">Tasarımı onayla</h2>
        </div>

        <div>
          <div className={row}>
            <span className="text-cream/50">Konum</span>
            <span className="text-right">{config.location.display}</span>
          </div>
          <div className={row}>
            <span className="text-cream/50">Tarih</span>
            <span>{d}.{m}.{y} · {config.time}</span>
          </div>
          <div className={row}>
            <span className="text-cream/50 shrink-0">Lamba yazıları</span>
            <span className="text-right space-y-0.5">
              {lines.length ? lines.map((l, i) => <span key={i} className="block">{l}</span>) : "—"}
            </span>
          </div>
          <div className={row}>
            <span className="text-cream/50 shrink-0">Ahşap kazıma</span>
            <span className="text-right">
              {wood ? (
                <>
                  <span className="block">{pers.wood_text.trim()}</span>
                  <span className="block text-starlight">+{formatTL(WOOD_ENGRAVING_PRICE)}</span>
                </>
              ) : "Yok"}
            </span>
          </div>
        </div>

        {approved ? (
          <div className="space-y-3">
            {/* Tasarım no müşteriye gösterilmez; ikas'a arka planda iletilir */}
            <div className="rounded-xl border border-starlight/40 bg-starlight/10 p-4 text-sm space-y-1">
              <p className="font-medium text-starlight">✓ Tasarımınız onaylandı</p>
              <p className="text-cream/60 text-xs">
                Onaylanan tasarım bu haliyle üretime alınacaktır.
              </p>
            </div>
            <button
              onClick={() => checkout("add-to-cart")}
              disabled={!!sent}
              className="w-full rounded-lg bg-starlight text-night font-semibold py-3 text-sm disabled:opacity-50"
            >
              {sent === "add-to-cart" ? "Sepete ekleniyor…" : "Sepete Ekle"}
            </button>
            <button
              onClick={() => checkout("buy-now")}
              disabled={!!sent}
              className="w-full rounded-lg border border-starlight text-starlight font-semibold py-3 text-sm disabled:opacity-50"
            >
              {sent === "buy-now" ? "Ödeme sayfasına yönlendiriliyor…" : "Hızlı Satın Al"}
            </button>
            {sent && !embedded && (
              <p className="text-[11px] text-cream/40 text-center">
                (Bu sayfa mağaza içinde açılmadığı için yönlendirme yapılmaz — test modu.)
              </p>
            )}
          </div>
        ) : (
          <>
            <label className="flex items-start gap-3 cursor-pointer text-xs text-cream/70 leading-relaxed">
              <input
                type="checkbox"
                checked={checked}
                onChange={(e) => setChecked(e.target.checked)}
                className="mt-0.5 h-4 w-4 shrink-0 accent-[#e8c46a]"
              />
              Tasarımı kontrol ettim. Konum, tarih ve yazıların doğru olduğunu onaylıyorum.
              Onaydan sonra tasarım bu haliyle üretime alınır.
            </label>
            {err && <p className="text-xs text-red-300">{err}</p>}
            <button
              onClick={approve}
              disabled={!checked || loading || busy}
              className="w-full rounded-lg bg-starlight text-night font-medium py-3 text-sm disabled:opacity-40"
            >
              {busy ? "Kaydediliyor…" : "Tasarımı onaylıyorum"}
            </button>
            <button
              onClick={onBack}
              className="w-full rounded-lg border border-cream/15 text-cream/70 py-2.5 text-sm hover:text-cream"
            >
              ← Düzenlemeye dön
            </button>
          </>
        )}
      </section>
    </div>
  );
}
