import { Link } from "react-router-dom";
import { analyticalFields, ComparisonPage, pageTitle } from "../api/compare";
import { label } from "../api/campaigns";
import { isFilled } from "../api/features";

type Definition = typeof analyticalFields[number];
function Cell({ page, field }: { page: ComparisonPage; field: Definition }) {
  const value = page.features?.[field.key];
  if (!isFilled(value)) return <span aria-label="Not labeled">—</span>;
  if (field.kind === "scale" && typeof value === "number") {
    return <><strong>{value}</strong><small>{field.descriptions[value - 1]}</small></>;
  }
  if (typeof value === "boolean") return <>{value ? "Yes" : "No"}</>;
  if (field.kind === "derived" && typeof value === "number") return <>{Number(value.toFixed(2))}</>;
  return <>{String(value)}</>;
}

export function ComparisonTable({ pages }: { pages: ComparisonPage[] }) {
  const sections = [...new Set(analyticalFields.map(field => field.section))];
  return <section className="compare-section" aria-labelledby="comparison-table-title"><h2 id="comparison-table-title">Detailed comparison</h2><p>Stored values, grouped by the existing framework. — means not labeled or not applicable; 0 and No are recorded observations.</p>
    {sections.map(section => <details className="card compare-table-section" key={section}><summary>{section}</summary><div className="table-scroll" tabIndex={0} role="region" aria-label={`${section} comparison table`}><table className="comparison-table"><caption className="sr-only">{section}: selected page feature values</caption><thead><tr><th scope="col">Feature</th>{pages.map(page => <th scope="col" key={page.campaign_id}><Link to={`/campaigns/${page.campaign_id}/label`}>{pageTitle(page)}</Link><small>{page.language || "Language unset"} · {page.labeling_status}</small><a href={page.page_url} target="_blank" rel="noopener noreferrer">Source ↗</a></th>)}</tr></thead><tbody>{analyticalFields.filter(field => field.section === section).map(field => <tr key={field.key}><th scope="row">{label(field.key)}<small>{field.help}</small></th>{pages.map(page => <td key={page.campaign_id}><Cell page={page} field={field} /></td>)}</tr>)}</tbody></table></div></details>)}
  </section>;
}
