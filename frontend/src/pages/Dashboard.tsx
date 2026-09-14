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
import {
  Campaign,
  deleteCampaign,
  getCampaigns,
  label,
} from "../api/campaigns";
import { Loading, Notice, Status } from "../components/shared";
export default function Dashboard() {
  const location = useLocation();
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
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [bank, setBank] = useState("");
  const [project, setProject] = useState("");
  const [search, setSearch] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    getCampaigns()
      .then((c) => {
        if (active) setCampaigns(c);
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
  const evaluated = campaigns.filter((c) => c.status === "Evaluated").length;
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>
            Campaign overview<span className="heading-dot">.</span>
          </h1>
        </div>
        <Link className="button" to="/campaigns/new">
          <Plus size={17} /> Add campaign
        </Link>
      </div>
      <div className="stats">
        <div className="stat card">
          <div>
            <span>Total campaigns</span>
            <strong>{loading || error ? "—" : campaigns.length}</strong>
            <small>Your growing research library</small>
          </div>
          <span className="stat-icon">
            <Layers3 size={21} />
          </span>
        </div>
        <div className="stat card">
          <div>
            <span>In progress</span>
            <strong>
              {loading || error ? "—" : campaigns.length - evaluated}
            </strong>
            <small>Ready for a closer look</small>
          </div>
          <span className="stat-icon amber">
            <FileText size={21} />
          </span>
        </div>
        <div className="stat card">
          <div>
            <span>Evaluated</span>
            <strong>{loading || error ? "—" : evaluated}</strong>
            <small>Observations turned into insights</small>
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
            <p>Three simple steps to a complete campaign review.</p>
          </div>
        </div>
        <div className="mini-steps">
          <span>
            <b>1</b> Collect
          </span>
          <ArrowRight size={14} />
          <span>
            <b>2</b> Observe
          </span>
          <ArrowRight size={14} />
          <span>
            <b>3</b> Evaluate
          </span>
        </div>
      </div>
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
              <table>
                <thead>
                  <tr>
                    <th>CAMPAIGN / BANK</th>
                    <th>PROJECT</th>
                    <th>STATUS</th>
                    <th>DATE ADDED</th>
                    <th>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((c) => (
                    <tr key={c.id}>
                      <td>
                        <div className="table-bank">
                          <div
                            className={`bank-avatar ${c.bank_name.toLowerCase() === "ing" ? "orange" : ""}`}
                          >
                            {c.bank_name.slice(0, 2).toUpperCase()}
                          </div>
                          <div>
                            <Link
                              className="campaign-title"
                              to={`/campaigns/${c.id}`}
                            >
                              {c.details?.campaign_name || c.bank_name}
                            </Link>
                            {c.details?.campaign_name && (
                              <small>{c.bank_name}</small>
                            )}
                            <a
                              className="table-url"
                              title={c.campaign_url}
                              href={c.campaign_url}
                              target="_blank"
                              rel="noreferrer"
                            >
                              {new URL(c.campaign_url).hostname}
                              <ArrowUpRight size={12} />
                            </a>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className="project-tag">{label(c.project)}</span>
                      </td>
                      <td>
                        <Status value={c.status} />
                      </td>
                      <td className="date">
                        {new Date(c.created_at).toLocaleDateString(undefined, {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })}
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
            <div className="table-footer">
              Showing {filtered.length} of {campaigns.length} campaigns
              <span>Manually collected. Thoughtfully evaluated.</span>
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
      <div className="dashboard-note">
        <span className="online-dot" /> A space for human observation. All
        evaluations are entered manually.
      </div>
    </>
  );
}
