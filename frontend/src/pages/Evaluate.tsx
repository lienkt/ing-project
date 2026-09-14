import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Check, Save } from "lucide-react";
import {
  evaluateCampaign,
  EvaluationInput,
  ScoreField,
  scoreFields,
} from "../api/campaigns";
import {
  CampaignContext,
  Loading,
  Notice,
  Steps,
  useCampaign,
} from "../components/shared";
const dimensions: Record<ScoreField, [string, string]> = {
  clarity_score: ["Clarity", "How easy is the main message to understand?"],
  visual_score: [
    "Visual strength",
    "How effectively do the visuals support the message?",
  ],
  benefit_score: [
    "Benefit communication",
    "How clearly does the campaign communicate customer value?",
  ],
  cta_score: ["CTA strength", "How clear and compelling is the next action?"],
  overall_score: [
    "Overall score",
    "Your independent assessment of the campaign as a whole.",
  ],
};
export default function Evaluate() {
  const { id, campaign, error } = useCampaign();
  const [scores, setScores] = useState<Partial<Record<ScoreField, number>>>({});
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saved, setSaved] = useState(false);
  useEffect(() => {
    if (campaign?.evaluation) {
      setScores(
        Object.fromEntries(
          scoreFields.map((k) => [k, campaign.evaluation![k]]),
        ),
      );
      setNotes(campaign.evaluation.evaluation_notes || "");
    }
  }, [campaign]);
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (scoreFields.some((k) => !scores[k])) {
      setSaveError("Select a score for each dimension.");
      return;
    }
    setSaving(true);
    setSaveError("");
    try {
      await evaluateCampaign(id, {
        ...scores,
        evaluation_notes: notes || null,
      } as EvaluationInput);
      setSaved(true);
    } catch (e) {
      setSaveError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }
  if (error)
    return (
      <>
        <Notice message={error} />
        <Link to="/">Back to dashboard</Link>
      </>
    );
  if (!campaign) return <Loading />;
  return (
    <>
      <Link className="back" to={`/campaigns/${id}`}>
        <ArrowLeft size={15} /> Campaign details
      </Link>
      <div className="page-heading">
        <div>
          <div className="eyebrow">TURN OBSERVATIONS INTO INSIGHTS</div>
          <h1>Evaluate campaign</h1>
          <p>Your perspective, across five key dimensions.</p>
        </div>
        <span className="project-tag">Manual evaluation</span>
      </div>
      <Steps current={3} id={id} />
      <CampaignContext campaign={campaign} />
      {saved ? (
        <div className="card empty">
          <span className="empty-icon">
            <Check size={30} />
          </span>
          <h2>Evaluation saved successfully</h2>
          <p>This campaign is now marked as Evaluated.</p>
          <button
            type="button"
            className="secondary"
            onClick={() => setSaved(false)}
          >
            Edit evaluation
          </button>
          <div className="success-actions">
            <Link className="button secondary" to={`/campaigns/${id}`}>
              Back to campaign
            </Link>
            <Link className="button" to="/">
              Back to dashboard
            </Link>
          </div>
        </div>
      ) : (
        <form className="card form-card" onSubmit={submit}>
          <div className="section-heading">
            <h2>Communication scores</h2>
            <p>
              Choose a score for every dimension. 1 = weak · 3 = average · 5 =
              strong.
            </p>
          </div>
          <Notice message={saveError} />
          {scoreFields.map((key) => (
            <fieldset className="score-row" key={key}>
              <legend>{dimensions[key][0]}</legend>
              <div className="score-content">
                <p>{dimensions[key][1]}</p>
                <div className="score-options">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <label
                      key={n}
                      className={scores[key] === n ? "selected" : ""}
                    >
                      <input
                        required
                        type="radio"
                        name={key}
                        value={n}
                        checked={scores[key] === n}
                        onChange={() => setScores({ ...scores, [key]: n })}
                      />
                      <span>{n}</span>
                    </label>
                  ))}
                </div>
              </div>
            </fieldset>
          ))}
          <label className="evaluation-notes">
            Evaluation notes
            <textarea
              rows={4}
              maxLength={10000}
              placeholder="Explain your scores or capture key takeaways…"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </label>
          <div className="form-actions">
            <span className="muted">
              Scores are entered manually, never calculated.
            </span>
            <button disabled={saving}>
              <Save size={16} />
              {saving
                ? "Saving…"
                : campaign.evaluation
                  ? "Update evaluation"
                  : "Save evaluation"}
            </button>
          </div>
        </form>
      )}
    </>
  );
}
