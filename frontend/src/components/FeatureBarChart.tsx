import { Link } from "react-router-dom";
import { ComparisonPage, pageTitle, ScaleDefinition } from "../api/compare";
import { label } from "../api/campaigns";
import { pageColors } from "./comparisonColors";

export function FeatureBarChart({
  pages,
  field,
}: {
  pages: ComparisonPage[];
  field: ScaleDefinition;
}) {
  const colors = pageColors(pages);
  return (
    <div
      className="feature-chart-scroll"
      role="region"
      tabIndex={0}
      aria-label={`${label(field.key)} bar chart`}
    >
      <div className="feature-chart-plot">
        <div className="feature-chart-axis" aria-hidden="true">
          {[5, 4, 3, 2, 1, 0].map((value) => (
            <span key={value}>{value}</span>
          ))}
        </div>
        <div className="feature-chart-columns">
          {pages.map((page) => {
            const value = page.features?.[field.key];
            const recorded = typeof value === "number";
            const description = recorded
              ? `${value}/5 — ${field.descriptions[value - 1]}`
              : "Not labeled";
            return (
              <div className="feature-chart-column" key={page.campaign_id}>
                <div
                  className="feature-chart-bar-area"
                  role="img"
                  aria-label={`${pageTitle(page)}: ${description}`}
                  title={description}
                >
                  {recorded ? (
                    <div
                      className="feature-chart-bar"
                      style={{
                        height: `${(value / 5) * 100}%`,
                        background: colors.get(page.campaign_id),
                      }}
                    >
                      <span>{value}</span>
                    </div>
                  ) : (
                    <span className="feature-chart-missing">—</span>
                  )}
                </div>
                <Link to={`/campaigns/${page.campaign_id}`} title={pageTitle(page)}>
                  {page.bank_name}
                  <small>#{page.campaign_id}</small>
                </Link>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
