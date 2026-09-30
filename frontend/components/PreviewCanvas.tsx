"use client";
import type { PreviewView } from "@/lib/api";

const VIEWS: { id: PreviewView; label: string }[] = [
  { id: "mockup", label: "Ürün görünümü" },
  { id: "flat", label: "Üretim çizimi" },
];

export default function PreviewCanvas({
  svg, loading, error, hasConfig, view, onViewChange, large = false,
}: {
  svg: string;
  loading: boolean;
  error: string;
  hasConfig: boolean;
  view: PreviewView;
  onViewChange: (v: PreviewView) => void;
  large?: boolean;   // onay ekranı: masaüstünde ekran yüksekliğine sığacak kadar büyük
}) {
  return (
    <div className="relative rounded-2xl border border-cream/10 bg-nightdeep/50 p-3">
      <div className="flex items-center justify-between gap-2 px-1 pb-2">
        <h2 className="text-xs tracking-[0.25em] uppercase text-starlight/80">Canlı önizleme</h2>
        {loading && <span className="text-[10px] text-cream/40 animate-pulse">güncelleniyor…</span>}
      </div>
      {hasConfig && (
        <div className="mb-2 grid grid-cols-2 rounded-lg border border-cream/10 p-0.5 text-xs">
          {VIEWS.map((v) => (
            <button
              key={v.id}
              onClick={() => onViewChange(v.id)}
              className={`rounded-md py-1.5 transition-colors ${
                view === v.id ? "bg-starlight text-night font-medium" : "text-cream/60 hover:text-cream"
              }`}
            >
              {v.label}
            </button>
          ))}
        </div>
      )}
      {error && <p className="text-xs text-red-400 px-1 pb-2">{error}</p>}
      {!hasConfig ? (
        <div className="aspect-[2/3] rounded-xl border border-dashed border-cream/15 flex items-center justify-center">
          <p className="text-sm text-cream/40 text-center px-6">
            Konum ve tarihi girince<br />gökyüzü burada belirecek ✦
          </p>
        </div>
      ) : (
        <div
          className={`rounded-xl overflow-hidden shadow-2xl [&>svg]:w-full [&>svg]:h-auto ${
            large ? "md:flex md:justify-center md:bg-[#0a0604] md:[&>svg]:w-auto md:[&>svg]:max-w-full md:[&>svg]:h-[calc(100vh-240px)]" : ""
          }`}
          dangerouslySetInnerHTML={{ __html: svg }}
        />
      )}
      {hasConfig && view === "mockup" && (
        <p className="px-1 pt-2 text-[10px] text-cream/40 text-center">
          Temsili görseldir, ışık tonu ve ahşap dokusu ürüne göre farklılık gösterebilir.
        </p>
      )}
    </div>
  );
}
