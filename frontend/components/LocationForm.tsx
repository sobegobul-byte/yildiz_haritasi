"use client";
import { useState } from "react";
import { geocode, MapConfig } from "@/lib/api";

export default function LocationForm({ onResolved }: { onResolved: (c: MapConfig) => void }) {
  const [country, setCountry] = useState("Türkiye");
  const [province, setProvince] = useState("");
  const [district, setDistrict] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("21:00");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [found, setFound] = useState("");

  const submit = async () => {
    if (!province || !date) {
      setErr("İl ve tarih zorunlu");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      const loc = await geocode(country, province, district);
      setFound(loc.display);
      onResolved({
        location: {
          lat: loc.lat,
          lon: loc.lon,
          display: loc.display,
          timezone_offset_hours: country.toLowerCase().startsWith("t") ? 3 : 0,
        },
        date,
        time,
        mag_limit: 6.0,
        show_constellations: true,
      });
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  const field = "w-full rounded-lg bg-nightdeep border border-cream/15 px-3 py-2.5 text-sm placeholder:text-cream/30 focus:border-starlight/60 focus:outline-none";

  return (
    <div className="rounded-2xl border border-cream/10 bg-nightdeep/50 p-4 space-y-3">
      <h2 className="text-xs tracking-[0.25em] uppercase text-starlight/80">Konum ve tarih</h2>
      <div className="grid grid-cols-2 gap-2">
        <input className={field} value={country} onChange={(e) => setCountry(e.target.value)} placeholder="Ülke" />
        <input className={field} value={province} onChange={(e) => setProvince(e.target.value)} placeholder="İl *" />
      </div>
      <input className={field} value={district} onChange={(e) => setDistrict(e.target.value)} placeholder="İlçe (isteğe bağlı)" />
      <div className="grid grid-cols-2 gap-2">
        <input className={field} type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        <input className={field} type="time" value={time} onChange={(e) => setTime(e.target.value)} />
      </div>
      {err && <p className="text-xs text-red-400">{err}</p>}
      {found && <p className="text-xs text-cream/50">📍 {found}</p>}
      <button
        onClick={submit}
        disabled={busy}
        className="w-full rounded-lg bg-starlight text-night font-medium py-2.5 text-sm disabled:opacity-50"
      >
        {busy ? "Gökyüzü hesaplanıyor…" : "Gökyüzünü oluştur"}
      </button>
    </div>
  );
}
