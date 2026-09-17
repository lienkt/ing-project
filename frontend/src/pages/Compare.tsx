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

  const selected = pages.filter((page) => selectedIds.includes(page.campaign_id));
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
  const bankNames = [...new Set(pages.map((page) => page.bank_name))];
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
          <div className="eyebrow">DATASET → LABEL → COMPARE → INSIGHTS</div>
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
          ) : (
            <>
              <p>Select a bank, or expand its pages to choose individually.</p>
              <div className="compare-selection-actions">
                <button
                  className="secondary"
                  type="button"
                  onClick={() => setSelectedIds(pages.map((page) => page.campaign_id))}
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
                const bankPages = pages.filter((page) => page.bank_name === bank);
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
                          <label>
                            <input
                              type="checkbox"
                              checked={selectedIds.includes(page.campaign_id)}
                              onChange={() => toggle(page.campaign_id)}
                            />
                            <span>
                              <strong>
                                {page.product_name || "Product not recorded"} · Page #
                                {page.campaign_id}
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
                          </label>
                          <FeatureStatus value={page.labeling_status} />
                          <div className="compare-page-links">
                            <a
                              href={page.page_url}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              Open source ↗
                            </a>
                            <Link to={`/campaigns/${page.campaign_id}/label`}>
                              Label features
                            </Link>
                          </div>
                          <p className="compare-url">{page.page_url}</p>
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
      {!loading && !error && category && pages.length > 0 && (
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
