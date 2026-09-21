import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { getProjects, label, ProjectOption } from "../api/campaigns";
import { analyticalFields, ComparisonPage, getComparison } from "../api/compare";
import { isFilled } from "../api/features";
import { Notice } from "../components/shared";
import { FeatureStatus } from "../components/FeatureControls";
import { ComparisonTable } from "../components/ComparisonTable";
import { ComparisonChart } from "../components/ComparisonChart";
import { ComparisonFindings } from "../components/ComparisonFindings";

export default function Compare() {
  const { hash, key: locationKey } = useLocation();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const category = params.get("product_category") || "";
  const [categories, setCategories] = useState<ProjectOption[]>([]);
  const [pages, setPages] = useState<ComparisonPage[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [labelingStatus, setLabelingStatus] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    setPages([]);
    setSelectedIds([]);
    Promise.all([
      getProjects(),
      category ? getComparison(category) : Promise.resolve(null),
    ])
      .then(([options, comparison]) => {
        if (!active) return;
        setCategories(options);
        setPages(comparison?.pages ?? []);
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
  }, [category, retry]);

  const filteredPages = pages.filter(
    (page) => !labelingStatus || page.labeling_status === labelingStatus,
  );
  const selected = filteredPages.filter((page) =>
    selectedIds.includes(page.campaign_id),
  );
  useEffect(() => {
    if (hash === "#insights") {
      const frame = requestAnimationFrame(() => {
        const target = document.getElementById("insights");
        target?.focus();
        target?.scrollIntoView({ block: "start" });
      });
      return () => cancelAnimationFrame(frame);
    }
  }, [hash, locationKey, selected.length, loading]);
  const observedPages = selected.filter((page) =>
    analyticalFields.some((field) => isFilled(page.features?.[field.key])),
  );
  const mixedLanguages =
    new Set(selected.map((page) => page.language).filter(Boolean)).size > 1;
  const bankNames = [...new Set(filteredPages.map((page) => page.bank_name))];
  function toggle(id: number) {
    setSelectedIds((previous) =>
      previous.includes(id)
        ? previous.filter((value) => value !== id)
        : [...previous, id],
    );
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">DATASET → LABEL → COMPARE</div>
          <h1>Compare Campaigns</h1>
          <p>Compare how banks communicate similar products.</p>
        </div>
        <Link className="button secondary" to="/">
          Back to dataset
        </Link>
      </div>
      {hash === "#insights" && selected.length < 2 && (
        <section
          id="insights"
          tabIndex={-1}
          className="card form-card compare-section"
          aria-labelledby="insights-entry-title"
        >
          <h2 id="insights-entry-title">Choose pages to see insights</h2>
          <p>
            Select a product category and at least two pages below. Their recorded
            features will appear as factual observations here.
          </p>
          <a className="button secondary" href="#comparison-filters">
            Choose pages
          </a>
        </section>
      )}
      <section
        id="comparison-filters"
        className="card form-card compare-section"
        aria-label="Comparison filters"
      >
        <h2>Choose pages to compare</h2>
        <label className="compare-category">
          Product category
          <select
            value={category}
            onChange={(e) => {
              setPages([]);
              setSelectedIds([]);
              navigate({
                pathname: "/compare",
                search: e.target.value
                  ? `?${new URLSearchParams({ product_category: e.target.value })}`
                  : "",
                hash,
              });
            }}
          >
            <option value="">Select a product category</option>
            {category && !categories.some((option) => option.key === category) && (
              <option value={category}>{label(category)}</option>
            )}
            {categories.map((option) => (
              <option key={option.key} value={option.key}>
                {option.name}
              </option>
            ))}
          </select>
        </label>
        <label className="compare-category">
          Labeling status
          <select
            value={labelingStatus}
            onChange={(e) => {
              const status = e.target.value;
              setLabelingStatus(status);
              setSelectedIds((previous) =>
                previous.filter((id) =>
                  pages.some(
                    (page) =>
                      page.campaign_id === id &&
                      (!status || page.labeling_status === status),
                  ),
                ),
              );
            }}
          >
            <option value="">All statuses</option>
            {["Not Started", "In Progress", "Completed"].map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </label>
        <Notice message={error} />
        {error && (
          <button
            type="button"
            className="secondary"
            onClick={() => setRetry((value) => value + 1)}
          >
            Try again
          </button>
        )}
        {loading ? (
          <p role="status">Loading comparison candidates…</p>
        ) : (
          !error &&
          (!category ? (
            <p>Choose one category to see its campaign pages.</p>
          ) : pages.length === 0 ? (
            <div className="empty">
              <h3>No pages in this category</h3>
              <p>Add a campaign and label its features to start a comparison.</p>
              <Link className="button" to="/campaigns/new">
                Add campaign
              </Link>
            </div>
          ) : filteredPages.length === 0 ? (
            <div className="empty">
              <h3>No pages match this labeling status</h3>
              <button
                type="button"
                className="secondary"
                onClick={() => setLabelingStatus("")}
              >
                Show all statuses
              </button>
            </div>
          ) : (
            <>
              <p>Select a bank, or expand its pages to choose individually.</p>
              <div className="compare-selection-actions">
                <button
                  className="secondary"
                  type="button"
                  onClick={() =>
                    setSelectedIds(filteredPages.map((page) => page.campaign_id))
                  }
                >
                  Select all pages
                </button>
                <button
                  className="secondary"
                  type="button"
                  onClick={() => setSelectedIds([])}
                >
                  Clear selection
                </button>
                <span role="status">{selected.length} pages selected</span>
              </div>
              {bankNames.map((bank) => {
                const bankPages = filteredPages.filter(
                  (page) => page.bank_name === bank,
                );
                const allSelected = bankPages.every((page) =>
                  selectedIds.includes(page.campaign_id),
                );
                return (
                  <fieldset className="compare-bank" key={bank}>
                    <legend>{bank}</legend>
                    <button
                      type="button"
                      className={`bank-select ${allSelected ? "selected" : "secondary"}`}
                      aria-pressed={allSelected}
                      onClick={() =>
                        setSelectedIds((previous) =>
                          allSelected
                            ? previous.filter(
                                (id) =>
                                  !bankPages.some((page) => page.campaign_id === id),
                              )
                            : [
                                ...new Set([
                                  ...previous,
                                  ...bankPages.map((page) => page.campaign_id),
                                ]),
                              ],
                        )
                      }
                    >
                      {allSelected ? "✓ Selected" : "Select bank"}
                    </button>
                    <details className="candidate-disclosure">
                      <summary>
                        Review {bankPages.length}{" "}
                        {bankPages.length === 1 ? "page" : "pages"}
                      </summary>
                      {bankPages.map((page) => (
                        <div className="compare-candidate" key={page.campaign_id}>
                          <div className="compare-candidate-info">
                            <input
                              aria-label={`Select ${page.product_name || "product"} · Page ${page.campaign_id}`}
                              type="checkbox"
                              checked={selectedIds.includes(page.campaign_id)}
                              onChange={() => toggle(page.campaign_id)}
                            />
                            <span className="compare-candidate-details">
                              <strong>
                                <Link to={`/campaigns/${page.campaign_id}`}>
                                  {page.product_name || "Product not recorded"}
                                </Link>{" "}
                                · Page #{page.campaign_id}
                              </strong>
                              <small>
                                {label(page.product_category)} ·{" "}
                                {page.language || "Language not recorded"} ·{" "}
                                {page.bank_type || "Bank type not recorded"}
                              </small>
                              <small>
                                Reviewed: {page.capture_date || "Not recorded"}
                              </small>
                            </span>
                          </div>
                          <FeatureStatus value={page.labeling_status} />
                        </div>
                      ))}
                    </details>
                  </fieldset>
                );
              })}
            </>
          ))
        )}
      </section>
      {!loading && !error && category && filteredPages.length > 0 && (
        <>
          <div className="sample-summary" aria-label="Selected sample">
            <strong>
              {new Set(selected.map((page) => page.bank_name)).size} banks
            </strong>
            <strong>{selected.length} pages</strong>
            <span>
              {categories.find((option) => option.key === category)?.name ||
                label(category)}
            </span>
          </div>
          <details className="sample-notes compare-section">
            <summary>
              Comparison notes{mixedLanguages ? " · Mixed languages" : ""}
              {selected.some((page) => page.labeling_status !== "Completed")
                ? " · Incomplete labels"
                : ""}
            </summary>
            <p>
              Results cover selected pages only, not whole banks. Missing values appear
              as —.
            </p>
            {mixedLanguages && (
              <p>Mixed languages may affect wording and word counts.</p>
            )}
            {selected.some((page) => page.labeling_status !== "Completed") && (
              <p>Some labels are unfinished. Results may change.</p>
            )}
            {selected.some(
              (page) => !page.capture_date || !page.language || !page.product_name,
            ) && (
              <p>Some pages are missing a product name, language, or review date.</p>
            )}
          </details>
          {selected.length < 2 ? (
            <div className="card empty">
              <h2>Select at least two pages</h2>
              <p>
                Choose pages above to compare their stored features. If only one page
                exists, add and label another campaign in this category.
              </p>
            </div>
          ) : (
            <>
              {observedPages.length < 2 && (
                <div className="notice" role="status">
                  Not enough labeled pages for analytical findings. Label at least two
                  selected pages using the links above. The table shows available data
                  and missing values.
                </div>
              )}
              <ComparisonFindings pages={selected} />
              <ComparisonChart pages={selected} />
              <ComparisonTable pages={selected} />
            </>
          )}
        </>
      )}
    </>
  );
}
