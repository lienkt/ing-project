import { FeatureStatus } from "./FeatureControls";
import { FieldHelp } from "./FieldHelp";
import { ScaleHelp } from "./ScaleHelp";
import { Link } from "react-router-dom";
import { analyticalFields, ComparisonPage } from "../api/compare";
import { label } from "../api/campaigns";
import { isFilled } from "../api/features";

const bankColumnClass = (bank: string) =>
  /^ing\b/i.test(bank.trim()) ? "comparison-ing-column" : undefined;

type Definition = (typeof analyticalFields)[number];
function Cell({ page, field }: { page: ComparisonPage; field: Definition }) {
  const value = page.features?.[field.key];
  if (!isFilled(value)) return <span aria-label="Not labeled">—</span>;
  if (field.kind === "scale" && typeof value === "number") {
    return (
      <strong aria-label={`${value}: ${field.descriptions[value - 1]}`}>{value}</strong>
    );
  }
  if (typeof value === "boolean")
    return (
      <span className={`comparison-boolean ${value ? "is-yes" : "is-no"}`}>
        {value ? "✓ Yes" : "− No"}
      </span>
    );
  if (field.kind === "derived" && typeof value === "number")
    return <>{Number(value.toFixed(2))}</>;
  return <>{String(value)}</>;
}

export function ComparisonTable({
  pages,
  group,
}: {
  pages: ComparisonPage[];
  group?: string;
}) {
  const sections = group
    ? [group]
    : [...new Set(analyticalFields.map((field) => field.section))];
  return (
    <section className="compare-section" aria-labelledby="comparison-table-title">
      <h2 id="comparison-table-title" className="comparison-help-heading">
        Detailed comparison
        <FieldHelp
          label="Detailed comparison"
          help="Stored values, grouped by the existing framework. — means not labeled or not applicable; 0 and No are recorded observations."
        />
      </h2>
      <p className="comparison-table-hint">
        Read across to compare pages. Yes / No are recorded labels; — means not labeled
        or not applicable.
      </p>
      {sections.map((section) => (
        <details
          className="card compare-table-section"
          key={`${group ?? "overview"}-${section}`}
          open={group !== undefined}
        >
          <summary>{section}</summary>
          <div
            className="table-scroll"
            tabIndex={0}
            role="region"
            aria-label={`${section} comparison table`}
          >
            <table className="comparison-table">
              <caption className="sr-only">
                {section}: selected page feature values
              </caption>
              <thead>
                <tr>
                  <th scope="col">Feature</th>
                  {pages.map((page) => (
                    <th
                      scope="col"
                      key={page.campaign_id}
                      className={bankColumnClass(page.bank_name)}
                    >
                      <Link to={`/campaigns/${page.campaign_id}`}>
                        <strong>{page.bank_name}</strong>
                        <small>
                          {page.product_name || "Product not recorded"} · #
                          {page.campaign_id}
                        </small>
                      </Link>
                      <div className="comparison-page-status">
                        <span>{page.language || "Language unset"}</span>
                        <FeatureStatus value={page.labeling_status} />
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {analyticalFields
                  .filter((field) => field.section === section)
                  .map((field) => (
                    <tr key={field.key}>
                      <th scope="row">
                        <span className="comparison-help-heading">
                          {label(field.key)}
                          {field.kind === "scale" ? (
                            <ScaleHelp
                              label={label(field.key)}
                              help={field.help}
                              descriptions={field.descriptions}
                            />
                          ) : (
                            <FieldHelp label={label(field.key)} help={field.help} />
                          )}
                        </span>
                      </th>
                      {pages.map((page) => (
                        <td
                          key={page.campaign_id}
                          className={bankColumnClass(page.bank_name)}
                        >
                          <Cell page={page} field={field} />
                        </td>
                      ))}
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </details>
      ))}
    </section>
  );
}
