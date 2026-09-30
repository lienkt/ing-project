import { useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";
import { Link } from "react-router-dom";
import { X } from "lucide-react";
import { ImportResult, Source } from "../api/collection";

export function ScrapingResults({
  results,
  sources,
  onClose,
}: {
  results: ImportResult[];
  sources: Source[];
  onClose: () => void;
}) {
  const headingId = useId();
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
  return createPortal(
    <dialog
      ref={dialog}
      className="capture-dialog scraping-results-dialog"
      aria-labelledby={headingId}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
    >
      <section className="capture-viewer card">
        <header className="capture-heading">
          <h2 id={headingId}>Scraping results</h2>
          <button
            type="button"
            className="secondary"
            aria-label="Close scraping results"
            onClick={onClose}
          >
            <X size={18} aria-hidden="true" />
          </button>
        </header>
        <div className="capture-body">
          <ul className="scraping-results-list">
            {results.map((result) => (
              <li key={result.source_id}>
                <strong>
                  {sources.find((source) => source.source_id === result.source_id)
                    ?.product_name || result.source_id}
                </strong>
                <p>
                  {result.status === "success"
                    ? "Capture saved in Dataset"
                    : result.status === "existing"
                      ? "Already in Dataset — skipped"
                      : result.status === "manual_required"
                        ? result.message || "Manual scraping required"
                        : `Capture failed: ${result.error || "Unknown error"}`}
                </p>
              </li>
            ))}
          </ul>
          <div className="scraping-results-actions">
            <button type="button" className="secondary" onClick={onClose}>
              Close
            </button>
            <Link className="button" to="/">
              View Dataset
            </Link>
          </div>
        </div>
      </section>
    </dialog>,
    document.body,
  );
}
