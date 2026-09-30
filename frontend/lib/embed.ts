// Web sitesine iframe olarak gömülme desteği.
// Sayfa iframe içindeyse müşteri modundadır (imalat düğmeleri gizlenir) ve
// önemli olaylar üst sayfaya postMessage ile bildirilir.

// Mesajın gideceği web sitesi adresi (örn. https://yummylightstore.com).
// Boş bırakılırsa her siteye gönderilir ("*").
const PARENT_ORIGIN = process.env.NEXT_PUBLIC_PARENT_ORIGIN || "*";

export function isEmbedded(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.self !== window.top;
  } catch {
    return true; // farklı alan adındaki üst sayfaya erişim engellenir -> iframe içindeyiz
  }
}

export function notifyParent(type: string, data: Record<string, unknown> = {}) {
  if (typeof window === "undefined" || window.parent === window) return;
  window.parent.postMessage({ source: "yildiz-haritasi", type, ...data }, PARENT_ORIGIN);
}
