import { CaptureViewer } from "../components/CaptureViewer";
import { useCallback, useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, Camera, Trash2 } from "lucide-react";
import {
  Details,
  deleteCampaign,
  label,
  updateCampaignDetails,
} from "../api/campaigns";
import { Loading, Notice, Steps, useCampaign } from "../components/shared";
import { LabelEditor } from "./Label";
const empty: Details = {
  campaign_name: null,
  headline: null,
  subheadline: null,
  main_message: null,
  cta_text: null,
  notes: null,
  text_density: null,
  tone: null,
  feature_vs_benefit: null,
  emotional_vs_rational: null,
  customer_vs_product_focus: null,
};
const choices: Partial<Record<keyof Details, string[]>> = {
  text_density: ["low", "medium", "high"],
  feature_vs_benefit: ["feature_focused", "balanced", "benefit_focused"],
  emotional_vs_rational: ["emotional", "balanced", "rational"],
  customer_vs_product_focus: ["customer_focused", "balanced", "product_focused"],
};
export default function DetailsPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const review = params.get("review") === "1";
  const [showCaptures, setShowCaptures] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const { id, campaign, setCampaign, error } = useCampaign();
  const location = useLocation();
  const [data, setData] = useState<Details>(empty);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [success, setSuccess] = useState(
    location.state?.created
      ? "Campaign created successfully. Add your observations below."
      : "",
  );
  const [dirty, setDirty] = useState(false);
  useEffect(() => {
    if (campaign) setData(campaign.details || empty);
  }, [campaign]);
  function change(key: keyof Details, value: string) {
    setData({ ...data, [key]: value || null });
    setDirty(true);
    setSuccess("");
  }
  const saveObservations = useCallback(async () => {
    if (!dirty) return;
    const updated = await updateCampaignDetails(id, data);
    setCampaign(updated);
    setDirty(false);
  }, [id, data, dirty, setCampaign]);
  async function remove() {
    if (
      !campaign ||
      !window.confirm(
        `Delete ${campaign.details?.campaign_name || campaign.bank_name}? Its details and evaluation will also be permanently deleted.`,
      )
    )
      return;
    setDeleting(true);
    setSaveError("");
    try {
      await deleteCampaign(campaign.id);
      navigate("/", { state: { message: "Campaign deleted successfully." } });
    } catch (e) {
      setSaveError((e as Error).message);
      setDeleting(false);
    }
  }
  if (error)
    return (
      <>
        <Notice message={error} />
        <Link to="/">Back to dashboard</Link>
      </>
    );
  if (!campaign) return <Loading />;
  return (
    <>
      <Link className="back" to="/">
        <ArrowLeft size={15} /> All campaigns
      </Link>
      <div className="page-heading">
        <div>
          <div className="eyebrow">OBSERVE THE COMMUNICATION</div>
          <h1>Campaign details & labels</h1>
          <p>
            Review the captured page, check the prefilled fields, and complete labeling.
          </p>
        </div>
        <div className="campaign-header-actions">
          <button
            type="button"
            className="secondary capture-table-button"
            onClick={() => setShowCaptures(true)}
          >
            <Camera size={18} /> View captures
          </button>
          <button
            type="button"
            className="danger-link delete-icon"
            title="Delete campaign"
            aria-label="Delete campaign"
            aria-busy={deleting}
            disabled={deleting || saving}
            onClick={remove}
          >
            <Trash2 size={19} aria-hidden="true" />
          </button>
        </div>
      </div>
      {showCaptures && (
        <CaptureViewer
          campaignId={campaign.id}
          product={
            campaign.collection?.product_name ||
            campaign.details?.campaign_name ||
            campaign.bank_name
          }
          onClose={() => setShowCaptures(false)}
        />
      )}
      <Steps current={2} id={id} />
      <Notice message={success} success />
      <Notice message={saveError} />
      <LabelEditor
        key={`${id}:${review}`}
        id={id}
        review={review}
        additionalDirty={dirty}
        additionalTotal={Object.keys(empty).length}
        additionalRecorded={
          Object.keys(empty).filter((key) =>
            Boolean(data[key as keyof Details]?.trim()),
          ).length
        }
        saveAdditional={saveObservations}
        onSavingChange={setSaving}
      >
        <div className="additional-observations-content">
          <div className="section-heading">
            <h3>Message & content</h3>
            <p>
              Review the source page and record your observations. All fields are
              optional.
            </p>
          </div>
          <div className="form-grid">
            {(
              [
                "campaign_name",
                "cta_text",
                "headline",
                "subheadline",
                "main_message",
                "notes",
              ] as (keyof Details)[]
            ).map((key) => (
              <label
                key={key}
                className={["main_message", "notes"].includes(key) ? "full" : ""}
              >
                {key === "cta_text" ? "CTA text" : label(key)}
                {["main_message", "notes"].includes(key) ? (
                  <textarea
                    rows={3}
                    maxLength={10000}
                    value={data[key] || ""}
                    onChange={(e) => change(key, e.target.value)}
                    placeholder={
                      key === "main_message"
                        ? "What is the central message of this campaign?"
                        : "Additional observations and context…"
                    }
                  />
                ) : (
                  <input
                    maxLength={
                      ["campaign_name", "cta_text"].includes(key) ? 300 : 10000
                    }
                    value={data[key] || ""}
                    onChange={(e) => change(key, e.target.value)}
                  />
                )}
              </label>
            ))}
          </div>
          <div className="section-heading divided">
            <h3>Communication style</h3>
            <p>Describe the balance and tone of the campaign.</p>
          </div>
          <div className="form-grid">
            {(Object.keys(choices) as (keyof Details)[]).map((key) => (
              <label key={key}>
                {label(key)}
                <select
                  value={data[key] || ""}
                  onChange={(e) => change(key, e.target.value)}
                >
                  <option value="">Select an observation</option>
                  {choices[key]!.map((v) => (
                    <option key={v} value={v}>
                      {label(v)}
                    </option>
                  ))}
                </select>
              </label>
            ))}
            <label>
              Tone
              <input
                value={data.tone || ""}
                maxLength={120}
                placeholder="e.g. Friendly, reassuring, formal"
                onChange={(e) => change("tone", e.target.value)}
              />
            </label>
          </div>
        </div>
      </LabelEditor>
    </>
  );
}
