"use client";
import { Personalization, TextElement } from "@/lib/api";

// Koordinat ve tarih otomatik yazılır (koordinat her zaman en alt satırda).
// Boyut/hizalama/kaydırma ayarları kaldırıldı — satırlar boş alana otomatik ortalanır.
const FIELDS: { key: keyof Personalization; label: string; multiline?: boolean }[] = [
  { key: "title", label: "1. Satır" },
  { key: "subtitle", label: "2. Satır" },
  { key: "names", label: "3. Satır" },
  { key: "message", label: "4. Satır (mesaj)", multiline: true },
];

export default function TextEditor({
  pers, onChange,
}: { pers: Personalization; onChange: (p: Personalization) => void }) {
  const update = (key: keyof Personalization, patch: Partial<TextElement>) =>
    onChange({ ...pers, [key]: { ...pers[key], ...patch } });

  const input = "w-full rounded-md bg-night border border-cream/15 px-2.5 py-2 text-sm focus:border-starlight/60 focus:outline-none";

  return (
    <div className="rounded-2xl border border-cream/10 bg-nightdeep/50 p-4 space-y-3">
      <div className="flex items-center gap-2 mb-2">
        <span className="flex h-6 w-6 items-center justify-center rounded-full border border-starlight text-starlight text-xs font-semibold">2</span>
        <h2 className="text-xs tracking-[0.2em] uppercase text-starlight/80">Kişiselleştir</h2>
      </div>
      {FIELDS.map(({ key, label, multiline }) => {
        const el = pers[key];
        return (
          <label key={key} className="block text-xs text-cream/60">
            {label}
            {multiline ? (
              <textarea
                rows={2}
                value={el.content}
                onChange={(e) => update(key, { content: e.target.value })}
                className={`${input} mt-1`}
                placeholder={label}
              />
            ) : (
              <input
                value={el.content}
                onChange={(e) => update(key, { content: e.target.value })}
                className={`${input} mt-1`}
                placeholder={label}
              />
            )}
          </label>
        );
      })}
    </div>
  );
}
