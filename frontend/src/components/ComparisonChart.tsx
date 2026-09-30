import { FeatureBarChart } from "./FeatureBarChart";
import { useState } from "react";
import { FieldHelp } from "./FieldHelp";
import { ScaleHelp } from "./ScaleHelp";
import { ComparisonPage, scaleFields } from "../api/compare";
import { label } from "../api/campaigns";

const sections = [...new Set(scaleFields.map((field) => field.section))];

export function ComparisonChart({ pages }: { pages: ComparisonPage[] }) {
  const [selectedFeature, setSelectedFeature] = useState<string>("text_density");
  const field =
    scaleFields.find((item) => item.key === selectedFeature) ?? scaleFields[0];
  const available = pages.filter(
    (page) => typeof page.features?.[field.key] === "number",
  ).length;

  return (
    <section
      className="card form-card compare-section"
      aria-labelledby="comparison-chart-title"
    >
      <h2 id="comparison-chart-title" className="comparison-help-heading">
        Communication overview
        <FieldHelp
          label="Communication overview"
          help="Each chart compares one labeled feature on the same 1–5 scale. Higher values describe a position on the scale, not better performance."
        />
      </h2>
      <p className="chart-explanation">
        Choose a feature to compare the selected pages. Higher scores describe a
        position on the scale, not better performance. — means not labeled.
      </p>
      <label className="compare-category" htmlFor="comparison-scale-feature">
        Feature
        <select
          id="comparison-scale-feature"
          value={field.key}
          onChange={(event) => setSelectedFeature(event.target.value)}
        >
          {sections.map((section) => (
            <optgroup key={section} label={section}>
              {scaleFields
                .filter((item) => item.section === section)
                .map((item) => (
                  <option key={item.key} value={item.key}>
                    {label(item.key)}
                  </option>
                ))}
            </optgroup>
          ))}
        </select>
      </label>
      <section className="feature-chart-group" aria-label={field.section}>
        <h3>{field.section}</h3>
        <figure className="feature-chart" key={field.key}>
          <figcaption className="comparison-help-heading">
            {label(field.key)}
            <ScaleHelp
              label={label(field.key)}
              descriptions={field.descriptions}
              help={field.help}
            />
          </figcaption>
          <p>
            {available}/{pages.length} pages labeled · Scale 1–5
          </p>
          <FeatureBarChart pages={pages} field={field} />
          {available < 2 && (
            <p className="feature-chart-note">
              {available === 0
                ? "No recorded values yet."
                : "Label another page to compare this feature."}
            </p>
          )}
        </figure>
      </section>
    </section>
  );
}
