import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Camera, ExternalLink, X } from "lucide-react";
import { Capture, captureArtifactUrl, getCaptures } from "../api/collection";

export function CaptureViewer({
  campaignId,
  product,
  onClose,
}: {
  campaignId: number;
  product: string;
  onClose: () => void;
}) {
  const [captures, setCaptures] = useState<Capture[]>([]);
  const [selected, setSelected] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const previous = document.activeElement;
    const overflow = document.body.style.overflow;
    dialog.current?.showModal();
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = overflow;
      if (previous instanceof HTMLElement && previous.isConnected) previous.focus();
    };
  }, []);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    setCaptures([]);
    getCaptures(campaignId)
      .then((rows) => {
        if (!active) return;
        setCaptures(rows);
        setSelected(rows[0]?.id || "");
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
  const current = captures.find((c) => c.id === selected);
  return createPortal(
    <dialog
      ref={dialog}
      className="capture-dialog"
      aria-label={`Page captures for ${product}`}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        if (event.target !== event.currentTarget) return;
        const rect = event.currentTarget.getBoundingClientRect();
        if (
          event.clientX < rect.left ||
          event.clientX > rect.right ||
          event.clientY < rect.top ||
          event.clientY > rect.bottom
        )
          onClose();
      }}
    >
      <section
        className="capture-viewer card"
        aria-label={`Page captures for ${product}`}
      >
        <header className="capture-heading">
          <div>
            <h2>{product}</h2>
          </div>
          <button
            className="secondary"
            onClick={onClose}
            aria-label="Close capture viewer"
          >
            <X size={18} />
          </button>
        </header>
        <div
          className="capture-body"
          tabIndex={0}
          role="region"
          aria-label="Capture content"
        >
          {loading && <p role="status">Loading captures…</p>}
          {error && (
            <div role="alert">
              <p>{error}</p>
              <button onClick={() => setRetry((n) => n + 1)}>Try again</button>
            </div>
          )}
          {!loading && !error && !current && (
            <div className="capture-empty">
              <Camera size={32} />
              <h3>No saved captures yet</h3>
              <p>
                Use Tools → Scraping to capture this product. Older imports may need to
                be captured again.
              </p>
            </div>
          )}
          {current && (
            <>
              <div className="capture-toolbar">
                <label>
                  Capture history · {captures.length} saved
                  <select
                    value={selected}
                    onChange={(e) => setSelected(e.target.value)}
                  >
                    {captures.map((c, i) => (
                      <option key={c.id} value={c.id}>
                        {i === 0 ? "Latest · " : ""}
                        {new Date(c.page.scraped_at).toLocaleString()}
                        {c.page.is_demo ? " · Demo" : ""}
                      </option>
                    ))}
                  </select>
                </label>
                {current.has_screenshot && (
                  <a
                    className="button"
                    href={captureArtifactUrl(current.id, "screenshot.png")}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <ExternalLink size={16} /> Open full-size screenshot
                  </a>
                )}
                {current.has_screenshot && (
                  <a
                    className="button secondary"
                    href={captureArtifactUrl(current.id, "dom.json")}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <ExternalLink size={16} /> Open dom.json
                  </a>
                )}
              </div>
              <p className="capture-caption">
                Captured {new Date(current.page.scraped_at).toLocaleString()} · Saved
                labels are unchanged when a new capture is added.
              </p>
              {current.has_screenshot ? (
                <a
                  className="capture-preview"
                  href={captureArtifactUrl(current.id, "screenshot.png")}
                  target="_blank"
                  rel="noreferrer"
                  aria-label={`Open full-size screenshot of ${product}`}
                >
                  <img
                    key={current.id}
                    src={captureArtifactUrl(current.id, "screenshot.png")}
                    alt={`Saved website screenshot of ${product}`}
                  />
                  <span>Screenshot preview · Click to view the full page ↗</span>
                </a>
              ) : (
                <div className="capture-empty">
                  <Camera size={30} />
                  <h3>No screenshot available</h3>
                  <p>
                    {current.page.is_demo
                      ? "This is synthetic demo content, not a captured website."
                      : "This capture contains text only."}
                  </p>
                </div>
              )}
              <div className="capture-supporting">
                {(
                  [
                    ["Headings", current.page.headings],
                    ["Paragraphs", current.page.paragraphs],
                    ["Bullet items", current.page.bullets],
                    ["Tables", current.page.tables],
                  ] as const
                ).map(([name, items]) => (
                  <details key={`${current.id}-${name}`}>
                    <summary>
                      {name} ({items?.length ?? 0} extracted)
                    </summary>
                    <div className="capture-text">
                      {items?.length ? (
                        items.map((text, i) => <p key={i}>{text}</p>)
                      ) : (
                        <p>No items extracted.</p>
                      )}
                    </div>
                  </details>
                ))}

                <details key={`${current.id}-text`}>
                  <summary>Extracted text</summary>
                  <p>
                    This is the text collected from the page, separate from the
                    screenshot.
                  </p>
                  <div className="capture-text">
                    {current.page.text || "No text was extracted."}
                  </div>
                </details>
                <details key={`${current.id}-notes`}>
                  <summary>Capture notes & technical details</summary>
                  {current.page.warnings.map((w, i) => (
                    <p key={i}>{w}</p>
                  ))}
                </details>
              </div>
            </>
          )}
        </div>
      </section>
    </dialog>,
    document.body,
  );
}
