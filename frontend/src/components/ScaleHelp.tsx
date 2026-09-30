import { QuickGuide } from "./QuickGuide";

export function ScaleHelp({
  label,
  descriptions,
  value,
  help,
}: {
  label: string;
  descriptions: readonly string[];
  value?: number | null;
  help?: string;
}) {
  return (
    <QuickGuide label={`Explain ${label} scale`} title={`${label} · 1–5 scale`}>
      {help && <p className="field-help-description">{help}</p>}
      <ol className="scale-help-list">
        {descriptions.map((description, index) => (
          <li key={index} className={value === index + 1 ? "is-selected" : undefined}>
            <span className="scale-help-number" aria-hidden="true">
              {index + 1}
            </span>
            <div>
              <strong>{description}</strong>
              {value === index + 1 && <small>Current value</small>}
            </div>
          </li>
        ))}
      </ol>
      <p className="status-help-note">
        Higher means a different position on the scale, not better performance.
      </p>
    </QuickGuide>
  );
}
