"use client";
import { Personalization, TextElement } from "@/lib/api";

// Koordinat ve tarih otomatik yazılır (koordinat her zaman en alt satırda).
// Satır kaydırma ve yazı boyutu sunucuda otomatik hesaplanır: yazılar lamba
// kesim çizgisinin içinde kalacak şekilde alt satıra geçer ve küçülür.
const FIELDS: { key: keyof Personalization; label: string; placeholder: string; max: number; multiline?: boolean }[] = [
  { key: "title", label: "1. Satır (başlık)", placeholder: "Örn. Fatih & Yasemin", max: 40 },
  { key: "subtitle", label: "2. Satır", placeholder: "Örn. Aynı gökyüzü altında, hep seninle.", max: 70 },
  { key: "names", label: "3. Satır", placeholder: "İsteğe bağlı", max: 70 },
  { key: "message", label: "4. Satır (mesaj)", placeholder: "İsteğe bağlı", max: 140, multiline: true },
];

export default function TextEditor({
  pers, onChange, overflow,
}: { pers: Personalization; onChange: (p: Personalization) => void; overflow: boolean }) {
  const update = (key: keyof Personalization, patch: Partial<TextElement>) =>
    onChange({ ...pers, [key]: { ...pers[key], ...patch } });

  const input = "w-full rounded-md bg-night border border-cream/15 px-2.5 py-2 text-sm placeholder:text-cream/30 focus:border-starlight/60 focus:outline-none";

  return (
    <div className="rounded-2xl border border-cream/10 bg-nightdeep/50 p-4 space-y-3">
      <div className="flex items-center gap-2">
        <span className="flex h-6 w-6 items-center justify-center rounded-full border border-starlight text-starlight text-xs font-semibold">2</span>
        <h2 className="text-xs tracking-[0.2em] uppercase text-starlight/80">Kişiselleştir</h2>
      </div>
      <p className="text-[11px] text-cream/45">
        Yazılar lamba alanına otomatik sığdırılır: uzun yazı alt satıra geçer, boyut kendiliğinden ayarlanır.
      </p>
      {FIELDS.map(({ key, label, placeholder, max, multiline }) => {
        const el = pers[key];
        return (
          <label key={key} className="block text-xs text-cream/60">
            <span className="flex justify-between">
              {label}
              {el.content.length > max * 0.7 && (
                <span className="text-cream/35">{el.content.length}/{max}</span>
              )}
            </span>
            {multiline ? (
              <textarea
                rows={2}
                maxLength={max}
                value={el.content}
                onChange={(e) => update(key, { content: e.target.value })}
                className={`${input} mt-1`}
                placeholder={placeholder}
              />
            ) : (
              <input
                maxLength={max}
                value={el.content}
                onChange={(e) => update(key, { content: e.target.value })}
                className={`${input} mt-1`}
                placeholder={placeholder}
              />
            )}
          </label>
        );
      })}
      {overflow && (
        <p className="rounded-md border border-red-400/40 bg-red-400/10 px-3 py-2 text-xs text-red-300">
          Yazılar lamba alanına sığmıyor. Lütfen bazı satırları kısaltın ya da boş bırakın.
        </p>
      )}
    </div>
  );
}
