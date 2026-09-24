import type { ComparisonPage } from "../api/compare";

const bankKey = (name: string) => name.trim().toLowerCase().replace(/\s+/g, " ");
const productKey = (page: ComparisonPage) =>
  page.product_name?.trim().toLowerCase() || `page-${page.campaign_id}`;

function bankHue(bank: string) {
  if (/^ing\b/.test(bank)) return 25;
  if (/^kbc\b/.test(bank)) return 200;
  if (/^belfius\b/.test(bank)) return 340;
  if (/^bnp\b/.test(bank)) return 150;
  if (/^revolut\b/.test(bank)) return 265;
  if (/^n26\b/.test(bank)) return 180;
  // Reserve orange for ING, including for banks added to the dataset later.
  const hash = Array.from(bank).reduce(
    (value, char) => (value * 31 + char.charCodeAt(0)) >>> 0,
    0,
  );
  return 100 + (hash % 251);
}

export function pageColors(pages: ComparisonPage[]) {
  const productsByBank = new Map<string, Set<string>>();
  for (const page of pages) {
    const bank = bankKey(page.bank_name);
    if (!productsByBank.has(bank)) productsByBank.set(bank, new Set());
    productsByBank.get(bank)!.add(productKey(page));
  }
  return new Map(
    pages.map((page) => {
      const bank = bankKey(page.bank_name);
      const products = [...productsByBank.get(bank)!].sort();
      const index = products.indexOf(productKey(page));
      const lightness =
        products.length === 1 ? 48 : 36 + (index / (products.length - 1)) * 30;
      return [
        page.campaign_id,
        `hsl(${bankHue(bank)} ${/^ing\b/.test(bank) ? 95 : 60}% ${lightness}%)`,
      ];
    }),
  );
}
