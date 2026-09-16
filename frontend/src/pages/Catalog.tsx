import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Trash2 } from "lucide-react";
import {
  addBank,
  addProject,
  getBanks,
  getProjects,
  editBank,
  editProject,
  deleteBank,
  deleteProject,
  BankOption,
  ProjectOption,
} from "../api/campaigns";
import { Notice } from "../components/shared";

type Option = BankOption | ProjectOption;
const identifier = (item: Option) =>
  "id" in item ? String(item.id) : item.key;
export default function Catalog({ kind }: { kind: "bank" | "project" }) {
  const [name, setName] = useState("");
  const [items, setItems] = useState<Option[]>([]);
  const [editing, setEditing] = useState<Option | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const title = kind === "bank" ? "Bank" : "Project";
  useEffect(() => {
    let active = true;
    (kind === "bank" ? getBanks() : getProjects())
      .then((data) => {
        if (active) setItems(data);
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
  }, [kind]);
  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const item = editing
        ? await ("id" in editing
            ? editBank(editing.id, name)
            : editProject(editing.key, name))
        : await (kind === "bank" ? addBank(name) : addProject(name));
      setItems((previous) =>
        [
          ...previous.filter(
            (p) => !editing || identifier(p) !== identifier(editing),
          ),
          item,
        ].sort((a, b) => a.name.localeCompare(b.name)),
      );
      setName("");
      setEditing(null);
      setSuccess(`${item.name} ${editing ? "updated" : "added"} successfully.`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }
  async function remove(item: Option) {
    if (
      !window.confirm(
        `Delete ${item.name}? Banks and projects used by campaigns cannot be deleted until those campaigns are reassigned or deleted.`,
      )
    )
      return;
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      await ("id" in item ? deleteBank(item.id) : deleteProject(item.key));
      setItems((previous) =>
        previous.filter((p) => identifier(p) !== identifier(item)),
      );
      if (editing && identifier(editing) === identifier(item)) {
        setEditing(null);
        setName("");
      }
      setSuccess(`${item.name} deleted successfully.`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">WORKSPACE OPTIONS</div>
          <h1>Manage {kind === "bank" ? "banks" : "projects"}</h1>
          <p>Maintain the options available when adding a campaign.</p>
        </div>
      </div>
      <Notice message={error} />
      <Notice message={success} success />
      <div className="form-layout">
        <form className="card form-card" onSubmit={submit}>
          <div className="section-heading">
            <h2>
              {editing ? "Edit" : "Add"} {kind}
            </h2>
          </div>
          <label>
            {title} name <span className="required">*</span>
            <input
              required
              disabled={saving}
              maxLength={kind === "bank" ? 120 : 40}
              value={name}
              placeholder={
                kind === "bank" ? "e.g. Argenta" : "e.g. Business loan"
              }
              onChange={(e) => {
                setName(e.target.value);
                setSuccess("");
              }}
            />
          </label>
          <div className="form-actions">
            {editing ? (
              <button
                type="button"
                className="secondary"
                disabled={saving}
                onClick={() => {
                  setEditing(null);
                  setName("");
                  setError("");
                }}
              >
                Cancel edit
              </button>
            ) : (
              <Link to="/campaigns/new" className="button secondary">
                Add campaign
              </Link>
            )}
            <button disabled={saving || loading}>
              <Plus size={16} />
              {saving ? "Saving…" : editing ? "Save changes" : `Add ${kind}`}
            </button>
          </div>
        </form>
        <aside className="card form-card">
          <div className="section-heading">
            <h2>Available {kind === "bank" ? "banks" : "projects"}</h2>
          </div>
          {loading ? (
            <p role="status">Loading options…</p>
          ) : items.length ? (
            <ul className="catalog-list">
              {items.map((item) => (
                <li key={identifier(item)}>
                  <span>{item.name}</span>
                  <div className="catalog-actions">
                    <button
                      type="button"
                      className="secondary"
                      disabled={saving}
                      onClick={() => {
                        setEditing(item);
                        setName(item.name);
                        setError("");
                        setSuccess("");
                      }}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className="danger-link delete-icon"
                      title={`Delete ${kind}`}
                      aria-label={`Delete ${kind} ${item.name}`}
                      disabled={saving}
                      onClick={() => remove(item)}
                    >
                      <Trash2 size={17} aria-hidden="true" />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p>
              No {kind === "bank" ? "banks" : "projects"} yet. Add one using the
              form.
            </p>
          )}
        </aside>
      </div>
    </>
  );
}
