import { useEffect, useState } from "react";
import { Camera, ExternalLink } from "lucide-react";
import { ComparisonPage } from "../api/compare";
import { Capture, captureArtifactUrl, getCaptures } from "../api/collection";
import { CaptureViewer } from "./CaptureViewer";

function EvidenceCard({ page }: { page: ComparisonPage }) {
  const [capture, setCapture] = useState<Capture | null>(null);
  const [status, setStatus] = useState("Loading capture…");
  const [retry, setRetry] = useState(0);
  const [viewing, setViewing] = useState(false);
  const [imageFailed, setImageFailed] = useState(false);
  useEffect(() => {
    let active = true;
    setStatus("Loading capture…");
    setImageFailed(false);
    getCaptures(page.campaign_id)
      .then((rows) => {
        if (!active) return;
        setCapture(rows[0] ?? null);
        setStatus(rows[0]?.has_screenshot ? "" : "No saved screenshot");
      })
      .catch(() => {
        if (active) setStatus("Could not load capture");
      });
    return () => {
      active = false;
    };
  }, [page.campaign_id, retry]);
  return (
    <article className="compare-evidence-card">
      <strong>{page.bank_name}</strong>
      <button
        className="compare-evidence-preview"
        onClick={() => setViewing(true)}
        aria-label={`View captures for ${page.bank_name} · ${page.product_name || page.campaign_id}`}
      >
        {capture?.has_screenshot && !imageFailed ? (
          <img
            loading="lazy"
            src={captureArtifactUrl(capture.id, "screenshot.png")}
            alt={`${page.bank_name} campaign screenshot`}
            onError={() => setImageFailed(true)}
          />
        ) : (
          <span>
            <Camera size={24} />
            {imageFailed ? "Screenshot unavailable" : status}
          </span>
        )}
      </button>
      {status === "Could not load capture" && (
        <button className="secondary" onClick={() => setRetry((value) => value + 1)}>
          Retry
        </button>
      )}
      <span>{page.product_name || `Page #${page.campaign_id}`}</span>
      <small>
        {capture
          ? `Captured ${new Date(capture.page.scraped_at).toLocaleDateString()}`
          : "No capture date available"}
      </small>
      <a href={page.page_url} target="_blank" rel="noreferrer">
        Visit source <ExternalLink size={13} />
      </a>
      {viewing && (
        <CaptureViewer
          campaignId={page.campaign_id}
          product={`${page.bank_name} · ${page.product_name || "Product"}`}
          onClose={() => setViewing(false)}
        />
      )}
    </article>
  );
}

export function ComparisonEvidence({ pages }: { pages: ComparisonPage[] }) {
  return (
    <section className="card compare-evidence">
      <h2>
        <Camera size={20} /> Visual evidence
      </h2>
      <p>
        Saved campaign pages behind the labels. Select a screenshot to explore its
        capture.
      </p>
      <div className="compare-evidence-grid">
        {pages.map((page) => (
          <EvidenceCard key={page.campaign_id} page={page} />
        ))}
      </div>
    </section>
  );
}
