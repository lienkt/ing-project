import { ScrapingResults } from "../components/ScrapingResults";
import { AddSourceDialog } from "../components/AddSourceDialog";
import { CaptureViewer } from "../components/CaptureViewer";
import { useEffect, useState } from "react";
import { Trash2 } from "lucide-react";
import { Link } from "react-router-dom";
import {
  Catalog,
  getSources,
  ImportResult,
  scrapeSources,
  addSource,
  deleteSource,
  Source,
  NewSource,
  CaptureMode,
} from "../api/collection";
import { label, getBanks, getProjects, ProjectOption } from "../api/campaigns";
import { Loading, Notice } from "../components/shared";

const sourceStatus = (source: Source) =>
  source.campaign_id ? "Imported" : source.error ? "Failed" : "Ready";

export default function Scraping() {
  const [captureId, setCaptureId] = useState<number | null>(null);
  const [captureProduct, setCaptureProduct] = useState("");
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [error, setError] = useState("");
  const [bank, setBank] = useState("");
  const [category, setCategory] = useState("");
  const [product, setProduct] = useState("");
  const [language, setLanguage] = useState("");
  const [status, setStatus] = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [adding, setAdding] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [banks, setBanks] = useState<{ name: string }[]>([]);
  const [projects, setProjects] = useState<ProjectOption[]>([]);
  const [draft, setDraft] = useState<NewSource>({
    bank: "",
    product_name: "",
    product_category: "",
    language: "English",
    url: "",
  });
  useEffect(() => {
    let active = true;
    Promise.all([getBanks(), getProjects()])
      .then(([b, p]) => {
        if (active) {
          setBanks(b);
          setProjects(p);
        }
      })
      .catch((e) => {
        if (active) setError((e as Error).message);
      });
    return () => {
      active = false;
    };
  }, []);
  async function createSource(event: React.FormEvent) {
    event.preventDefault();
    setAdding(true);
    setError("");
    try {
      await addSource(draft);
      setCatalog(await getSources());
      setBank("");
      setCategory("");
      setProduct("");
      setLanguage("");
      setStatus("");
      setFormOpen(false);
      setDraft({ ...draft, product_name: "", url: "" });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setAdding(false);
    }
  }
  const [results, setResults] = useState<ImportResult[]>([]);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    getSources()
      .then((value) => {
        if (active) {
          setCatalog(value);
          setError("");
        }
      })
      .catch((e) => {
        if (active) setError((e as Error).message);
      });
    return () => {
      active = false;
    };
  }, [retry]);
  async function run(ids = selected, mode: CaptureMode = "auto", recapture = false) {
    setRunning(true);
    setError("");
    setResults([]);
    try {
      const response = await scrapeSources(ids, mode, recapture);
      setResults(response.results);
      setSelected([]);
      setCatalog(await getSources());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRunning(false);
    }
  }
  async function removeSource(source: Source) {
    if (
      !window.confirm(
        `Delete ${source.product_name} from Scraping Sources? Saved campaigns, captures and labels will be kept.`,
      )
    )
      return;
    setDeleting(source.source_id);
    setError("");
    try {
      await deleteSource(source.source_id);
      setSelected((ids) => ids.filter((id) => id !== source.source_id));
      setCatalog(await getSources());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setDeleting(null);
    }
  }
  const visible =
    catalog?.sources.filter(
      (s) =>
        (!bank || bank === s.bank) &&
        (!category || category === s.product_category) &&
        (!product || product === s.product_name) &&
        (!language || language === s.language) &&
        (!status || status === sourceStatus(s)),
    ) ?? [];
  const pageSize = 10;
  const pageCount = Math.max(1, Math.ceil(visible.length / pageSize));
  const currentPage = Math.min(page, pageCount);
  const firstVisiblePage = Math.max(1, Math.min(currentPage - 1, pageCount - 2));
  const pageNumbers = Array.from(
    { length: Math.min(3, pageCount) },
    (_, index) => firstVisiblePage + index,
  );
  const offset = (currentPage - 1) * pageSize;
  const pageSources = visible.slice(offset, offset + pageSize);
  useEffect(() => {
    setPage(1);
  }, [bank, category, product, language, status]);
  useEffect(() => {
    setPage((previous) => Math.min(previous, pageCount));
  }, [pageCount]);
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Scraping Sources</h1>
          <p>Add product sources, capture evidence, and review labels.</p>
        </div>
        <button
          type="button"
          disabled={running || adding || deleting !== null}
          onClick={() => setFormOpen(true)}
        >
          Add source
        </button>
      </div>
      {captureId !== null && (
        <CaptureViewer
          key={captureId}
          campaignId={captureId}
          product={captureProduct}
          onClose={() => setCaptureId(null)}
        />
      )}
      <Notice message={error} />
      {error && (
        <button className="secondary" onClick={() => setRetry((v) => v + 1)}>
          Reload sources
        </button>
      )}
      {formOpen && (
        <AddSourceDialog saving={adding} onClose={() => setFormOpen(false)}>
          <form onSubmit={createSource}>
            <Notice message={error} />
            <fieldset className="feature-form-fields" disabled={adding || running}>
              <div className="form-grid">
                <label>
                  Bank
                  <select
                    required
                    value={draft.bank}
                    onChange={(e) => setDraft({ ...draft, bank: e.target.value })}
                  >
                    <option value="">Select bank</option>
                    {banks.map((b) => (
                      <option key={b.name}>{b.name}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Product name
                  <input
                    required
                    maxLength={300}
                    value={draft.product_name}
                    onChange={(e) =>
                      setDraft({ ...draft, product_name: e.target.value })
                    }
                  />
                </label>
                <label>
                  Category
                  <select
                    required
                    value={draft.product_category}
                    onChange={(e) =>
                      setDraft({ ...draft, product_category: e.target.value })
                    }
                  >
                    <option value="">Select category</option>
                    {projects.map((p) => (
                      <option key={p.key} value={p.key}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Language
                  <select
                    value={draft.language}
                    onChange={(e) => setDraft({ ...draft, language: e.target.value })}
                  >
                    {["English", "Dutch", "French", "Other"].map((l) => (
                      <option key={l}>{l}</option>
                    ))}
                  </select>
                </label>
                <label className="full">
                  URL
                  <input
                    type="url"
                    required
                    maxLength={2048}
                    value={draft.url}
                    onChange={(e) => setDraft({ ...draft, url: e.target.value })}
                  />
                </label>
              </div>
              <button type="submit">{adding ? "Adding…" : "Add to source list"}</button>
            </fieldset>
          </form>
        </AddSourceDialog>
      )}
      {!catalog && !error && <Loading />}
      {catalog && (
        <>
          <fieldset
            disabled={running || adding || deleting !== null}
            className="source-controls card"
          >
            <div className="filters">
              <label>
                Bank
                <select
                  value={bank}
                  onChange={(e) => {
                    setBank(e.target.value);
                    setSelected([]);
                  }}
                >
                  <option value="">All banks</option>
                  {catalog.banks.map((b) => (
                    <option key={b}>{b}</option>
                  ))}
                </select>
              </label>
              <label>
                Product category
                <select
                  value={category}
                  onChange={(e) => {
                    setCategory(e.target.value);
                    setSelected([]);
                  }}
                >
                  <option value="">All categories</option>
                  {catalog.categories.map((c) => (
                    <option key={c} value={c}>
                      {label(c)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Product
                <select
                  value={product}
                  onChange={(event) => {
                    setProduct(event.target.value);
                    setSelected([]);
                  }}
                >
                  <option value="">All products</option>
                  {[...new Set(catalog.sources.map((source) => source.product_name))]
                    .sort()
                    .map((value) => (
                      <option key={value} value={value}>
                        {value}
                      </option>
                    ))}
                </select>
              </label>
              <label>
                Language
                <select
                  value={language}
                  onChange={(event) => {
                    setLanguage(event.target.value);
                    setSelected([]);
                  }}
                >
                  <option value="">All languages</option>
                  {[...new Set(catalog.sources.map((source) => source.language))]
                    .sort()
                    .map((value) => (
                      <option key={value} value={value}>
                        {value}
                      </option>
                    ))}
                </select>
              </label>
              <label>
                Status
                <select
                  value={status}
                  onChange={(event) => {
                    setStatus(event.target.value);
                    setSelected([]);
                  }}
                >
                  <option value="">All statuses</option>
                  {["Ready", "Imported", "Failed"].map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="source-actions">
              <button
                className="secondary"
                onClick={() =>
                  setSelected(
                    visible
                      .filter((s) => !s.has_capture && s.capture_available)
                      .map((s) => s.source_id),
                  )
                }
              >
                Select all
              </button>
              <button className="secondary" onClick={() => setSelected([])}>
                Clear
              </button>
              <button
                disabled={!selected.length}
                onClick={() => void run(selected, "auto")}
              >
                {running ? "Capturing…" : `Scrape selected (${selected.length})`}
              </button>
            </div>
            <div className="table-scroll">
              <table className="source-table">
                <thead>
                  <tr>
                    <th aria-label="Select source" />
                    <th>BANK / PRODUCT</th>
                    <th>CATEGORY</th>
                    <th>LANGUAGE</th>
                    <th>AUTOMATION</th>
                    <th>STATUS</th>
                    <th>URL</th>
                    <th>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {pageSources.map((source) => (
                    <tr key={source.source_id}>
                      <td>
                        <input
                          type="checkbox"
                          aria-label={`Select ${source.bank} ${source.product_name}`}
                          checked={selected.includes(source.source_id)}
                          disabled={source.has_capture || !source.capture_available}
                          onChange={(e) =>
                            setSelected((ids) =>
                              e.target.checked
                                ? [...ids, source.source_id]
                                : ids.filter((id) => id !== source.source_id),
                            )
                          }
                        />
                      </td>
                      <td>
                        <strong>{source.bank}</strong>
                        <small>{source.product_name}</small>
                      </td>
                      <td>{label(source.product_category)}</td>
                      <td>{source.language}</td>
                      <td>
                        <span
                          className={`badge ${source.scraping.supported ? "evaluated" : "basic"}`}
                          title={source.scraping.message || undefined}
                        >
                          {source.scraping.supported
                            ? "Specialized scraper available"
                            : "Generic capture only"}
                        </span>
                        {source.scraping.supported && !source.scraping.available && (
                          <small>{source.scraping.message}</small>
                        )}
                      </td>
                      <td>
                        <span
                          className={`badge ${source.campaign_id ? "evaluated" : source.error ? "source-failed" : "basic"}`}
                        >
                          {sourceStatus(source)}
                        </span>
                        {source.error && (
                          <details className="source-error">
                            <summary>Error details</summary>
                            <p>{source.error}</p>
                          </details>
                        )}
                      </td>
                      <td>
                        <a
                          href={source.url}
                          title={source.url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {new URL(source.url).hostname} ↗
                        </a>
                        {source.campaign_id && (
                          <small>
                            <Link to={`/campaigns/${source.campaign_id}`}>
                              View campaign →
                            </Link>
                            <button
                              className="secondary"
                              onClick={() => {
                                setCaptureId(source.campaign_id!);
                                setCaptureProduct(source.product_name);
                              }}
                            >
                              View captures
                            </button>
                          </small>
                        )}
                      </td>
                      <td>
                        <div className="source-row-actions">
                          <button
                            type="button"
                            className={
                              source.has_capture || !source.auto_labeling_supported
                                ? "secondary"
                                : undefined
                            }
                            title={
                              source.has_capture
                                ? "Saves a new capture in history; labels stay unchanged"
                                : undefined
                            }
                            disabled={!source.capture_available}
                            onClick={() =>
                              void run(
                                [source.source_id],
                                !source.has_capture &&
                                  source.scraping.supported &&
                                  source.auto_labeling_supported
                                  ? "scrape_and_label"
                                  : "capture_only",
                                source.has_capture,
                              )
                            }
                          >
                            {source.has_capture
                              ? "Capture only"
                              : source.scraping.supported &&
                                  source.auto_labeling_supported
                                ? "Scrape & Auto-label"
                                : "Capture page"}
                          </button>
                          <button
                            type="button"
                            className="danger-link delete-icon"
                            title="Delete source"
                            aria-label={`Delete source ${source.product_name}`}
                            aria-busy={deleting === source.source_id}
                            onClick={() => void removeSource(source)}
                          >
                            <Trash2 size={17} aria-hidden="true" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {visible.length > 0 && (
              <div className="table-footer dataset-footer">
                <span role="status">
                  Showing {offset + 1}–{offset + pageSources.length} of {visible.length}{" "}
                  sources
                </span>
                <nav
                  className="dataset-pagination"
                  aria-label="Scraping sources pagination"
                >
                  <button
                    type="button"
                    className="secondary"
                    disabled={currentPage === 1}
                    onClick={() => setPage(currentPage - 1)}
                  >
                    ← Previous
                  </button>
                  {pageNumbers.map((number) => (
                    <button
                      key={number}
                      type="button"
                      className={`dataset-page-number${number === currentPage ? "" : " secondary"}`}
                      aria-label={`Page ${number}`}
                      aria-current={number === currentPage ? "page" : undefined}
                      onClick={() => setPage(number)}
                    >
                      {number}
                    </button>
                  ))}
                  <button
                    type="button"
                    className="secondary"
                    disabled={currentPage === pageCount}
                    onClick={() => setPage(currentPage + 1)}
                  >
                    Next →
                  </button>
                </nav>
              </div>
            )}
            {!visible.length && <p>No sources match these filters.</p>}
          </fieldset>
        </>
      )}
      {running && <p role="status">Importing selected pages…</p>}
      {!running && results.length > 0 && (
        <ScrapingResults
          results={results}
          sources={catalog?.sources ?? []}
          onClose={() => setResults([])}
        />
      )}
    </>
  );
}
