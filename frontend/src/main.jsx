import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Activity, ArrowDownRight, ArrowUpRight, CalendarDays, ChevronDown, CircleHelp, Clock3, Download, RefreshCw, Wind, Zap } from 'lucide-react';
import './styles.css';

const fmt = (v, digits = 0) => v == null ? '—' : new Intl.NumberFormat('en-GB', { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(v);

function App() {
  const [cutoff, setCutoff] = useState('12:00');
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState('');
  const [period, setPeriod] = useState('all');
  const [page, setPage] = useState(1);

  const load = async () => {
    setBusy(true); setError('');
    try {
      const response = await fetch(`/api/analysis?cutoff=${encodeURIComponent(cutoff)}`);
      if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail || `Request failed (${response.status})`); }
      setData(await response.json());
    } catch (e) { setError(e.message || 'Unable to load Elexon data.'); }
    finally { setBusy(false); }
  };
  useEffect(() => { load(); }, [cutoff]);

  const filtered = useMemo(() => period === 'all' ? (data?.intervals || []) : (data?.intervals || []).filter(x => Number(x.startTime.slice(8, 10)) <= Number(period)), [data, period]);
  const daily = useMemo(() => {
    const grouped = {};
    for (const row of filtered) { const day = row.startTime.slice(0, 10); (grouped[day] ||= []).push(row); }
    return Object.values(grouped).map(rows => {
      const paired = rows.filter(x => x.matched);
      return { date: rows[0].startTime.slice(0, 10), actual: paired.length ? paired.reduce((sum, x) => sum + x.actualMw, 0) / paired.length : null, forecast: paired.length ? paired.reduce((sum, x) => sum + x.forecastMw, 0) / paired.length : null };
    });
  }, [filtered]);
  useEffect(() => setPage(1), [period]);
  const visible = filtered.slice((page - 1) * 12, page * 12);
  const m = data?.metrics;

  const exportCsv = () => {
    const cols = ['startTime', 'actualMw', 'forecastMw', 'errorMw', 'absoluteErrorMw', 'forecastPublishedAt'];
    const csv = [cols.join(','), ...filtered.map(row => cols.map(c => row[c] ?? '').join(','))].join('\n');
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' })); a.download = 'uk-wind-forecast-accuracy-jan-2026.csv'; a.click(); URL.revokeObjectURL(a.href);
  };

  if (error && !data) return <main className="center-state"><div className="state-icon"><Wind /></div><h1>Wind data is unavailable</h1><p>{error}</p><button className="primary-btn" onClick={load}><RefreshCw size={16} />Try again</button><small>Live data comes directly from the Elexon BMRS API. No sample values are shown.</small></main>;
  const biasUp = (m?.biasMw || 0) > 0;

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><Wind size={20} /></div><span>northstar<span className="brand-period">.</span><small>ENERGY INTELLIGENCE</small></span></div>
      <div className="side-label">WORKSPACE</div><button className="nav-item active"><Activity size={17} />Wind intelligence</button>
      <div className="side-label bottom-label">DATA SOURCE</div><div className="source-card"><div className="source-status" /><div><b>Elexon BMRS</b><small>Official generation data</small></div><span className="source-link">↗</span></div>
      <div className="sidebar-foot">PILOT ANALYSIS <span>01 / 26</span></div>
    </aside>
    <main className="main">
      <header className="topbar"><div className="crumb">Analytics <span>/</span> Generation outlook</div><div className="top-actions"><span className="live-dot" />Historical analysis <span className="top-divider" /><span className="avatar">UK</span></div></header>
      <section className="content">
        <div className="eyebrow"><span /> UK NATIONAL WIND <span className="eyebrow-line" /> JANUARY 2026</div>
        <div className="heading-row"><div><h1>Forecast intelligence</h1><p className="subtitle">Understand forecast uncertainty before the day-ahead decision.</p></div><div className="header-tools"><div className="select-wrap"><CalendarDays size={15} /><select aria-label="Analysis month"><option>January 2026</option></select><ChevronDown size={14} /></div><button className="icon-btn" title="Refresh data" onClick={load}><RefreshCw size={16} className={busy ? 'spin' : ''} /></button></div></div>
        <div className="context-bar"><div className="context-icon"><Clock3 size={16} /></div><div><strong>Historical decision view</strong><span>Latest forecast available by <b>{cutoff} UK time</b> on the day before delivery</span></div><label className="cutoff-control">Cutoff <select value={cutoff} onChange={e => setCutoff(e.target.value)}><option>10:00</option><option>12:00</option><option>16:00</option><option>18:00</option></select></label><span className="assumption-link" title="The challenge does not specify an exact market cutoff. This time is a pilot convention."><CircleHelp size={15} /></span></div>
        {error && data && <div className="inline-error">Latest refresh failed: {error}. Showing the last successful result.</div>}
        <section className="metric-grid">
          <Metric title="Mean absolute error" value={fmt(m?.maeMw)} unit="MW" note="Typical absolute miss" icon={<Activity size={17} />} loading={busy && !data} />
          <Metric title="Forecast bias" value={fmt(m?.biasMw)} unit="MW" note={biasUp ? 'Forecasts ran high on average' : 'Forecasts ran low on average'} icon={biasUp ? <ArrowUpRight size={18} /> : <ArrowDownRight size={18} />} tone={biasUp ? 'amber' : 'green'} loading={busy && !data} />
          <Metric title="RMSE" value={fmt(m?.rmseMw)} unit="MW" note="Larger misses count more" icon={<Zap size={17} />} tone="violet" loading={busy && !data} />
          <Metric title="Interval coverage" value={fmt(m?.coveragePct, 1)} unit="%" note={`${fmt(m?.matchedIntervals)} of ${fmt(m?.expectedIntervals)} intervals`} icon={<CalendarDays size={17} />} tone="blue" loading={busy && !data} />
        </section>
        <section className="panel chart-panel">
          <div className="panel-heading"><div><div className="section-kicker">ACTUAL VS FORECAST</div><h2>Wind generation profile</h2><p>Daily average across matched half-hour delivery intervals</p></div><div className="chart-controls"><div className="legend"><span className="legend-item"><i className="legend-line actual" />Actual</span><span className="legend-item"><i className="legend-line forecast" />Forecast vintage</span></div><select className="day-select" value={period} onChange={e => setPeriod(e.target.value)}><option value="all">Full month</option><option value="07">1–7 Jan</option><option value="14">1–14 Jan</option><option value="21">1–21 Jan</option></select></div></div>
          <div className="chart-wrap">{busy && !data ? <div className="skeleton chart-skeleton" /> : <ResponsiveContainer width="100%" height="100%"><AreaChart data={daily} margin={{ top: 10, right: 8, bottom: 0, left: 0 }}><defs><linearGradient id="actualFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#147d65" stopOpacity={0.16} /><stop offset="95%" stopColor="#147d65" stopOpacity={0} /></linearGradient></defs><CartesianGrid vertical={false} stroke="#e9eeea" /><XAxis dataKey="date" tickFormatter={x => new Date(`${x}T12:00:00`).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })} axisLine={false} tickLine={false} tick={{ fill: '#8b9892', fontSize: 11 }} minTickGap={24} /><YAxis axisLine={false} tickLine={false} tick={{ fill: '#8b9892', fontSize: 11 }} tickFormatter={x => `${Math.round(x / 1000)}k`} width={40} /><Tooltip content={<ChartTip />} /><Area type="monotone" dataKey="actual" name="Actual" stroke="#177f67" strokeWidth={2.5} fill="url(#actualFill)" connectNulls={false} activeDot={{ r: 4, strokeWidth: 0 }} /><Area type="monotone" dataKey="forecast" name="Forecast vintage" stroke="#5977ce" strokeWidth={2} strokeDasharray="5 4" fill="none" connectNulls={false} activeDot={{ r: 4, strokeWidth: 0 }} /></AreaChart></ResponsiveContainer>}</div>
          <div className="chart-foot"><span><i className="dot green-dot" />Data source: Elexon BMRS · FUELHH + WINDFOR</span><span>Values in MW <span className="foot-sep">·</span> 30-minute settlement intervals</span></div>
        </section>
        <section className="panel table-panel">
          <div className="panel-heading table-heading"><div><div className="section-kicker">INTERVAL DETAIL</div><h2>Forecast and outturn</h2><p>Selected vintage paired with actual generation by delivery start time</p></div><button className="export-btn" onClick={exportCsv}><Download size={15} />Export CSV</button></div>
          <div className="table-scroll"><table><thead><tr><th>DELIVERY (UK)</th><th>FORECAST VINTAGE</th><th>ACTUAL</th><th>FORECAST</th><th>ERROR</th><th>STATUS</th></tr></thead><tbody>{busy && !data ? Array.from({ length: 4 }, (_, i) => <tr key={i}><td colSpan="6"><div className="skeleton row-skeleton" /></td></tr>) : visible.map(row => <tr key={row.startTime}><td className="date-cell">{new Date(row.startTime).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: 'Europe/London' })}</td><td className="vintage-cell">{row.forecastPublishedAt ? new Date(row.forecastPublishedAt).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: 'Europe/London' }) : '—'}</td><td>{fmt(row.actualMw)} <small>MW</small></td><td>{fmt(row.forecastMw)} <small>MW</small></td><td className={row.errorMw == null ? 'muted' : row.errorMw > 0 ? 'err-high' : 'err-low'}>{row.errorMw == null ? '—' : `${row.errorMw > 0 ? '+' : ''}${fmt(row.errorMw)} MW`}</td><td><span className={`status ${row.matched ? 'paired' : 'missing'}`}>{row.matched ? 'Paired' : 'Missing data'}</span></td></tr>)}</tbody></table>{!busy && visible.length === 0 && <div className="empty-table">No intervals available for this filter.</div>}</div>
          <div className="table-footer"><span>Showing {visible.length ? (page - 1) * 12 + 1 : 0}–{Math.min(page * 12, filtered.length)} of {fmt(filtered.length)} intervals <span className="footer-note">· Missing values are not included in accuracy metrics</span></span><div className="pagination"><button disabled={page === 1} onClick={() => setPage(p => p - 1)}>Previous</button><span>{page}</span><button disabled={page * 12 >= filtered.length} onClick={() => setPage(p => p + 1)}>Next</button></div></div>
        </section>
        <footer className="page-footer"><span>Northstar Energy Intelligence <b>·</b> Pilot analysis</span><span>Forecast selection method <a href="#method">View notes ↓</a></span></footer>
        <section className="method-note" id="method"><h3>How to read this analysis</h3><p>For each January delivery interval, the dashboard selects the latest valid WINDFOR forecast published by the configurable previous-day cutoff ({cutoff} Europe/London). Forecasts published after that cutoff are excluded. Intervals are joined on normalized delivery start time. MAE and RMSE describe error magnitude; positive bias means the forecast tended to exceed actual generation. The chosen cutoff is a transparent pilot assumption because the assignment does not specify an exact decision time.</p><p>Only exact matching delivery intervals contribute. No values are fabricated. Coverage shows the share of the expected 1,488 half-hourly January intervals with both an eligible forecast and an actual.</p></section>
      </section>
    </main>
  </div>;
}

function Metric({ title, value, unit, note, icon, tone = '', loading }) {
  return <article className={`metric-card ${tone}`}><div className="metric-top"><span>{title}</span><span className="metric-icon">{icon}</span></div><div className="metric-value">{loading ? <i className="skeleton val-skeleton" /> : <>{value}<small>{unit}</small></>}</div><div className="metric-note">{loading ? 'Loading official data' : note}</div></article>;
}

function ChartTip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return <div className="tooltip"><b>{new Date(`${label}T12:00:00`).toLocaleDateString('en-GB', { day: 'numeric', month: 'long' })}</b>{payload.map(x => <span key={x.name}><i style={{ background: x.color }} />{x.name}<strong>{fmt(x.value)} MW</strong></span>)}</div>;
}

createRoot(document.getElementById('root')).render(<App />);

