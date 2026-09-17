import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Catalog, getSources, ImportResult, scrapeSources } from "../api/collection";
import { label } from "../api/campaigns";
import { Loading, Notice } from "../components/shared";

export default function Scraping() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [error, setError] = useState("");
  const [bank, setBank] = useState("");
  const [category, setCategory] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<ImportResult[]>([]);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    getSources().then(value => { if (active) { setCatalog(value); setError(""); } })
      .catch(e => { if (active) setError((e as Error).message); });
    return () => { active = false; };
  }, [retry]);
  async function run() {
    setRunning(true); setError(""); setResults([]);
    try {
      const response = await scrapeSources(selected);
      setResults(response.results); setSelected([]);
      setCatalog(await getSources());
    } catch (e) { setError((e as Error).message); }
    finally { setRunning(false); }
  }
  const visible = catalog?.sources.filter(s => (!bank || bank === s.bank) && (!category || category === s.product_category)) ?? [];
  const blocked = catalog?.scraping_is_demo && catalog.data_mode !== "demo";
  return <>
    <div className="page-heading"><div><h1>Scraping Sources</h1><p>Select pages to add to Dataset.</p></div></div>
    <Notice message={error} />
    {error && <button className="secondary" onClick={() => setRetry(v => v + 1)}>Reload sources</button>}
    {!catalog && !error && <Loading />}
    {catalog && <>
      {catalog.scraping_is_demo && <div className="notice" role="note"><strong>Demo mode</strong> · Sample content only; no live webpages fetched.{blocked && " Switch the backend to DATA_MODE=demo to import."}</div>}
      <fieldset disabled={running} className="source-controls card">
        <div className="filters"><label>Bank<select value={bank} onChange={e => { setBank(e.target.value); setSelected([]); }}><option value="">All banks</option>{catalog.banks.map(b => <option key={b}>{b}</option>)}</select></label>
          <label>Product category<select value={category} onChange={e => { setCategory(e.target.value); setSelected([]); }}><option value="">All categories</option>{catalog.categories.map(c => <option key={c} value={c}>{label(c)}</option>)}</select></label></div>
        <div className="source-actions"><button className="secondary" onClick={() => setSelected(visible.filter(s => !s.campaign_id).map(s => s.source_id))}>Select all</button><button className="secondary" onClick={() => setSelected([])}>Clear</button><button disabled={blocked || !selected.length} onClick={() => void run()}>{running ? "Scraping…" : `Scrape Selected (${selected.length})`}</button></div>
        <div className="table-scroll"><table className="source-table"><thead><tr><th aria-label="Select source" /><th>BANK / PRODUCT</th><th>CATEGORY</th><th>LANGUAGE</th><th>STATUS</th><th>LINK</th></tr></thead><tbody>
          {visible.map(source => <tr key={source.source_id}>
            <td><input type="checkbox" aria-label={`Select ${source.bank} ${source.product_name}`} checked={selected.includes(source.source_id)} disabled={!!source.campaign_id} onChange={e => setSelected(ids => e.target.checked ? [...ids, source.source_id] : ids.filter(id => id !== source.source_id))} /></td>
            <td><strong>{source.bank}</strong><small>{source.product_name}</small></td>
            <td>{label(source.product_category)}</td><td>{source.language}</td>
            <td><span className={`badge ${source.campaign_id ? "evaluated" : source.error ? "source-failed" : "basic"}`}>{source.campaign_id ? "Imported" : source.error ? "Failed" : "Ready"}</span>
              {source.error && <details className="source-error"><summary>Error details</summary><p>{source.error}</p></details>}</td>
            <td>{source.campaign_id ? <Link to={`/campaigns/${source.campaign_id}`}>View campaign →</Link> : <a href={source.url} title={source.url} target="_blank" rel="noreferrer">{source.is_example ? "Example" : "Source"} ↗</a>}</td>
          </tr>)}
        </tbody></table></div>
        {!visible.length && <p>No sources match these filters.</p>}
      </fieldset>
    </>}
    {running && <p role="status">Importing selected pages…</p>}
    {results.length > 0 && <section className="card form-card" aria-live="polite"><h2>Scraping results</h2><ul>{results.map(result => <li key={result.source_id}><strong>{catalog?.sources.find(s => s.source_id === result.source_id)?.product_name || result.source_id}</strong>: {result.status === "success" ? "Added to Dataset" : result.status === "existing" ? "Already in Dataset — skipped" : `Failed: ${result.error}`}</li>)}</ul><Link to="/">View Dataset</Link></section>}
  </>;
}
