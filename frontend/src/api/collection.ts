import { request, AutomationSupport } from "./campaigns";
import { FeatureInput, FeatureResponse } from "./features";

export type Source = {
  scraping: AutomationSupport;
  auto_labeling_supported: boolean;
  capture_available: boolean;
  source_id: string;
  bank: string;
  bank_type: string | null;
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
export const deleteSource = (id: string) =>
  request<void>(`/scraping/sources/${encodeURIComponent(id)}`, "DELETE");
export type CaptureMode = "auto" | "capture_only" | "scrape_and_label";
export type NewSource = {
  bank: string;
  product_name: string;
  product_category: string;
  language: string;
  url: string;
};
export const addSource = (data: NewSource) =>
  request<NewSource & { source_id: string }>("/scraping/sources", "POST", data);
export const scrapeSources = (
  source_ids: string[],
  mode: CaptureMode = "auto",
  recapture = false,
) =>
  request<{ results: ImportResult[] }>("/scraping/run", "POST", {
    source_ids,
    mode,
    recapture,
  });
export const getSuggestions = (id: string) =>
  request<Proposal | null>(`/campaigns/${id}/suggestions`);
export const reviewSuggestions = (id: string, token: string, data: FeatureInput) => {
  const { average_paragraph_length: _derived, ...values } = data;
  return request<FeatureResponse>(`/campaigns/${id}/suggestions/review`, "POST", {
    token,
    values,
  });
};

export type Capture = {
  id: string;
  created_at: string;
  has_screenshot: boolean;
  page: ScrapedContent;
};
export const getCaptures = (id: number) =>
  request<Capture[]>(`/scraping/campaigns/${id}/captures`);
export const captureArtifactUrl = (id: string, artifact: string) =>
  `${(import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "")}/api/scraping/captures/${id}/${artifact}`;

export type ScrapedContent = {
  title: string;
  headline?: string | null;
  text: string;
  headings?: string[];
  paragraphs?: string[];
  bullets?: string[];
  tables?: string[];
  scraped_at: string;
  is_demo: boolean;
  warnings: string[];
  source: { product_name: string; language: string; url: string };
};
export const getScrapedContent = (id: number) =>
  request<ScrapedContent | null>(`/scraping/campaigns/${id}/content`);
