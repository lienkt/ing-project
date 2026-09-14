export const projects = [
  "credit_card",
  "savings_account",
  "current_account",
  "personal_loan",
  "mortgage",
  "insurance",
  "investment",
  "other",
] as const;
export type Project = string;
export const label = (value: string) =>
  value.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
export type Details = {
  campaign_name: string | null;
  headline: string | null;
  subheadline: string | null;
  main_message: string | null;
  cta_text: string | null;
  notes: string | null;
  text_density: string | null;
  tone: string | null;
  feature_vs_benefit: string | null;
  emotional_vs_rational: string | null;
  customer_vs_product_focus: string | null;
};
export const scoreFields = [
  "clarity_score",
  "visual_score",
  "benefit_score",
  "cta_score",
  "overall_score",
] as const;
export type ScoreField = (typeof scoreFields)[number];
export type EvaluationInput = Record<ScoreField, number> & {
  evaluation_notes: string | null;
};
export type Evaluation = EvaluationInput & {
  id: number;
  campaign_id: number;
  source: string;
  created_at: string;
  updated_at: string;
};
export type CampaignInput = {
  bank_name: string;
  project: Project;
  campaign_url: string;
};
export type Campaign = CampaignInput & {
  id: number;
  created_at: string;
  updated_at: string;
  status: "Basic Info" | "Details Added" | "Evaluated";
  details: Details | null;
  evaluation: Evaluation | null;
};
const base = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(
  /\/$/,
  "",
);
async function request<T>(
  path: string,
  method = "GET",
  data?: unknown,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${base}/api${path}`, {
      method,
      headers: data ? { "Content-Type": "application/json" } : undefined,
      body: data ? JSON.stringify(data) : undefined,
    });
  } catch {
    throw new Error(
      "Cannot connect to the server. Check that the backend is running and try again.",
    );
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail
              .map(
                (e: { loc: string[]; msg: string }) =>
                  `${e.loc.slice(1).join(" ")}: ${e.msg}`,
              )
              .join("; ")
          : "Something went wrong. Please try again.",
    );
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}
export const getCampaigns = (
  filters: { bank_name?: string; project?: string } = {},
) =>
  request<Campaign[]>(
    `/campaigns?${new URLSearchParams(Object.entries(filters).filter(([, v]) => v))}`,
  );
export const getCampaign = (id: string) =>
  request<Campaign>(`/campaigns/${id}`);
export const createCampaign = (data: CampaignInput) =>
  request<Campaign>("/campaigns", "POST", data);
export const updateCampaignDetails = (id: string, data: Details) =>
  request<Campaign>(`/campaigns/${id}/details`, "PUT", data);
export const evaluateCampaign = (id: string, data: EvaluationInput) =>
  request<Evaluation>(`/campaigns/${id}/evaluation`, "POST", data);

export const updateCampaign = (id: string, data: CampaignInput) =>
  request<Campaign>(`/campaigns/${id}`, "PUT", data);

export type BankOption = { id: number; name: string };
export type ProjectOption = { key: string; name: string };
export const getBanks = () => request<BankOption[]>("/banks");
export const getProjects = () => request<ProjectOption[]>("/projects");
export const addBank = (name: string) =>
  request<BankOption>("/banks", "POST", { name });
export const addProject = (name: string) =>
  request<ProjectOption>("/projects", "POST", { name });

export const deleteCampaign = (id: number) =>
  request<void>(`/campaigns/${id}`, "DELETE");
export const editBank = (id: number, name: string) =>
  request<BankOption>(`/banks/${id}`, "PUT", { name });
export const deleteBank = (id: number) =>
  request<void>(`/banks/${id}`, "DELETE");
export const editProject = (key: string, name: string) =>
  request<ProjectOption>(`/projects/${encodeURIComponent(key)}`, "PUT", {
    name,
  });
export const deleteProject = (key: string) =>
  request<void>(`/projects/${encodeURIComponent(key)}`, "DELETE");
