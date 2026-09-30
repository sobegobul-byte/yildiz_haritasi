"use client";
import { useState } from "react";
import { ExportFormat, MapConfig, Personalization, downloadExport } from "@/lib/api";

export default function ExportBar({
  config, pers, blocked, woodBlocked,
}: { config: MapConfig; pers: Personalization; blocked: boolean; woodBlocked: boolean }) {
  const [busy, setBusy] = useState<"" | ExportFormat>("");
  const wood = pers.wood_engraving && pers.wood_text.trim() !== "";

  const run = async (fmt: ExportFormat) => {
    setBusy(fmt);
    try {
      await downloadExport(fmt, config, pers);
    } finally {
      setBusy("");
    }
  };

  return (
    <div className="fixed bottom-0 inset-x-0 bg-nightdeep/90 backdrop-blur border-t border-cream/10 p-3">
      <div className="mx-auto max-w-md md:max-w-5xl flex gap-2">
        <button
          onClick={() => run("pdf")}
          disabled={!!busy || blocked}
          className="flex-1 rounded-lg bg-starlight text-night font-medium py-3 text-sm disabled:opacity-50"
        >
          {busy === "pdf" ? "Hazırlanıyor…" : "PDF indir (baskı)"}
        </button>
        <button
          onClick={() => run("dxf")}
          disabled={!!busy || blocked}
          className="flex-1 rounded-lg border border-starlight/60 text-starlight font-medium py-3 text-sm disabled:opacity-50"
        >
          {busy === "dxf" ? "Hazırlanıyor…" : "DXF indir (lazer)"}
        </button>
        {wood && (
          <button
            onClick={() => run("wood-dxf")}
            disabled={!!busy || woodBlocked}
            className="flex-1 rounded-lg border border-starlight/60 text-starlight font-medium py-3 text-sm disabled:opacity-50"
          >
            {busy === "wood-dxf" ? "Hazırlanıyor…" : "Ahşap DXF"}
          </button>
        )}
      </div>
    </div>
  );
}
