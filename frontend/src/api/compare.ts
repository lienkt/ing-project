import { request } from "./campaigns";
import { FeatureRecord, LabelingStatus, featureFields } from "./features";

export type ComparisonPage = {
  campaign_id: number;
  bank_name: string;
  bank_type: string | null;
  product_name: string | null;
  product_category: string;
  page_url: string;
  language: string | null;
  capture_date: string | null;
  labeling_status: LabelingStatus;
  features: FeatureRecord | null;
};
export type Comparison = { product_category: string; pages: ComparisonPage[] };
export function getComparison(
  category: string,
  campaignIds: number[] = [],
  bankNames: string[] = [],
) {
  const params = new URLSearchParams({ product_category: category });
  campaignIds.forEach((id) => params.append("campaign_ids", String(id)));
  bankNames.forEach((name) => params.append("bank_names", name));
  return request<Comparison>(`/compare?${params}`);
}
export const analyticalFields = featureFields.filter(
  (field) => field.section !== "Identification & Metadata",
);
export const scaleFields = analyticalFields.filter((field) => field.kind === "scale");
export type ScaleDefinition = (typeof scaleFields)[number];
export const pageTitle = (page: ComparisonPage) =>
  `${page.bank_name} · ${page.product_name || "Product not recorded"} · Page #${page.campaign_id}`;
