import { Link } from "react-router-dom";
import { QuickGuide } from "./QuickGuide";
import { FieldHelp } from "./FieldHelp";
import { useState } from "react";
import { ComparisonPage, pageTitle, scaleFields } from "../api/compare";
import { label } from "../api/campaigns";

// A small, fixed set of dimensions, not fixed results or bank rankings.
const dimensions = new Set([
  "text_density",
  "tone_formality",
  "emotional_vs_rational",
  "feature_vs_benefit_focus",
  "visual_intensity",
  "cta_prominence",
]);

export function ComparisonFindings({ pages }: { pages: ComparisonPage[] }) {
  const [showAll, setShowAll] = useState(false);
  const observations = scaleFields
    .filter((field) => dimensions.has(field.key))
    .flatMap((field) => {
      const values = pages.flatMap((page) => {
        const value = page.features?.[field.key];
        return typeof value === "number" ? [{ page, value }] : [];
      });
      if (values.length < 2) return [];
      const minimum = Math.min(...values.map((item) => item.value));
      const maximum = Math.max(...values.map((item) => item.value));
      return [{ field, values, minimum, maximum }];
    });
  return (
    <section
      id="insights"
      tabIndex={-1}
      className="card compare-section findings-section"
      aria-labelledby="findings-title"
    >
      <h2 id="findings-title" className="comparison-help-heading">
        Key observations
        <FieldHelp
          label="Key observations"
          help="Scores describe page content, not marketing effectiveness."
        />
      </h2>
      {observations.length === 0 ? (
        <p className="compare-empty-chart">
          No findings yet. At least two selected pages need a value for the same
          highlighted scale: text density, tone formality, emotional vs rational,
          feature vs benefit focus, visual intensity, or CTA prominence.
        </p>
      ) : (
        <ul className="comparison-findings">
          {observations
            .slice(0, showAll ? observations.length : 3)
            .map(({ field, values, minimum, maximum }) => (
              <li key={field.key}>
                <h3 className="comparison-help-heading">
                  {label(field.key)}
                  <QuickGuide
                    label={`Explain ${label(field.key)} observation`}
                    title={label(field.key)}
                  >
                    <p className="field-help-description">{field.help}</p>
                    <p className="field-help-description">
                      <strong>Observation: </strong>
                      {minimum === maximum
                        ? `Among the selected pages with a recorded value, all ${values.length} pages share a score of ${minimum} (${field.descriptions[minimum - 1]}).`
                        : `In the selected sample, recorded scores range from ${minimum} (${field.descriptions[minimum - 1]}) to ${maximum} (${field.descriptions[maximum - 1]}).`}
                    </p>
                    <p className="status-help-note">
                      Coverage: {values.length}/{pages.length} selected pages.{" "}
                      {pages.length - values.length} missing.
                    </p>
                  </QuickGuide>
                </h3>
                <p>
                  {minimum === maximum
                    ? `All ${values.length} labeled pages share a score of ${minimum}/5.`
                    : `Scores range from ${minimum} to ${maximum} out of 5.`}{" "}
                  {values.length}/{pages.length} pages labeled.
                </p>
                <div className="finding-values">
                  {values.map(({ page, value }) => (
                    <div key={page.campaign_id}>
                      <Link to={`/campaigns/${page.campaign_id}`}>
                        {pageTitle(page)}
                      </Link>
                      <strong>
                        {value}
                        <small> / 5</small>
                      </strong>
                    </div>
                  ))}
                </div>
              </li>
            ))}
        </ul>
      )}
      {observations.length > 3 && (
        <button
          type="button"
          className="secondary"
          aria-expanded={showAll}
          onClick={() => setShowAll((value) => !value)}
        >
          {showAll
            ? "Show fewer observations"
            : `Show all ${observations.length} observations`}
        </button>
      )}
    </section>
  );
}
