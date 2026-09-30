"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import LocationForm from "@/components/LocationForm";
import PreviewCanvas from "@/components/PreviewCanvas";
import TextEditor from "@/components/TextEditor";
import ExportBar from "@/components/ExportBar";
import {
  MapConfig, Personalization, PreviewView, emptyEl, fetchPreview,
} from "@/lib/api";

const defaultPersonalization = (): Personalization => ({
  title: emptyEl({ content: "GÖKYÜZÜ", font_size: 40, letter_spacing: 6 }),
  subtitle: emptyEl({ content: "tam o anda, tam orada", font_size: 16 }),
  names: emptyEl({ content: "", font_size: 24 }),
  coords_text: emptyEl({ content: "", font_size: 21, letter_spacing: 2 }),
  date_text: emptyEl({ content: "", font_size: 18, letter_spacing: 2 }),
  message: emptyEl({ content: "", font_size: 16 }),
});

export default function Home() {
  const [config, setConfig] = useState<MapConfig | null>(null);
  const [pers, setPers] = useState<Personalization>(defaultPersonalization());
  const [svg, setSvg] = useState<string>("");
  const [view, setView] = useState<PreviewView>("mockup");
  const [overflow, setOverflow] = useState(false);
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

  return (
    <main className="min-h-screen bg-night text-cream pb-40">
      <header className="px-5 pt-8 pb-4 text-center">
        <p className="text-[11px] tracking-[0.35em] text-starlight/80 uppercase">Yummy Light Store</p>
        <h1 className="mt-1 font-serif text-2xl">Yıldız Haritası Stüdyosu</h1>
        <p className="mt-1 text-sm text-cream/50">O geceyi, o gökyüzünü tasarla</p>
      </header>

      <div className="mx-auto max-w-md px-4 space-y-4 md:max-w-5xl md:grid md:grid-cols-[1fr_380px] md:gap-6 md:space-y-0 md:items-start">
        {/* Önizleme — mobilde üstte yapışkan */}
        <section className="md:order-2 md:sticky md:top-4">
          <PreviewCanvas
            svg={svg} loading={loading} error={error} hasConfig={!!config}
            view={view} onViewChange={setView}
          />
        </section>

        {/* Adımlar sırayla: 1) konum/tarih -> yıldız haritası, 2) kişiselleştirme.
            Harita oluşunca 1. adım tek satıra kapanır, yazarken kaydırma gerekmez. */}
        <section className="space-y-4 md:order-1">
          <LocationForm onResolved={setConfig} />
          {config && <TextEditor pers={pers} onChange={setPers} overflow={overflow} />}
        </section>
      </div>

      {config && <ExportBar config={config} pers={pers} blocked={overflow} />}
    </main>
  );
}
