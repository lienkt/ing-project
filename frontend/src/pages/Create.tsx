import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, Link2 } from "lucide-react";
import {
  CampaignInput,
  createCampaign,
  getCampaign,
  updateCampaign,
  Project,
  getBanks,
  getProjects,
  BankOption,
  ProjectOption,
} from "../api/campaigns";
import { Loading, Notice, Steps } from "../components/shared";
export default function Create() {
  const [banks, setBanks] = useState<BankOption[]>([]);
  const [projects, setProjects] = useState<ProjectOption[]>([]);
  const { id } = useParams();
  const [loading, setLoading] = useState(Boolean(id));
  const [loadError, setLoadError] = useState("");
  const [success, setSuccess] = useState("");
  const navigate = useNavigate();
  const [data, setData] = useState<CampaignInput>({
    bank_name: "",
    project: "",
    campaign_url: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    setLoadError("");
    setSuccess("");
    setError("");
    if (!id) setData({ bank_name: "", project: "", campaign_url: "" });
    let active = true;
    setLoading(true);
    Promise.all([
      getBanks(),
      getProjects(),
      id ? getCampaign(id) : Promise.resolve(null),
    ])
      .then(([b, p, c]) => {
        if (active) {
          setBanks(b);
          setProjects(p);
          if (c)
            setData({
              bank_name: c.bank_name,
              project: c.project,
              campaign_url: c.campaign_url,
            });
          else setData((current) => ({ ...current, project: p[0]?.key || "" }));
        }
      })
      .catch((e) => {
        if (active) setLoadError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [id]);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      if (id) {
        await updateCampaign(id, data);
        setSuccess("Basic information saved successfully.");
      } else {
        const c = await createCampaign(data);
        navigate(`/campaigns/${c.id}`, { state: { created: true } });
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }
  if (loading) return <Loading />;
  if (loadError)
    return (
      <>
        <Notice message={loadError} />
        <Link to="/">Back to dashboard</Link>
      </>
    );
  return (
    <>
      <Link className="back" to="/">
        <ArrowLeft size={15} /> All campaigns
      </Link>
      <div className="page-heading">
        <div>
          <div className="eyebrow">GROW YOUR RESEARCH LIBRARY</div>
          <h1>{id ? "Edit basic information" : "Add a campaign"}</h1>
          <p>
            Start with the basics. You can add observations and scores later.
          </p>
        </div>
      </div>
      <Steps current={1} id={id} />
      <div className="form-layout">
        <form
          className="card form-card"
          onSubmit={submit}
          onChange={() => setSuccess("")}
        >
          <div className="section-heading">
            <h2>Basic information</h2>
          </div>
          <Notice message={error} />
          <Notice message={success} success />
          <label>
            Bank name <span className="required">*</span>
            <input
              required
              maxLength={120}
              placeholder="e.g. KBC"
              value={data.bank_name}
              onChange={(e) => setData({ ...data, bank_name: e.target.value })}
              list="banks"
            />
            <datalist id="banks">
              {banks.map((b) => (
                <option key={b.id}>{b.name}</option>
              ))}
            </datalist>
          </label>
          <label>
            Project <span className="required">*</span>
            <select
              required
              value={data.project}
              onChange={(e) =>
                setData({ ...data, project: e.target.value as Project })
              }
            >
              <option value="">Select a project</option>
              {projects.map((p) => (
                <option key={p.key} value={p.key}>
                  {p.name}
                </option>
              ))}
            </select>
            <small>The product or service category you’re analyzing.</small>
          </label>
          <label>
            Campaign URL <span className="required">*</span>
            <input
              required
              type="url"
              pattern="https?://.*"
              maxLength={2048}
              placeholder="https://www.bank.com/campaign"
              value={data.campaign_url}
              onChange={(e) =>
                setData({ ...data, campaign_url: e.target.value })
              }
            />
            <small>Link to the original campaign or product page.</small>
          </label>
          <div className="form-actions">
            <Link className="button secondary" to="/">
              Cancel
            </Link>
            <button disabled={saving}>
              {saving
                ? "Saving…"
                : id
                  ? "Save basic information"
                  : "Create campaign"}
              <ArrowRight size={16} />
            </button>
          </div>
        </form>
        <aside className="help-card">
          <Link2 size={23} />
          <h3>
            Every campaign starts
            <br />
            with a source.
          </h3>
          <p>
            Add the page you want to study. Then capture its message,
            communication style, and your own evaluation.
          </p>
          <div className="help-divider" />
          <span className="eyebrow">WHAT HAPPENS NEXT</span>
          <ol>
            <li>Add communication details</li>
            <li>Score five key dimensions</li>
            <li>Keep everything in one place</li>
          </ol>
        </aside>
      </div>
    </>
  );
}
