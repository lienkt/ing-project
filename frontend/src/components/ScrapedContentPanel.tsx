import { useEffect, useState } from "react";
import { getScrapedContent, ScrapedContent } from "../api/collection";

export function ScrapedContentPanel({
  campaignId,
  onViewCapture,
}: {
  campaignId: number;
  onViewCapture: () => void;
}) {
  const [page, setPage] = useState<ScrapedContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    getScrapedContent(campaignId)
      .then((data) => {
        if (active) setPage(data);
      })
      .catch((e) => {
        if (active) setError((e as Error).message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [campaignId, retry]);
  return (
    <section className="card form-card scraped-content">
      <div className="capture-heading">
        <div>
          <span className="capture-eyebrow">COLLECTED FROM THE WEBSITE</span>
          <h2>Scraped content</h2>
        </div>
        {page && (
          <button type="button" className="secondary" onClick={onViewCapture}>
            View capture
          </button>
        )}
      </div>
      {loading ? (
        <p role="status">Loading collected content…</p>
      ) : error ? (
        <div role="alert">
          <p>{error}</p>
          <button type="button" onClick={() => setRetry((v) => v + 1)}>
            Try again
          </button>
        </div>
      ) : !page ? (
        <p>
          No scraped content is saved for this campaign. You can still record your
          observations below.
        </p>
      ) : (
        <>
          <p>
            {page.source.product_name} · {page.source.language} · Collected{" "}
            {new Date(page.scraped_at).toLocaleString()}
            {page.is_demo ? " · Synthetic demo" : ""}
          </p>
          <p className="muted">
            Collected evidence for your review. The observation fields and feature
            labels below are saved separately.
          </p>
          <h3>{page.headline || page.title}</h3>
          <a href={page.source.url} target="_blank" rel="noreferrer">
            Open source website ↗
          </a>
          <div className="capture-supporting">
            {(
              [
                ["Paragraphs", page.paragraphs],
                ["Headings", page.headings],
                ["Bullet items", page.bullets],
                ["Tables", page.tables],
              ] as const
            ).map(([name, items]) => (
              <details key={name} open={name === "Paragraphs" && !!items?.length}>
                <summary>
                  {name} ({items?.length ?? 0} extracted)
                </summary>
                <div className="capture-text">
                  {items?.length ? (
                    items.map((text, i) => <p key={i}>{text}</p>)
                  ) : (
                    <p>
                      No {name.toLowerCase()} were extracted. This does not confirm they
                      are absent from the page.
                    </p>
                  )}
                </div>
              </details>
            ))}
            <details>
              <summary>Combined extracted text</summary>
              <div className="capture-text">{page.text || "No text extracted."}</div>
            </details>
            {!!page.warnings.length && (
              <details>
                <summary>Collection notes</summary>
                {page.warnings.map((note, i) => (
                  <p key={i}>{note}</p>
                ))}
              </details>
            )}
          </div>
        </>
      )}
    </section>
  );
}
