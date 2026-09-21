import { FieldLabel } from "../components/FieldHelp";
import { type ReactNode, useCallback, useEffect, useRef, useState } from "react";
import { Link, Navigate, useParams, useSearchParams } from "react-router-dom";
import { Check } from "lucide-react";
import { label } from "../api/campaigns";
import {
  completeFeatures,
  emptyFeatures,
  FeatureInput,
  FeatureKey,
  FeatureResponse,
  featureFields,
  getFeatures,
  isFilled,
  saveFeatures,
  withDerivedValues,
} from "../api/features";
import {
  BooleanChoice,
  FeatureStatus,
  RatingScale,
} from "../components/FeatureControls";
import { Loading, Notice } from "../components/shared";

import { getSuggestions, Proposal, reviewSuggestions } from "../api/collection";

export default function LabelPage() {
  const { id = "" } = useParams();
  const [params] = useSearchParams();
  const query = params.toString();
  return <Navigate replace to={`/campaigns/${id}${query ? `?${query}` : ""}`} />;
}

export function LabelEditor({
  id,
  review,
  children,
  additionalDirty = false,
  additionalRecorded = 0,
  additionalTotal = 0,
  saveAdditional,
  onSavingChange,
}: {
  id: string;
  review: boolean;
  children?: ReactNode;
  additionalDirty?: boolean;
  additionalRecorded?: number;
  additionalTotal?: number;
  saveAdditional?: () => Promise<void>;
  onSavingChange?: (saving: boolean) => void;
}) {
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [reviewPending, setReviewPending] = useState(review);
  const [activeSection, setActiveSection] = useState(0);
  const sectionHeading = useRef<HTMLHeadingElement>(null);
  function goToSection(index: number) {
    setActiveSection(index);
    requestAnimationFrame(() => {
      sectionHeading.current?.focus();
      sectionHeading.current?.scrollIntoView({ block: "start", behavior: "auto" });
    });
  }
  const [response, setResponse] = useState<FeatureResponse | null>(null);
  const [data, setData] = useState<FeatureInput>({
    ...emptyFeatures,
    labeling_notes: null,
  });
  const [loadError, setLoadError] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [, setSaved] = useState(false);
  const [retry, setRetry] = useState(0);
  const storageKey = `campaign-feature-draft:${id}`;
  useEffect(() => {
    let active = true;
    setLoadError("");
    Promise.all([getFeatures(id), getSuggestions(id)])
      .then(([result, suggestion]) => {
        if (!active) return;
        const loaded: FeatureInput = { ...emptyFeatures, labeling_notes: null };
        for (const field of featureFields)
          Object.assign(loaded, { [field.key]: result.features?.[field.key] ?? null });
        loaded.labeling_notes = result.features?.labeling_notes ?? null;
        setProposal(suggestion);
        if (review) {
          if (localStorage.getItem(storageKey))
            throw new Error(
              "You have an unsaved manual draft. Open manual labeling and save it before reviewing suggestions.",
            );
          if (!suggestion || suggestion.reviewed)
            throw new Error(
              "No pending suggestions. Open manual labeling or generate suggestions again.",
            );
          for (const field of featureFields) {
            if (
              loaded[field.key] === null &&
              suggestion.values[field.key] !== undefined
            ) {
              Object.assign(loaded, { [field.key]: suggestion.values[field.key] });
            }
          }
        }
        try {
          const raw = review ? null : localStorage.getItem(storageKey);
          if (raw) {
            const draft: unknown = JSON.parse(raw);
            if (draft && typeof draft === "object") {
              for (const key of [
                ...featureFields.map((f) => f.key),
                "labeling_notes",
              ] as const) {
                if (key in draft)
                  Object.assign(loaded, {
                    [key]: (draft as Record<string, unknown>)[key],
                  });
              }
              setDirty(true);
            }
          }
        } catch {
          /* Server values remain available if local storage is unavailable. */
        }
        setData(withDerivedValues(loaded));
        setResponse(result);
      })
      .catch((e) => {
        if (active) setLoadError((e as Error).message);
      });
    return () => {
      active = false;
    };
  }, [id, storageKey, retry, review]);

  function change(
    key: FeatureKey | "labeling_notes",
    value: string | number | boolean | null,
  ) {
    const next = withDerivedValues({ ...data, [key]: value });
    setData(next);
    setDirty(true);
    setSaved(false);
    setError("");
    try {
      if (!reviewPending) localStorage.setItem(storageKey, JSON.stringify(next));
    } catch {
      setError("Local recovery is unavailable. Save Draft before leaving this page.");
    }
  }
  const save = useCallback(
    async (complete = false) => {
      if (saving) return;
      const missing = featureFields.filter((f) => !isFilled(data[f.key]));
      if (complete && missing.length === featureFields.length) {
        setError("Label at least one feature before completing.");
        return;
      }
      if (
        complete &&
        missing.length > 0 &&
        !window.confirm(
          `${missing.length} features are unset, including ${missing
            .slice(0, 5)
            .map((f) => label(f.key))
            .join(", ")}. Complete with these omissions?`,
        )
      )
        return;
      setSaving(true);
      onSavingChange?.(true);
      setError("");
      try {
        await saveAdditional?.();
        let result = response;
        if (reviewPending && proposal) {
          result = await reviewSuggestions(id, proposal.token, data);
          setResponse(result);
          setDirty(false);
          setReviewPending(false);
          setProposal({ ...proposal, reviewed: true });
        } else if (!complete || dirty || !result?.features) {
          result = await saveFeatures(id, data);
          setResponse(result);
          setDirty(false);
          try {
            localStorage.removeItem(storageKey);
          } catch {
            /* Saving to the server succeeded. */
          }
        }
        if (complete) result = await completeFeatures(id, missing.length > 0);
        setResponse(result);
        setSaved(true);
      } catch (e) {
        setError(`Error saving: ${(e as Error).message}`);
      } finally {
        setSaving(false);
        onSavingChange?.(false);
      }
    },
    [
      data,
      dirty,
      id,
      response,
      saving,
      storageKey,
      reviewPending,
      proposal,
      saveAdditional,
      onSavingChange,
    ],
  );

  useEffect(() => {
    if (reviewPending || (!dirty && !additionalDirty) || saving || error || !response)
      return;
    const timer = window.setTimeout(() => {
      void save();
    }, 1200);
    return () => window.clearTimeout(timer);
  }, [dirty, additionalDirty, saving, error, response, save, reviewPending]);

  if (loadError)
    return (
      <>
        <Notice message={loadError} />
        <button onClick={() => setRetry((v) => v + 1)}>Try again</button>{" "}
        <Link to={`/campaigns/${id}`}>Manual labeling</Link> ·{" "}
        <Link to="/">All campaigns</Link>
      </>
    );
  if (!response) return <Loading />;
  const campaign = response.campaign;
  const filled = featureFields.filter((f) => isFilled(data[f.key])).length;
  const progress = Math.round((100 * filled) / featureFields.length);
  const featureSections = [...new Set(featureFields.map((f) => f.section))];
  const sections = children
    ? [...featureSections, "Additional campaign observations"]
    : featureSections;
  return (
    <>
      <div className="page-heading">
        <div>
          <h2>Campaign labels</h2>
          <p>
            {reviewPending
              ? "Review automatic suggestions"
              : "Review & complete labels"}
          </p>
        </div>
        <FeatureStatus value={dirty ? "In Progress" : response.labeling_status} />
      </div>
      <section className="card form-card feature-context" aria-label="Campaign context">
        <dl>
          <div>
            <dt>Bank</dt>
            <dd>{campaign.bank_name}</dd>
          </div>
          <div>
            <dt>Product</dt>
            <dd>{data.product_name || "Not recorded"}</dd>
          </div>
          <div>
            <dt>Product Category</dt>
            <dd>{label(campaign.project)}</dd>
          </div>
          <div>
            <dt>Language</dt>
            <dd>{data.language || "Not recorded"}</dd>
          </div>
        </dl>
        <a
          className="button"
          href={campaign.campaign_url}
          target="_blank"
          rel="noopener noreferrer"
        >
          Open original webpage ↗
        </a>
      </section>
      <section
        className="card form-card feature-progress"
        aria-label="Labeling progress"
      >
        <h2>
          {progress}% complete{" "}
          <span className="muted">
            · {filled}/{featureFields.length} fields
          </span>
        </h2>
        <progress
          max={featureFields.length}
          value={filled}
          aria-label="Features filled"
        />
        <details className="sample-notes">
          <summary>Labeling guidance</summary>
          <p>
            Scales describe communication, not quality. Zero and No count as
            observations. Leave unknown or inapplicable fields unset and explain them in
            notes.
          </p>
        </details>
      </section>
      {response.features?.source === "automatic" && (
        <div className="notice" role="note">
          Supported fields were filled during scraping. Review them and complete the
          remaining fields.
        </div>
      )}
      {campaign.collection?.is_demo && (
        <div className="notice" role="note">
          Demo imported content — not collected website evidence.
        </div>
      )}
      {proposal && !proposal.reviewed && (
        <section className="notice" aria-label="Automatic suggestions">
          <strong>
            {proposal.is_demo ? "Demo automatic suggestions" : "Automatic suggestions"}
          </strong>
          {reviewPending ? (
            <>
              <p>
                Review each value before saving. Existing manual values are kept; empty
                fields are prefilled. Autosave is off during review. Unsaved review
                edits reset on reload.
              </p>
              <details>
                <summary>Review proposed values</summary>
                <ul>
                  {featureFields
                    .filter((f) => proposal.values[f.key] !== undefined)
                    .map((field) => (
                      <li key={field.key}>
                        {label(field.key)}:{" "}
                        {String(proposal.values[field.key] ?? "Unset")}{" "}
                        <button
                          type="button"
                          className="secondary"
                          disabled={saving}
                          onClick={() =>
                            change(field.key, proposal.values[field.key] ?? null)
                          }
                        >
                          Use suggestion
                        </button>
                      </li>
                    ))}
                </ul>
              </details>
              {proposal.warnings.map((warning) => (
                <p key={warning}>{warning}</p>
              ))}
            </>
          ) : (
            <p>
              <Link to={`/campaigns/${id}?review=1`}>Review pending suggestions</Link>.
              Manual editing does not apply them.
            </p>
          )}
        </section>
      )}
      <Notice message={error} />
      <form
        className="label-editor"
        onSubmit={(e) => {
          e.preventDefault();
          void save();
        }}
      >
        <div className="label-workspace">
          <nav className="label-section-nav" aria-label="Feature sections">
            {sections.map((section, index) => {
              const fields = featureFields.filter((field) => field.section === section);
              const additional = index === featureSections.length;
              const total = additional ? additionalTotal : fields.length;
              const done = additional
                ? additionalRecorded
                : fields.filter((field) => isFilled(data[field.key])).length;
              return (
                <button
                  key={section}
                  type="button"
                  className={activeSection === index ? "active" : ""}
                  aria-current={activeSection === index ? "step" : undefined}
                  aria-controls="active-label-section"
                  onClick={() => goToSection(index)}
                >
                  <span className="label-section-number">{index + 1}</span>
                  <span className="label-section-description">
                    <span className="label-section-title">
                      <span>{section}</span>
                      {total > 0 && done === total && (
                        <span
                          className="label-section-check"
                          role="img"
                          aria-label="All fields recorded"
                        >
                          <Check size={11} strokeWidth={2.5} aria-hidden="true" />
                        </span>
                      )}
                    </span>
                    <small>
                      {done}/{total} recorded
                    </small>
                  </span>
                </button>
              );
            })}
          </nav>
          <fieldset disabled={saving} className="feature-form-fields">
            {sections.map((section, i) => {
              if (i !== activeSection) return null;
              const fields = featureFields.filter((f) => f.section === section);
              const additional = i === featureSections.length;
              const total = additional ? additionalTotal : fields.length;
              const done = additional
                ? additionalRecorded
                : fields.filter((f) => isFilled(data[f.key])).length;
              return (
                <section
                  id="active-label-section"
                  className="card feature-section"
                  key={section}
                  aria-labelledby="active-section-title"
                >
                  <header className="label-section-heading">
                    <p className="eyebrow">
                      SECTION {i + 1} OF {sections.length}
                    </p>
                    <h2 id="active-section-title" ref={sectionHeading} tabIndex={-1}>
                      {section}
                    </h2>
                    <p>
                      {done}/{total} fields recorded{additional ? " · Optional" : ""}
                    </p>
                  </header>
                  {additional && children}
                  <div className="form-grid">
                    {fields.map((field) => {
                      const value = data[field.key];
                      const inputId = `campaign-${id}-${field.key}`;
                      const suggested =
                        reviewPending && proposal?.values[field.key] !== undefined;
                      const proposedValue = proposal?.values[field.key];
                      const proposedText =
                        field.kind === "scale" && typeof proposedValue === "number"
                          ? `${proposedValue} — ${field.descriptions[proposedValue - 1]}`
                          : String(proposedValue ?? "Unset");
                      const help = suggested
                        ? `${field.help}. Auto suggested: ${proposedText}. You can keep, change, or clear this value.`
                        : field.help;
                      if (field.kind === "derived")
                        return (
                          <div className="feature-input-field" key={field.key}>
                            <FieldLabel
                              id={inputId}
                              label={label(field.key)}
                              help={`${field.help}. Calculated automatically; zero paragraphs leaves this unset.`}
                            />
                            <input
                              id={inputId}
                              readOnly
                              value={
                                typeof value === "number"
                                  ? Number(value.toFixed(2))
                                  : ""
                              }
                              placeholder="Requires word count and paragraph count > 0"
                            />
                          </div>
                        );
                      if (field.kind === "scale")
                        return (
                          <RatingScale
                            key={field.key}
                            label={label(field.key)}
                            help={help}
                            value={typeof value === "number" ? value : null}
                            descriptions={field.descriptions}
                            onChange={(v) => change(field.key, v)}
                          />
                        );
                      if (field.kind === "boolean")
                        return (
                          <BooleanChoice
                            key={field.key}
                            label={label(field.key)}
                            help={help}
                            value={typeof value === "boolean" ? value : null}
                            onChange={(v) => change(field.key, v)}
                          />
                        );
                      return (
                        <div className="feature-input-field" key={field.key}>
                          <FieldLabel
                            id={inputId}
                            label={label(field.key)}
                            help={help}
                          />
                          {field.kind === "enum" ? (
                            <select
                              id={inputId}
                              value={typeof value === "string" ? value : ""}
                              onChange={(e) =>
                                change(field.key, e.target.value || null)
                              }
                            >
                              <option value="">Unset</option>
                              {field.options.map((option) => (
                                <option key={option}>{option}</option>
                              ))}
                            </select>
                          ) : field.kind === "textarea" ? (
                            <textarea
                              id={inputId}
                              maxLength={10000}
                              rows={3}
                              value={typeof value === "string" ? value : ""}
                              onChange={(e) =>
                                change(field.key, e.target.value || null)
                              }
                            />
                          ) : (
                            <input
                              id={inputId}
                              type={
                                field.kind === "count"
                                  ? "number"
                                  : field.kind === "date"
                                    ? "date"
                                    : "text"
                              }
                              min={field.kind === "count" ? 0 : undefined}
                              max={field.kind === "count" ? 2147483647 : undefined}
                              step={field.kind === "count" ? 1 : undefined}
                              maxLength={300}
                              value={
                                typeof value === "number" || typeof value === "string"
                                  ? value
                                  : ""
                              }
                              onChange={(e) =>
                                change(
                                  field.key,
                                  e.target.value === ""
                                    ? null
                                    : field.kind === "count"
                                      ? Number(e.target.value)
                                      : e.target.value,
                                )
                              }
                            />
                          )}
                        </div>
                      );
                    })}
                  </div>
                </section>
              );
            })}
            <details className="label-notes">
              <summary>Labeling notes & context</summary>
              <label>
                Labeling notes
                <textarea
                  rows={4}
                  maxLength={10000}
                  value={data.labeling_notes ?? ""}
                  onChange={(e) => change("labeling_notes", e.target.value || null)}
                  placeholder="Explain uncertainty, omitted fields, and the page or language inspected."
                />
              </label>
            </details>
          </fieldset>
        </div>
        <nav className="section-pagination" aria-label="Label section pagination">
          <button
            type="button"
            className="secondary"
            disabled={saving || activeSection === 0}
            onClick={() => goToSection(activeSection - 1)}
          >
            ← Previous
          </button>
          <span>
            {activeSection + 1} / {sections.length}
          </span>
          <button
            type="button"
            className="secondary"
            disabled={saving || activeSection === sections.length - 1}
            onClick={() => goToSection(activeSection + 1)}
          >
            Next →
          </button>
        </nav>

        <div className="card form-card labeling-actions">
          <span role="status">
            {saving
              ? "Saving…"
              : error
                ? "Save failed"
                : reviewPending
                  ? "Suggestions awaiting review"
                  : dirty || additionalDirty
                    ? "Changes pending…"
                    : "Saved ✓"}
          </span>
          <button type="submit" className="secondary" disabled={saving}>
            {reviewPending ? "Save Reviewed Draft" : "Save Draft"}
          </button>
          <button
            type="button"
            className={
              activeSection === sections.length - 1 || progress === 100
                ? ""
                : "secondary"
            }
            disabled={saving}
            onClick={() => void save(true)}
          >
            Complete Labeling
          </button>
        </div>
      </form>
    </>
  );
}
