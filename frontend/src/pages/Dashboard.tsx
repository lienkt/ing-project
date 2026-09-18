import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  CheckCheck,
  FileText,
  Layers3,
  Plus,
  Search,
  SlidersHorizontal,
  Trash2,
} from "lucide-react";
import { Campaign, deleteCampaign, getCampaigns, label } from "../api/campaigns";
import { getComparison, ComparisonPage } from "../api/compare";
import { Loading, Notice } from "../components/shared";
import { LabelingStatusHelp } from "../components/LabelingStatusHelp";
import { FeatureStatus } from "../components/FeatureControls";
export default function Dashboard() {
  const location = useLocation();
  useEffect(() => {
    if (location.hash !== "#label") return;
    const frame = requestAnimationFrame(() => {
      const target = document.getElementById("label");
      target?.focus();
      target?.scrollIntoView({ block: "start" });
    });
    return () => cancelAnimationFrame(frame);
  }, [location.key, location.hash]);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [actionError, setActionError] = useState("");
  const [success, setSuccess] = useState<string>(location.state?.message || "");
  async function remove(campaign: Campaign) {
    if (
      !window.confirm(
        `Delete ${campaign.details?.campaign_name || campaign.bank_name}? Its details and evaluation will also be permanently deleted.`,
      )
    )
      return;
    setDeleting(campaign.id);
    setActionError("");
    setSuccess("");
    try {
      await deleteCampaign(campaign.id);
      setCampaigns((current) => current.filter((c) => c.id !== campaign.id));
      setSuccess("Campaign deleted successfully.");
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setDeleting(null);
    }
  }
  const [metadata, setMetadata] = useState<Record<number, ComparisonPage>>({});
  const [metadataError, setMetadataError] = useState("");
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [bank, setBank] = useState("");
  const [project, setProject] = useState("");
  const [search, setSearch] = useState("");
  const [retry, setRetry] = useState(0);
  const [page, setPage] = useState(1);
  useEffect(() => {
    setPage(1);
  }, [bank, project, search]);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    getCampaigns()
      .then(async (c) => {
        if (!active) return;
        setCampaigns(c);
        setMetadata({});
        setMetadataError("");
        const results = await Promise.allSettled(
          [...new Set(c.map((page) => page.project))].map((category) =>
            getComparison(category),
          ),
        );
        if (!active) return;
        const entries: Record<number, ComparisonPage> = {};
        results.forEach((result) => {
          if (result.status === "fulfilled")
            result.value.pages.forEach((page) => {
              entries[page.campaign_id] = page;
            });
        });
        setMetadata(entries);
        if (results.some((result) => result.status === "rejected"))
          setMetadataError(
            "Some product and language details could not be loaded. Refresh the dataset to retry.",
          );
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [retry]);
  const filtered = campaigns.filter(
    (c) =>
      (!bank || c.bank_name === bank) &&
      (!project || c.project === project) &&
      `${c.bank_name} ${c.details?.campaign_name || ""} ${c.campaign_url}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  const pageSize = 10;
  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentPage = Math.min(page, pageCount);
  const firstVisiblePage = Math.max(1, Math.min(currentPage - 1, pageCount - 2));
  const pageNumbers = Array.from(
    { length: Math.min(3, pageCount) },
    (_, index) => firstVisiblePage + index,
  );
  const offset = (currentPage - 1) * pageSize;
  const visibleCampaigns = filtered.slice(offset, offset + pageSize);
  useEffect(() => {
    setPage((previous) => Math.min(previous, pageCount));
  }, [pageCount]);
  const evaluated = campaigns.filter((c) => c.labeling_status === "Completed").length;
  return (
    <>
      {location.hash === "#label" && (
        <section
          id="label"
          tabIndex={-1}
          className="card form-card compare-section"
          aria-labelledby="label-entry-title"
        >
          <h2 id="label-entry-title">Choose a campaign to label</h2>
          <p>
            Open a campaign by clicking its bank name to review and complete its labels.
          </p>
        </section>
      )}
      <div className="page-heading">
        <div>
          <h1>Campaign dataset</h1>
          <p>Choose a page, label its communication, then compare banks.</p>
        </div>
        <Link className="button" to="/campaigns/new">
          <Plus size={17} /> Add campaign
        </Link>
      </div>
      <div className="stats dataset-stats" role="region" aria-label="Campaign summary">
        <div className="stat card stat-total">
          <div>
            <span>Total campaigns</span>
            <strong>{loading || error ? "—" : campaigns.length}</strong>
            <small>Pages in your dataset</small>
          </div>
          <span className="stat-icon">
            <Layers3 size={21} />
          </span>
        </div>
        <div className="stat card stat-progress">
          <div>
            <span>In progress</span>
            <strong>{loading || error ? "—" : campaigns.length - evaluated}</strong>
            <small>Awaiting completed labeling</small>
          </div>
          <span className="stat-icon amber">
            <FileText size={21} />
          </span>
        </div>
        <div className="stat card stat-complete">
          <div>
            <span>Labeling completed</span>
            <strong>{loading || error ? "—" : evaluated}</strong>
            <small>Available for analytical review</small>
          </div>
          <span className="stat-icon green">
            <CheckCheck size={21} />
          </span>
        </div>
      </div>
      <div className="workflow-banner">
        <div className="workflow-intro">
          <span className="small-spark">✳</span>
          <div>
            <strong>From discovery to understanding</strong>
            <p>Dataset → Label → Compare: turn page observations into evidence.</p>
          </div>
        </div>
        <div className="mini-steps">
          <span>
            <b>1</b> Dataset
          </span>
          <ArrowRight size={14} />
          <span>
            <b>2</b> Label
          </span>
          <ArrowRight size={14} />
          <span>
            <b>3</b> Compare
          </span>
        </div>
      </div>
      <Notice message={metadataError} />
      <Notice message={actionError} />
      <Notice message={success} success />
      <section className="card library">
        <div className="library-heading">
          <div>
            <h2>
              Campaign library <span className="count">{campaigns.length}</span>
            </h2>
          </div>
          <SlidersHorizontal size={19} />
        </div>
        <div className="filters">
          <div className="search">
            <Search size={17} />
            <input
              aria-label="Search campaigns"
              placeholder="Search campaigns…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select
            aria-label="Filter by bank"
            value={bank}
            onChange={(e) => setBank(e.target.value)}
          >
            <option value="">All banks</option>
            {[...new Set(campaigns.map((c) => c.bank_name))].sort().map((b) => (
              <option key={b}>{b}</option>
            ))}
          </select>
          <select
            aria-label="Filter by project"
            value={project}
            onChange={(e) => setProject(e.target.value)}
          >
            <option value="">All projects</option>
            {[...new Set(campaigns.map((c) => c.project))].map((p) => (
              <option key={p} value={p}>
                {label(p)}
              </option>
            ))}
          </select>
        </div>
        {loading ? (
          <Loading />
        ) : error ? (
          <div className="empty">
            <Notice message={error} />
            <button className="secondary" onClick={() => setRetry(retry + 1)}>
              Try again
            </button>
          </div>
        ) : filtered.length ? (
          <>
            <div className="table-scroll">
              <table className="dataset-table">
                <thead>
                  <tr>
                    <th
                      scope="col"
                      aria-label="Row number"
                      className="dataset-row-number"
                    />
                    <th>BANK</th>
                    <th>PRODUCT</th>
                    <th>CATEGORY</th>
                    <th>LANGUAGE</th>
                    <th>
                      <span className="dataset-status-heading">
                        LABELING STATUS <LabelingStatusHelp />
                      </span>
                    </th>
                    <th>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleCampaigns.map((c, index) => (
                    <tr key={c.id}>
                      <td className="dataset-row-number">{offset + index + 1}</td>
                      <td>
                        <Link className="campaign-title" to={`/campaigns/${c.id}`}>
                          {c.bank_name}
                        </Link>
                        <a
                          className="table-url"
                          href={c.campaign_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Source <ArrowUpRight size={14} />
                        </a>
                      </td>
                      <td>
                        {metadata[c.id]?.product_name ||
                          c.collection?.product_name ||
                          "Not recorded"}
                      </td>
                      <td>{label(c.project)}</td>
                      <td>
                        {metadata[c.id]?.language ||
                          c.collection?.language ||
                          "Not recorded"}
                      </td>
                      <td>
                        <FeatureStatus value={c.labeling_status} />
                        <div>
                          <small>
                            {metadata[c.id]?.features?.source === "automatic" ||
                            metadata[c.id]?.features?.source === "manual_override"
                              ? "Auto-assisted"
                              : null}
                          </small>
                        </div>
                      </td>
                      <td>
                        <div className="row-actions">
                          <button
                            type="button"
                            className="danger-link delete-icon"
                            title="Delete campaign"
                            aria-label={`Delete campaign ${c.details?.campaign_name || c.bank_name}`}
                            aria-busy={deleting === c.id}
                            disabled={deleting !== null}
                            onClick={() => remove(c)}
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
            <div className="table-footer dataset-footer">
              <span role="status">
                Showing {offset + 1}–{offset + visibleCampaigns.length} of{" "}
                {filtered.length} campaigns
              </span>
              <nav className="dataset-pagination" aria-label="Dataset pagination">
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
          </>
        ) : (
          <div className="empty">
            <span className="empty-icon">
              <Layers3 size={28} />
            </span>
            <h3>
              {campaigns.length
                ? "No campaigns match your filters"
                : "Your next insight starts here"}
            </h3>
            <p>
              {campaigns.length
                ? "Try another bank, project, or search term."
                : "Add your first bank campaign to start building your research library."}
            </p>
            {campaigns.length ? (
              <button
                className="secondary"
                onClick={() => {
                  setBank("");
                  setProject("");
                  setSearch("");
                }}
              >
                Clear filters
              </button>
            ) : (
              <Link className="button" to="/campaigns/new">
                <Plus size={16} /> Add your first campaign
              </Link>
            )}
          </div>
        )}
      </section>
    </>
  );
}
