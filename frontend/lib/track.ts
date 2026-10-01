// Anonim kullanım analizi: tasarım adımları kendi sunucumuza kaydedilir ve
// iframe içindeysek üst sayfaya (ikas -> GA4 / Meta Pixel) iletilir.
// Kişisel veri gönderilmez: lambaya yazılan metinler, isim, e-posta yok.
import { isEmbedded, notifyParent } from "@/lib/embed";

export type TrackEvent = "open" | "location" | "date" | "text" | "approved" | "cart";
type Props = Record<string, string | number | boolean>;

let memorySid = "";

// Oturum kimliği: rastgele, sekme kapanınca yenilenir
function sid(): string {
  try {
    let v = sessionStorage.getItem("yh-sid");
    if (!v) {
      v = (crypto.randomUUID?.() || Math.random().toString(36).slice(2) + Date.now().toString(36)).slice(0, 36);
      sessionStorage.setItem("yh-sid", v);
    }
    return v;
  } catch {
    if (!memorySid) memorySid = Math.random().toString(36).slice(2) + Date.now().toString(36);
    return memorySid;
  }
}

export const sessionId = sid;

const sentOnce = new Set<string>();

export function track(name: TrackEvent, props: Props = {}, opts: { once?: boolean } = {}) {
  if (typeof window === "undefined") return;
  if (opts.once) {
    if (sentOnce.has(name)) return;
    sentOnce.add(name);
  }
  const body = JSON.stringify({
    name, sid: sid(), props,
    mobile: window.innerWidth < 768,
    embedded: isEmbedded(),
  });
  try {
    const blob = new Blob([body], { type: "application/json" });
    if (!navigator.sendBeacon?.("/api/events", blob)) {
      fetch("/api/events", { method: "POST", headers: { "Content-Type": "application/json" }, body, keepalive: true }).catch(() => {});
    }
  } catch {}
  // ikas sayfası GA4 / Meta Pixel'e iletir (serbest metin gönderilmez)
  const { occasion_other: _omit, ...publicProps } = props;
  notifyParent("event", { name, params: publicProps });
}

// Seçilen özel günün türü: geçmiş/gelecek, ay, kaç yıl önce, yıldönümüne kaç gün var
export function dateInsights(date: string): Props {
  const [y, m, d] = date.split("-").map(Number);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const picked = new Date(y, m - 1, d);
  const kind = picked.getTime() === today.getTime() ? "today" : picked < today ? "past" : "future";
  let next = new Date(today.getFullYear(), m - 1, d);
  if (next < today) next = new Date(today.getFullYear() + 1, m - 1, d);
  const daysToAnniv = Math.round((next.getTime() - today.getTime()) / 86400000);
  return {
    kind,
    month: m,
    year: y,
    years_ago: Math.max(0, today.getFullYear() - y),
    days_to_anniv: daysToAnniv,
  };
}
