import {
  IkasProduct,
  IkasProductOption,
  addItemToCart,
  getProductOptionSet,
  getSelectedProductVariant,
  hasValidProductOptionSetValues,
  initProductOptionSetValues,
  isCheckboxOption,
  isChoiceOption,
  selectValue,
  setCheckboxValue,
  setTextValue,
} from "@ikas/bp-storefront";
import { useEffect, useRef, useState } from "preact/hooks";
import { Props } from "./types";

// Yıldız Haritası Stüdyosu (tünel) iframe'i. Müşteri tasarımı onaylayınca iframe
// postMessage({source:"yildiz-haritasi", type:"approved", order}) gönderir; bu bölüm
// ürünün kişiselleştirme alanlarını doldurur ve (isteğe bağlı) ürünü sepete ekler.

type Order = { order_id: string; wood_engraving: boolean };
type Status = { kind: "info" | "ok" | "error"; text: string } | null;

const trLower = (s: string) => s.toLocaleLowerCase("tr");

function allOptions(product: IkasProduct): IkasProductOption[] {
  const out: IkasProductOption[] = [];
  const walk = (list: IkasProductOption[] | null | undefined) =>
    (list || []).forEach((o) => {
      out.push(o);
      walk(o.childOptions);
    });
  walk(product.productOptionSet?.options);
  return out;
}

function findOption(product: IkasProduct, name: string) {
  const n = trLower(name.trim());
  if (!n) return undefined;
  const opts = allOptions(product);
  return opts.find((o) => trLower(o.name) === n) || opts.find((o) => trLower(o.name).includes(n));
}

// Ahşap kazıma seçeneğini işaretle / kaldır (onay kutusu veya seçim listesi)
function setWoodOption(option: IkasProductOption, on: boolean) {
  if (isCheckboxOption(option)) {
    setCheckboxValue(option, on);
    return true;
  }
  if (isChoiceOption(option)) {
    const values = option.selectSettings?.values || [];
    const yes = values.find((v) => /evet|var|ekle|kaz|istiyorum/i.test(v.value));
    const no = values.find((v) => /hayır|hayir|yok|istemiyorum/i.test(v.value));
    const pick = on ? yes : no;
    if (pick) selectValue(option, pick);
    return !!pick || !on;
  }
  return false;
}

function originOf(url: string) {
  try {
    return new URL(url).origin;
  } catch {
    return "";
  }
}

export function YildizHaritasiTasarim({
  product,
  designerUrl,
  designOptionName = "Tasarım No",
  woodOptionName = "Ahşap",
  frameHeight = "min(100vh, 900px)",
  autoAddToCart = true,
  frameTitle = "Yıldız Haritası Tasarla",
  addingText = "Tasarımınız onaylandı, sepete ekleniyor…",
  addedText = "✓ Tasarımınız sepete eklendi. Tasarım No:",
  filledText = "✓ Tasarımınız onaylandı, Sepete Ekle ile devam edebilirsiniz. Tasarım No:",
  errorText = "Sepete eklenemedi. Lütfen Sepete Ekle düğmesini kullanın. Tasarım No:",
  missingOptionText = "Ürünün Tasarım No kişiselleştirme alanı bulunamadı.",
}: Props) {
  const [status, setStatus] = useState<Status>(null);
  // mesaj dinleyicisi her zaman güncel props'u görsün
  const latest = useRef({ product, designOptionName, woodOptionName, autoAddToCart });
  latest.current = { product, designOptionName, woodOptionName, autoAddToCart };

  useEffect(() => {
    if (product) getProductOptionSet(product);
  }, [product?.id]);

  useEffect(() => {
    const allowed = originOf(designerUrl);
    const onMessage = async (e: MessageEvent) => {
      if (!allowed || e.origin !== allowed) return;
      const m = e.data || {};
      if (m.source !== "yildiz-haritasi" || m.type !== "approved" || !m.order) return;
      const order = m.order as Order;
      const { product: p, designOptionName: dName, woodOptionName: wName, autoAddToCart: auto } = latest.current;
      if (!p) return;

      if (!p.productOptionSet) await getProductOptionSet(p);
      const designOpt = findOption(p, dName);
      if (!designOpt) {
        setStatus({ kind: "error", text: `${missingOptionText} Tasarım No: ${order.order_id}` });
        return;
      }
      setTextValue(designOpt, order.order_id);
      const woodOpt = findOption(p, wName);
      if (woodOpt) setWoodOption(woodOpt, !!order.wood_engraving);

      if (!auto) {
        setStatus({ kind: "ok", text: `${filledText} ${order.order_id}` });
        return;
      }

      setStatus({ kind: "info", text: addingText });
      try {
        const set = p.productOptionSet;
        if (set && !hasValidProductOptionSetValues(set)) {
          window.dispatchEvent(new CustomEvent("ikas:show-option-errors"));
          throw new Error("options");
        }
        const result = await addItemToCart(getSelectedProductVariant(p), p, 1);
        if (!result.success) throw new Error("cart");
        if (set) initProductOptionSetValues(set);
        window.dispatchEvent(new CustomEvent("ikas:reset-option-state"));
        window.dispatchEvent(new CustomEvent("ikas:open-cart-sidebar"));
        setStatus({ kind: "ok", text: `${addedText} ${order.order_id}` });
      } catch {
        setStatus({ kind: "error", text: `${errorText} ${order.order_id}` });
      }
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [designerUrl, addingText, addedText, filledText, errorText, missingOptionText]);

  if (!designerUrl || !originOf(designerUrl)) return null;

  return (
    <section className="yh-section">
      {status && <div className={`yh-status yh-status--${status.kind}`}>{status.text}</div>}
      <iframe
        className="yh-frame"
        src={designerUrl}
        title={frameTitle}
        style={{ height: frameHeight }}
        allow="clipboard-write"
      />
    </section>
  );
}

export default YildizHaritasiTasarim;
