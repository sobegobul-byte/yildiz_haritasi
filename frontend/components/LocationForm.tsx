"use client";
import { useEffect, useState } from "react";
import { geocode, MapConfig } from "@/lib/api";
import TR from "@/lib/tr-il-ilce.json";

// 81 il ve ilçeleri (PTT verisi, turkey-neighbourhoods paketinden). Alfabetik sıralı.
type Province = { code: string; name: string; districts: string[] };
const PROVINCES = TR as Province[];

const pad = (n: number) => String(n).padStart(2, "0");
const DAYS = Array.from({ length: 31 }, (_, i) => pad(i + 1));
const MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];
const THIS_YEAR = new Date().getFullYear();
const YEARS = Array.from({ length: THIS_YEAR + 2 - 1900 }, (_, i) => String(THIS_YEAR + 1 - i));   // yeniden eskiye
// saat/dakika serbest yazılır: sadece rakam, en fazla 2 hane
const digits = (v: string) => v.replace(/\D/g, "").slice(0, 2);

export default function LocationForm({ onResolved }: { onResolved: (c: MapConfig) => void }) {
  const [provinceCode, setProvinceCode] = useState("");
  const [district, setDistrict] = useState("");
  // Tarih/saat açılır listelerle seçilir (iOS'un yerel tarih/saat kutuları boş görünüyor,
  // takvim bugünden açılıyor ve kutu taşıyordu)
  const [day, setDay] = useState("");
  const [month, setMonth] = useState("");
  const [year, setYear] = useState("");
  const [hour, setHour] = useState("21");
  const [minute, setMinute] = useState("00");
  const daysInMonth = month ? new Date(Number(year || 2000), Number(month), 0).getDate() : 31;
  const date = day && month && year && Number(day) <= daysInMonth ? `${year}-${month}-${day}` : "";
  const hourOk = hour !== "" && Number(hour) <= 23;
  const minuteOk = minute !== "" && Number(minute) <= 59;
  const time = `${pad(Number(hour || 0))}:${pad(Number(minute || 0))}`;
  // ay/yıl değişince o ayda olmayan gün seçili kalmasın (ör. 31 Şubat)
  useEffect(() => {
    if (day && Number(day) > daysInMonth) setDay("");
  }, [day, daysInMonth]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [done, setDone] = useState(false);

  const province = PROVINCES.find((p) => p.code === provinceCode);

  const submit = async () => {
    if (!province || !district || !date) {
      setErr("İl, ilçe ve tarihi (gün, ay, yıl) seçin");
      return;
    }
    if (!hourOk || !minuteOk) {
      setErr("Saat 0–23, dakika 0–59 arasında olmalı");
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

  const field = "w-full rounded-lg bg-nightdeep border border-cream/15 px-3 py-2.5 text-base sm:text-sm focus:border-starlight/60 focus:outline-none disabled:opacity-40";
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

      <div className="block text-xs text-cream/60">
        Tarih
        <div className="mt-1 grid grid-cols-[1fr_1.4fr_1.2fr] gap-2">
          <select className={select} value={day} onChange={(e) => setDay(e.target.value)} aria-label="Gün">
            <option value="" disabled>Gün</option>
            {DAYS.map((d) => (
              <option key={d} value={d} disabled={Number(d) > daysInMonth}>{Number(d)}</option>
            ))}
          </select>
          <select className={select} value={month} onChange={(e) => setMonth(e.target.value)} aria-label="Ay">
            <option value="" disabled>Ay</option>
            {MONTHS.map((m, i) => (
              <option key={m} value={String(i + 1).padStart(2, "0")}>{m}</option>
            ))}
          </select>
          <select className={select} value={year} onChange={(e) => setYear(e.target.value)} aria-label="Yıl">
            <option value="" disabled>Yıl</option>
            {YEARS.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="block text-xs text-cream/60">
        Saat
        <div className="mt-1 flex items-center gap-2">
          <input
            className={`${field} text-center ${hourOk ? "" : "border-red-400/70"}`}
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            maxLength={2}
            placeholder="SS"
            value={hour}
            onChange={(e) => { setHour(digits(e.target.value)); setErr(""); }}
            onBlur={() => hour && hourOk && setHour(pad(Number(hour)))}
            onFocus={(e) => e.target.select()}
            aria-label="Saat"
          />
          <span className="text-cream/60 text-base">:</span>
          <input
            className={`${field} text-center ${minuteOk ? "" : "border-red-400/70"}`}
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            maxLength={2}
            placeholder="DD"
            value={minute}
            onChange={(e) => { setMinute(digits(e.target.value)); setErr(""); }}
            onBlur={() => minute && minuteOk && setMinute(pad(Number(minute)))}
            onFocus={(e) => e.target.select()}
            aria-label="Dakika"
          />
        </div>
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
