import { useId, useState } from "react";
import { LabelingStatus } from "../api/features";

export function FeatureStatus({ value }: { value: LabelingStatus }) {
  return <span className={`badge ${value === "Completed" ? "evaluated" : value === "In Progress" ? "detailed" : "basic"}`}>{value}</span>;
}

export function RatingScale({ value, onChange, label, descriptions, help }: {
  value: number | null; onChange: (value: number | null) => void;
  label: string; descriptions: readonly string[]; help?: string;
}) {
  const id = useId();
  const [preview, setPreview] = useState<number | null>(null);
  const shown = preview ?? value;
  return <fieldset className="feature-control" aria-describedby={`${id}-meaning`}>
    <legend>{label}</legend>
    {help && <p className="scale-meaning">{help}</p>}
    <div className="scale-endpoints"><span>{descriptions[0]}</span><span>{descriptions[4]}</span></div>
    <div className="score-options" onMouseLeave={() => setPreview(null)}>
      {descriptions.map((meaning, i) => <label key={meaning} className={value === i + 1 ? "selected" : ""} title={`${i + 1}: ${meaning}`} onMouseEnter={() => setPreview(i + 1)}>
        <input type="radio" name={id} checked={value === i + 1} onChange={() => onChange(i + 1)} onFocus={() => setPreview(i + 1)} onBlur={() => setPreview(null)} aria-label={`${i + 1}: ${meaning}`} />
        <span>{i + 1}</span>
      </label>)}
    </div>
    <p id={`${id}-meaning`} className="scale-meaning" aria-live="polite">{shown === null ? "Not set — choose a value" : `${preview !== null && preview !== value ? "Preview" : "Selected"}: ${shown} — ${descriptions[shown - 1]}`}</p>
    <details className="scale-guide"><summary>Scale guide</summary><ol>{descriptions.map(d => <li key={d}>{d}</li>)}</ol></details>
    <button type="button" className="secondary clear-scale" disabled={value === null} onClick={() => onChange(null)}>Clear</button>
  </fieldset>;
}

export function BooleanChoice({ value, onChange, label, help }: {
  value: boolean | null; onChange: (value: boolean | null) => void; label: string; help?: string;
}) {
  const id = useId();
  return <fieldset className="feature-control"><legend>{label}</legend>{help && <p className="scale-meaning">{help}</p>}<div className="boolean-options">
    {([true, false, null] as const).map(v => <label key={String(v)} className={value === v ? "selected" : ""}><input type="radio" name={id} checked={value === v} onChange={() => onChange(v)} />{v === null ? "Not set" : v ? "Yes" : "No"}</label>)}
  </div></fieldset>;
}
