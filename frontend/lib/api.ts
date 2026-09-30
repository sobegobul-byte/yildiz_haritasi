// Backend istemcisi. Next.js rewrite sayesinde /api -> localhost:8000

export type Align = "start" | "middle" | "end";

export interface TextElement {
  content: string;
  font_size: number;
  align: Align;
  dx: number;
  dy: number;
  letter_spacing: number;
  visible: boolean;
}

export const emptyEl = (overrides: Partial<TextElement> = {}): TextElement => ({
  content: "",
  font_size: 16,
  align: "middle",
  dx: 0,
  dy: 0,
  letter_spacing: 0,
  visible: true,
  ...overrides,
});

export interface Personalization {
  title: TextElement;
  subtitle: TextElement;
  names: TextElement;
  coords_text: TextElement;
  date_text: TextElement;
  message: TextElement;
  // ek hizmet: ahşap tabana yazı kazıma
  wood_engraving: boolean;
  wood_text: string;
}

export const WOOD_ENGRAVING_PRICE = 49.9;
export const formatTL = (n: number) =>
  n.toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " TL";

export interface ResolvedLocation {
  lat: number;
  lon: number;
  display: string;
  timezone_offset_hours: number;
}

export interface MapConfig {
  location: ResolvedLocation;
  date: string;
  time: string;
  mag_limit: number;
  show_constellations: boolean;
}

export async function geocode(country: string, province: string, district: string) {
  let r: Response;
  try {
    r = await fetch("/api/geocode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ country, province, district }),
    });
  } catch {
    throw new Error("Sunucuya ulaşılamıyor — klasördeki baslat.bat dosyasını çalıştırın");
  }
  if (r.status === 404) throw new Error("Konum bulunamadı — il adını kontrol edin");
  if (!r.ok) throw new Error("Sunucuya ulaşılamıyor — klasördeki baslat.bat dosyasını çalıştırın");
  return r.json();
}

// "mockup" = isikli urun gorunumu, "flat" = uretim cizimi (PDF/DXF ile birebir)
export type PreviewView = "mockup" | "flat";

export async function fetchPreview(
  config: MapConfig,
  personalization: Personalization,
  view: PreviewView = "mockup"
) {
  const r = await fetch("/api/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ config, personalization, template_id: "yummy-lamp", view }),
  });
  if (!r.ok) throw new Error("Önizleme oluşturulamadı");
  // overflow: yazılar en küçük boyutta bile lamba alanına sığmadı
  return {
    svg: await r.text(),
    overflow: r.headers.get("X-Text-Overflow") === "1",
    woodOverflow: r.headers.get("X-Wood-Overflow") === "1",
  };
}

export type ExportFormat = "pdf" | "dxf" | "wood-dxf";
const EXPORT_FILENAME: Record<ExportFormat, string> = {
  pdf: "yildiz-haritasi.pdf",
  dxf: "yildiz-haritasi.dxf",
  "wood-dxf": "ahsap-yazi.dxf",
};

export async function downloadExport(
  format: ExportFormat,
  config: MapConfig,
  personalization: Personalization
) {
  const r = await fetch(`/api/export/${format}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      config, personalization, template_id: "yummy-lamp",
      format: format === "pdf" ? "pdf" : "dxf",
    }),
  });
  if (!r.ok) throw new Error("Export başarısız");
  const blob = await r.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = EXPORT_FILENAME[format];
  a.click();
  URL.revokeObjectURL(url);
}

export interface OrderSummary {
  order_id: string;
  created_at: string;
  location: string;
  date: string;
  time: string;
  lamp_lines: string[];
  wood_engraving: boolean;
  wood_text: string;
  extra_price: number;
}

// Onaylanan tasarımı siparişe çevirir: üretim dosyaları bu bilgisayarda
// backend/orders/<sipariş-no>/ klasörüne kaydedilir.
export async function createOrder(config: MapConfig, personalization: Personalization): Promise<OrderSummary> {
  const r = await fetch("/api/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ config, personalization, template_id: "yummy-lamp" }),
  });
  if (!r.ok) {
    const detail = await r.json().then((j) => j.detail).catch(() => "");
    throw new Error(typeof detail === "string" && detail ? detail : "Sipariş oluşturulamadı, lütfen tekrar deneyin");
  }
  return r.json();
}

export type CheckoutAction = "add-to-cart" | "buy-now";

// Tasarım klasörünü orders/pending -> orders/cart taşır (müşteri Sepete Ekle / Hızlı Satın Al'a bastı)
export async function markOrderInCart(orderId: string, action: CheckoutAction) {
  await fetch(`/api/orders/${encodeURIComponent(orderId)}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: "cart", action }),
  });
}
