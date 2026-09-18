import { request, AutomationSupport } from "./campaigns";
import { FeatureInput, FeatureResponse } from "./features";

export type Source = {
  scraping: AutomationSupport;
  source_id: string;
  bank: string;
  bank_type: string;
  country: string;
  product_name: string;
  product_category: string;
  language: string;
  page_type: string;
  url: string;
  is_example: boolean;
  import_status: string;
  campaign_id: number | null;
  error: string | null;
  attempted_at: string | null;
};
export type Catalog = {
  sources: Source[];
  banks: string[];
  categories: string[];
  data_mode: string;
};
export type ImportResult = {
  source_id: string;
  status: "success" | "existing" | "failed" | "manual_required";
  supported: boolean;
  message: string | null;
  campaign_id: number | null;
  error: string | null;
};
export type Proposal = {
  campaign_id: number;
  token: string;
  engine: string;
  is_demo: boolean;
  values: Partial<FeatureInput>;
  warnings: string[];
  reviewed: boolean;
  created_at: string;
};
export const getSources = () => request<Catalog>("/scraping/sources");
export const scrapeSources = (source_ids: string[]) =>
  request<{ results: ImportResult[] }>("/scraping/run", "POST", { source_ids });
export const autoLabel = (id: number) =>
  request<
    Proposal | { status: "manual_required"; supported: boolean; message: string }
  >(`/campaigns/${id}/auto-label`, "POST");
export const getSuggestions = (id: string) =>
  request<Proposal | null>(`/campaigns/${id}/suggestions`);
export const reviewSuggestions = (id: string, token: string, data: FeatureInput) => {
  const { average_paragraph_length: _derived, ...values } = data;
  return request<FeatureResponse>(`/campaigns/${id}/suggestions/review`, "POST", {
    token,
    values,
  });
};
