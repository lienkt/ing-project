import { useState } from "react";
import { ComparisonPage, pageTitle, scaleFields } from "../api/compare";
import { label } from "../api/campaigns";

export function ComparisonChart({ pages }: { pages: ComparisonPage[] }) {
  const [key, setKey] = useState<string>("text_density");
  const field = scaleFields.find((item) => item.key === key) ?? scaleFields[0];
  const available = pages.filter(
    (page) => typeof page.features?.[field.key] === "number",
  );
  return (
    <section
      className="card form-card compare-section"
      aria-labelledby="comparison-chart-title"
    >
      <h2 id="comparison-chart-title">Explore a scale</h2>
      <p>
        One semantic dimension at a time. Higher values describe a position on the
        scale, not better performance.
      </p>
      <label className="compare-category">
        Feature
        <select value={field.key} onChange={(event) => setKey(event.target.value)}>
          {scaleFields.map((item) => (
            <option key={item.key} value={item.key}>
              {label(item.key)}
            </option>
          ))}
        </select>
      </label>
      <p>
        {available.length}/{pages.length} selected pages have a value for{" "}
        {label(field.key)}.
      </p>
      {available.length < 2 ? (
        <p className="compare-empty-chart">
          At least two labeled values are needed for this chart. Choose another feature
          or label the selected pages.
        </p>
      ) : (
        <figure className="comparison-bars">
          <figcaption>{label(field.key)} · 1–5 scale</figcaption>
          {pages.map((page) => {
            const value = page.features?.[field.key];
            return (
              <div className="comparison-bar-row" key={page.campaign_id}>
                <span>{pageTitle(page)}</span>
                {typeof value === "number" ? (
                  <>
                    <div className="comparison-bar-track" aria-hidden="true">
                      <div style={{ width: `${(value / 5) * 100}%` }} />
                    </div>
                    <span>
                      <strong>{value}/5</strong> — {field.descriptions[value - 1]}
                    </span>
                  </>
                ) : (
                  <span className="comparison-missing">
                    — Not labeled (omitted from chart)
                  </span>
                )}
              </div>
            );
          })}
        </figure>
      )}
      <details className="scale-guide">
        <summary>Read the scale definitions</summary>
        <ol>
          {field.descriptions.map((description) => (
            <li key={description}>{description}</li>
          ))}
        </ol>
      </details>
    </section>
  );
}
