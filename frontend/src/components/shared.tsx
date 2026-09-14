import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowUpRight, Check, ChevronRight } from "lucide-react";
import { Campaign, getCampaign, label } from "../api/campaigns";
export function Notice({
  message,
  success = false,
}: {
  message: string;
  success?: boolean;
}) {
  return message ? (
    <div
      className={`notice ${success ? "success" : "error"}`}
      role={success ? "status" : "alert"}
    >
      {message}
    </div>
  ) : null;
}
export function Status({ value }: { value: Campaign["status"] }) {
  return (
    <span
      className={`badge ${value === "Evaluated" ? "evaluated" : value === "Details Added" ? "detailed" : "basic"}`}
    >
      <span />
      {value}
    </span>
  );
}
export function useCampaign() {
  const { id = "" } = useParams();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    setCampaign(null);
    setError("");
    getCampaign(id)
      .then((c) => {
        if (active) setCampaign(c);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [id]);
  return { id, campaign, setCampaign, error };
}
export function CampaignContext({ campaign }: { campaign: Campaign }) {
  return (
    <div className="context card">
      <div className="bank-avatar">
        {campaign.bank_name.slice(0, 2).toUpperCase()}
      </div>
      <div>
        <h3>{campaign.details?.campaign_name || campaign.bank_name}</h3>
        <p>
          {campaign.bank_name} <span className="dot">·</span>{" "}
          {label(campaign.project)} <span className="dot">·</span> Added{" "}
          {new Date(campaign.created_at).toLocaleDateString()}
        </p>
      </div>
      <a
        className="source"
        href={campaign.campaign_url}
        target="_blank"
        rel="noreferrer"
      >
        Visit source <ArrowUpRight size={16} />
      </a>
    </div>
  );
}
export function Steps({ current, id }: { current: number; id?: string }) {
  return (
    <div className="steps">
      {["Basic information", "Campaign details", "Evaluation"].map(
        (name, i) => (
          <div
            key={name}
            className={
              i + 1 === current ? "active" : i + 1 < current ? "done" : ""
            }
          >
            <span>{i + 1 < current ? <Check size={14} /> : i + 1}</span>
            {id ? (
              <Link
                to={`/campaigns/${id}${i === 0 ? "/edit" : i === 2 ? "/evaluate" : ""}`}
              >
                {name}
              </Link>
            ) : (
              name
            )}
            {i < 2 && <ChevronRight size={15} className="step-chevron" />}
          </div>
        ),
      )}
    </div>
  );
}
export function Loading() {
  return (
    <div className="loading" role="status">
      Loading campaigns…
    </div>
  );
}
