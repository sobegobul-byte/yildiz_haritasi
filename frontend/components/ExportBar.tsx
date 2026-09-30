"use client";
import { useState } from "react";
import { ExportFormat, MapConfig, Personalization, downloadExport } from "@/lib/api";

// Alt çubuk: müşteri için "Sipariş ver"; yanında küçük imalat dosyası düğmeleri.
export default function ExportBar({
  config, pers, blocked, woodBlocked, orderDisabledReason, onOrder,
}: {
  config: MapConfig;
  pers: Personalization;
  blocked: boolean;
  woodBlocked: boolean;
  orderDisabledReason: string;
  onOrder: () => void;
}) {
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

  const small = "rounded-md border border-cream/15 px-2.5 py-1.5 text-[11px] text-cream/60 hover:text-cream disabled:opacity-40";

  return (
    <div className="fixed bottom-0 inset-x-0 bg-nightdeep/90 backdrop-blur border-t border-cream/10 p-3">
      <div className="mx-auto max-w-md md:max-w-5xl flex flex-col-reverse gap-2 md:flex-row md:items-center">
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] text-cream/35 mr-1">İmalat:</span>
          <button onClick={() => run("pdf")} disabled={!!busy || blocked} className={small}>
            {busy === "pdf" ? "…" : "PDF"}
          </button>
          <button onClick={() => run("dxf")} disabled={!!busy || blocked} className={small}>
            {busy === "dxf" ? "…" : "DXF"}
          </button>
          {wood && (
            <button onClick={() => run("wood-dxf")} disabled={!!busy || woodBlocked} className={small}>
              {busy === "wood-dxf" ? "…" : "Ahşap DXF"}
            </button>
          )}
        </div>
        <div className="flex-1 md:text-right">
          {orderDisabledReason && (
            <p className="mb-1 text-[11px] text-red-300 md:inline md:mr-3">{orderDisabledReason}</p>
          )}
          <button
            onClick={onOrder}
            disabled={!!orderDisabledReason}
            className="w-full md:w-72 rounded-lg bg-starlight text-night font-semibold py-3 text-sm disabled:opacity-40"
          >
            Sipariş ver
          </button>
        </div>
      </div>
    </div>
  );
}
