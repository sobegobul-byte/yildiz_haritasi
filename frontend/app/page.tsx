"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import LocationForm, { Occasion } from "@/components/LocationForm";
import PreviewCanvas from "@/components/PreviewCanvas";
import TextEditor from "@/components/TextEditor";
import ExportBar from "@/components/ExportBar";
import ReviewPanel from "@/components/ReviewPanel";
import { isEmbedded, notifyParent } from "@/lib/embed";
import { sessionId, track } from "@/lib/track";
import {
  CheckoutAction, MapConfig, OrderSummary, Personalization, PreviewView,
  createOrder, emptyEl, fetchPreview, markOrderInCart,
} from "@/lib/api";

const defaultPersonalization = (): Personalization => ({
  title: emptyEl({ content: "GÖKYÜZÜ", font_size: 40, letter_spacing: 6 }),
  subtitle: emptyEl({ content: "tam o anda, tam orada", font_size: 16 }),
  names: emptyEl({ content: "", font_size: 24 }),
  coords_text: emptyEl({ content: "", font_size: 21, letter_spacing: 2 }),
  date_text: emptyEl({ content: "", font_size: 18, letter_spacing: 2 }),
  message: emptyEl({ content: "", font_size: 16 }),
  wood_engraving: false,
  wood_text: "",
});

// Akış: design (1. ve 2. adım) -> review (3. adım: büyük önizleme + onay) -> approved
type Stage = "design" | "review" | "approved";

export default function Home() {
  const [stage, setStage] = useState<Stage>("design");
  const [order, setOrder] = useState<OrderSummary | null>(null);
  // iframe içinde (web sitesinde) müşteri modu: imalat düğmeleri gizli
  const [embedded, setEmbedded] = useState(false);
  useEffect(() => {
    setEmbedded(isEmbedded());
    track("open", {}, { once: true });
  }, []);
  const [occasion, setOccasion] = useState<Occasion>({ occasion: "", occasion_other: "" });
  const [config, setConfig] = useState<MapConfig | null>(null);
  const [pers, setPersState] = useState<Personalization>(defaultPersonalization());
  // müşteri lamba yazılarından birini ilk kez değiştirdiğinde "yazı yazdı" adımı
  const setPers = useCallback((p: Personalization) => {
    setPersState((prev) => {
      const keys = ["title", "subtitle", "names", "message"] as const;
      if (keys.some((k) => p[k].content !== prev[k].content)) track("text", {}, { once: true });
      return p;
    });
  }, []);
  const [svg, setSvg] = useState<string>("");
  const [view, setView] = useState<PreviewView>("mockup");
  const [overflow, setOverflow] = useState(false);
  const [woodOverflow, setWoodOverflow] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const debounce = useRef<ReturnType<typeof setTimeout>>();

  const refresh = useCallback((cfg: MapConfig, p: Personalization, v: PreviewView) => {
    clearTimeout(debounce.current);
    debounce.current = setTimeout(async () => {
      try {
        setLoading(true);
        setError("");
        const res = await fetchPreview(cfg, p, v);
        setSvg(res.svg);
        setOverflow(res.overflow);
        setWoodOverflow(res.woodOverflow);
      } catch (e: any) {
        setError(e.message || "Bir sorun oluştu");
      } finally {
        setLoading(false);
      }
    }, 350); // yazarken akıcı kalsın diye debounce
  }, []);

  useEffect(() => {
    if (config) refresh(config, pers, view);
  }, [config, pers, view, refresh]);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [stage]);

  // Sipariş ver ancak tasarım üretilebilir durumdaysa açılır
  const orderDisabledReason =
    loading || !svg ? "Önizleme hazırlanıyor…"
    : overflow ? "Lamba yazıları alana sığmıyor"
    : pers.wood_engraving && !pers.wood_text.trim() ? "Ahşap kazıma yazısını girin"
    : woodOverflow ? "Ahşap yazısı alana sığmıyor"
    : "";

  return (
    <main className="min-h-screen bg-night text-cream pb-40">
      <header className="px-5 pt-8 pb-4 text-center">
        <p className="text-[11px] tracking-[0.35em] text-starlight/80 uppercase">Yummy Light Store</p>
        <h1 className="mt-1 font-serif text-2xl">Yıldız Haritası Stüdyosu</h1>
        <p className="mt-1 text-sm text-cream/50">O geceyi, o gökyüzünü tasarla</p>
      </header>

      {stage !== "design" && config && (
        <ReviewPanel
          svg={svg} loading={loading} error={error}
          view={view} onViewChange={setView}
          config={config} pers={pers}
          approved={stage === "approved"}
          onBack={() => setStage("design")}
          order={order}
          onApprove={async () => {
            const o = await createOrder(config, pers, { ...occasion, sid: sessionId() });   // -> orders/pending/<no>
            track("approved", { wood: pers.wood_engraving, occasion: occasion.occasion, occasion_other: occasion.occasion_other });
            setOrder(o);
            setStage("approved");
          }}
          embedded={embedded}
          onCheckout={async (action: CheckoutAction) => {
            if (!order) return;
            // klasör pending -> cart; ağ hatası olsa da müşteri akışı durmasın
            await markOrderInCart(order.order_id, action).catch(() => {});
            track("cart", { action, wood: pers.wood_engraving, occasion: occasion.occasion });
            // ikas tarafı action'a göre sepete ekler: add-to-cart -> /cart, buy-now -> ödeme
            notifyParent("approved", { action, order });
          }}
        />
      )}

      {/* Tasarım adımları onay ekranında da bağlı kalır (gizli): geri dönünce
          1. adımın seçimleri kaybolmaz */}
      <div className={`mx-auto max-w-md px-4 space-y-4 md:max-w-5xl md:grid md:grid-cols-[1fr_380px] md:gap-6 md:space-y-0 md:items-start ${
        stage === "design" ? "" : "hidden md:hidden"
      }`}>
          {/* Önizleme — mobilde üstte */}
          <section className="md:order-2 md:sticky md:top-4">
            <PreviewCanvas
              svg={svg} loading={loading} error={error} hasConfig={!!config}
              view={view} onViewChange={setView}
            />
          </section>

          {/* Adımlar sırayla: 1) konum/tarih -> yıldız haritası, 2) kişiselleştirme.
              Harita oluşunca 1. adım tek satıra kapanır, yazarken kaydırma gerekmez. */}
          <section className="space-y-4 md:order-1">
            <LocationForm onResolved={setConfig} onOccasion={setOccasion} />
            {config && <TextEditor pers={pers} onChange={setPers} overflow={overflow} woodOverflow={woodOverflow} />}
          </section>
      </div>

      {config && stage === "design" && (
        <ExportBar
          config={config} pers={pers} blocked={overflow} woodBlocked={woodOverflow}
          showProductionFiles={!embedded}
          orderDisabledReason={orderDisabledReason}
          onOrder={() => { setView("mockup"); setStage("review"); }}
        />
      )}
    </main>
  );
}
