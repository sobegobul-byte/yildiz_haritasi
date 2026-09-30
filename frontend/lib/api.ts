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
}

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
  return { svg: await r.text(), overflow: r.headers.get("X-Text-Overflow") === "1" };
}

export async function downloadExport(
  format: "pdf" | "dxf",
  config: MapConfig,
  personalization: Personalization
) {
  const r = await fetch(`/api/export/${format}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ config, personalization, template_id: "yummy-lamp", format }),
  });
  if (!r.ok) throw new Error("Export başarısız");
  const blob = await r.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `yildiz-haritasi.${format}`;
  a.click();
  URL.revokeObjectURL(url);
}
