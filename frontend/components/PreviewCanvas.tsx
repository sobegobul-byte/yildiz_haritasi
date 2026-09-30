"use client";

export default function PreviewCanvas({
  svg, loading, error, hasConfig,
}: { svg: string; loading: boolean; error: string; hasConfig: boolean }) {
  return (
    <div className="relative rounded-2xl border border-cream/10 bg-nightdeep/50 p-3">
      <div className="flex items-center justify-between px-1 pb-2">
        <h2 className="text-xs tracking-[0.25em] uppercase text-starlight/80">Canlı önizleme</h2>
        {loading && <span className="text-[10px] text-cream/40 animate-pulse">güncelleniyor…</span>}
      </div>
      {error && <p className="text-xs text-red-400 px-1 pb-2">{error}</p>}
      {!hasConfig ? (
        <div className="aspect-[2/3] rounded-xl border border-dashed border-cream/15 flex items-center justify-center">
          <p className="text-sm text-cream/40 text-center px-6">
            Konum ve tarihi girince<br />gökyüzü burada belirecek ✦
          </p>
        </div>
      ) : (
        <div
          className="rounded-xl overflow-hidden shadow-2xl [&>svg]:w-full [&>svg]:h-auto"
          dangerouslySetInnerHTML={{ __html: svg }}
        />
      )}
    </div>
  );
}
