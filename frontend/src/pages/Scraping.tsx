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
    <div className="page-heading"><div><h1>Scraping Sources</h1><p>Import public bank webpages into the dataset.</p></div></div>
    <Notice message={error} />
    {error && <button className="secondary" onClick={() => setRetry(v => v + 1)}>Reload sources</button>}
    {!catalog && !error && <Loading />}
    {catalog && <>
      {catalog.scraping_is_demo && <div className="notice" role="note"><strong>Demo scraping engine active.</strong> Results are placeholders for integration testing; no webpages are fetched.{blocked && " Switch the backend to DATA_MODE=demo to import."}</div>}
      <p>Catalog entries are not Dataset records until imported successfully.</p>
      <fieldset disabled={running} className="source-controls">
        <div className="filters"><label>Bank<select value={bank} onChange={e => { setBank(e.target.value); setSelected([]); }}><option value="">All banks</option>{catalog.banks.map(b => <option key={b}>{b}</option>)}</select></label>
          <label>Product category<select value={category} onChange={e => { setCategory(e.target.value); setSelected([]); }}><option value="">All categories</option>{catalog.categories.map(c => <option key={c} value={c}>{label(c)}</option>)}</select></label></div>
        <div className="source-actions"><button className="secondary" onClick={() => setSelected(visible.filter(s => !s.campaign_id).map(s => s.source_id))}>Select all visible</button><button className="secondary" onClick={() => setSelected([])}>Clear selection</button><button disabled={blocked || !selected.length} onClick={() => void run()}>{running ? "Scraping…" : `Scrape Selected (${selected.length})`}</button></div>
        <div className="source-list">{visible.map(source => <article className="card source-card" key={source.source_id}>
          <label><input type="checkbox" checked={selected.includes(source.source_id)} disabled={!!source.campaign_id} onChange={e => setSelected(ids => e.target.checked ? [...ids, source.source_id] : ids.filter(id => id !== source.source_id))} /><span><strong>{source.bank} · {source.product_name}</strong><small>{label(source.product_category)} · {source.language} · {source.page_type}</small></span></label>
          <a href={source.url} target="_blank" rel="noreferrer">{source.url}</a>
          <p>{source.import_status}{source.is_example ? " · Example URL" : ""}{source.attempted_at ? ` · ${new Date(source.attempted_at).toLocaleString()}` : ""}</p>
          {source.error && <p className="error">{source.error}</p>}
          {source.campaign_id && <Link to={`/campaigns/${source.campaign_id}`}>Open imported campaign</Link>}
        </article>)}</div>
        {!visible.length && <p>No sources match these filters.</p>}
      </fieldset>
    </>}
    {running && <p role="status">Importing selected sources. Results appear when the batch finishes.</p>}
    {results.length > 0 && <section className="card form-card" aria-live="polite"><h2>Scraping results</h2><ul>{results.map(result => <li key={result.source_id}><strong>{catalog?.sources.find(s => s.source_id === result.source_id)?.product_name || result.source_id}</strong>: {result.status === "success" ? "Added to Dataset" : result.status === "existing" ? "Already in Dataset — skipped" : `Failed: ${result.error}`}</li>)}</ul><Link to="/">View Dataset</Link></section>}
  </>;
}
