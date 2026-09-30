"use client";
import { useState } from "react";
import { geocode, MapConfig } from "@/lib/api";
import TR from "@/lib/tr-il-ilce.json";

// 81 il ve ilçeleri (PTT verisi, turkey-neighbourhoods paketinden). Alfabetik sıralı.
type Province = { code: string; name: string; districts: string[] };
const PROVINCES = TR as Province[];

export default function LocationForm({ onResolved }: { onResolved: (c: MapConfig) => void }) {
  const [provinceCode, setProvinceCode] = useState("");
  const [district, setDistrict] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("21:00");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [done, setDone] = useState(false);

  const province = PROVINCES.find((p) => p.code === provinceCode);

  const submit = async () => {
    if (!province || !district || !date) {
      setErr("İl, ilçe ve tarih seçin");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      // "Merkez" ilçesi il merkezidir; konum aramasında il adı yeterli
      const loc = await geocode("Türkiye", province.name, district === "Merkez" ? "" : district);
      onResolved({
        location: {
          lat: loc.lat,
          lon: loc.lon,
          display: `${district}, ${province.name}`,
          timezone_offset_hours: 3,
        },
        date,
        time,
        mag_limit: 6.0,
        show_constellations: true,
      });
      setDone(true);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  const field = "w-full rounded-lg bg-nightdeep border border-cream/15 px-3 py-2.5 text-sm focus:border-starlight/60 focus:outline-none disabled:opacity-40";
  const select = `${field} appearance-none bg-[url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2212%22 height=%228%22><path d=%22M1 1l5 5 5-5%22 fill=%22none%22 stroke=%22%23e8c46a%22 stroke-width=%221.5%22/></svg>')] bg-no-repeat bg-[position:right_0.8rem_center] pr-8`;

  if (done && province) {
    const [y, m, d] = date.split("-");
    return (
      <div className="rounded-2xl border border-cream/10 bg-nightdeep/50 p-4 flex items-center gap-3">
        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-starlight text-night text-xs font-semibold">✓</span>
        <div className="min-w-0 flex-1">
          <p className="text-xs tracking-[0.2em] uppercase text-starlight/80">1. Adım · Yıldız haritası</p>
          <p className="mt-0.5 truncate text-sm text-cream/80">
            {district}, {province.name} · {d}.{m}.{y} {time}
          </p>
        </div>
        <button onClick={() => setDone(false)} className="text-xs text-starlight underline underline-offset-2">
          Değiştir
        </button>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-cream/10 bg-nightdeep/50 p-4 space-y-3">
      <div className="flex items-center gap-2">
        <span className="flex h-6 w-6 items-center justify-center rounded-full border border-starlight text-starlight text-xs font-semibold">1</span>
        <h2 className="text-xs tracking-[0.2em] uppercase text-starlight/80">Yıldız haritası · Konum ve tarih</h2>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <label className="block text-xs text-cream/60">
          İl
          <select
            className={`${select} mt-1`}
            value={provinceCode}
            onChange={(e) => {
              setProvinceCode(e.target.value);
              setDistrict("");
            }}
          >
            <option value="" disabled>İl seçin</option>
            {PROVINCES.map((p) => (
              <option key={p.code} value={p.code}>{p.name}</option>
            ))}
          </select>
        </label>
        <label className="block text-xs text-cream/60">
          İlçe
          <select
            className={`${select} mt-1`}
            value={district}
            disabled={!province}
            onChange={(e) => setDistrict(e.target.value)}
          >
            <option value="" disabled>{province ? "İlçe seçin" : "Önce il seçin"}</option>
            {province?.districts.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <label className="block text-xs text-cream/60">
          Tarih
          <input className={`${field} mt-1`} type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </label>
        <label className="block text-xs text-cream/60">
          Saat
          <input className={`${field} mt-1`} type="time" value={time} onChange={(e) => setTime(e.target.value)} />
        </label>
      </div>

      {err && <p className="text-xs text-red-400">{err}</p>}
      <button
        onClick={submit}
        disabled={busy}
        className="w-full rounded-lg bg-starlight text-night font-medium py-2.5 text-sm disabled:opacity-50"
      >
        {busy ? "Gökyüzü hesaplanıyor…" : "Yıldız haritasını oluştur"}
      </button>
    </div>
  );
}
