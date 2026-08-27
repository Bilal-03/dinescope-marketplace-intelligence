'use client';

import { useMemo, useState } from 'react';
import type { AnalyticsData, CuisinePair, CuisineSummary, CuisineView, MarketRow, MarketView, MonthlyPoint, Scope, Segment } from '@/app/lib/analytics';
import type { ProductRole } from '@/app/lib/access';

type PageId = 'overview' | 'customers' | 'markets' | 'cuisines' | 'reliability' | 'decision';

const NAV_ITEMS: { id: PageId; label: string; icon: string; state: 'live' | 'planned' }[] = [
  { id: 'overview', label: 'Overview', icon: '⌂', state: 'live' },
  { id: 'customers', label: 'Customer growth', icon: '↗', state: 'live' },
  { id: 'markets', label: 'Market demand', icon: '◎', state: 'live' },
  { id: 'cuisines', label: 'Cuisine gaps', icon: '◇', state: 'live' },
  { id: 'reliability', label: 'Data reliability', icon: '✓', state: 'live' },
  { id: 'decision', label: 'Decision lab', icon: '⌁', state: 'live' },
];

const PAGE_COPY: Record<PageId, { eyebrow: string; title: string; subtitle: string }> = {
  overview: { eyebrow: 'Product & Growth', title: 'Marketplace overview', subtitle: 'Understand customer momentum, value and where growth needs attention.' },
  customers: { eyebrow: 'First analytics module', title: 'Customer growth & retention', subtitle: 'Separate acquisition volume, repeat behavior and cohort retention.' },
  markets: { eyebrow: 'Phase 5d', title: 'Market demand intelligence', subtitle: 'Compare meaningful scale, growth, value and market confidence.' },
  cuisines: { eyebrow: 'Phase 5e', title: 'Cuisine opportunity', subtitle: 'Find demand-to-coverage gaps without overstating restaurant performance.' },
  reliability: { eyebrow: 'Foundation', title: 'Data reliability center', subtitle: 'See exactly what is trusted, excluded and limited before acting.' },
  decision: { eyebrow: 'Phase 6', title: 'Decision lab', subtitle: 'Prioritise opportunities with adjustable evidence and confidence weights.' },
};

export default function Dashboard({ data, displayName, role }: { data: AnalyticsData; displayName: string; role: ProductRole }) {
  const [page, setPage] = useState<PageId>('overview');
  const [market, setMarket] = useState('All markets');
  const [period, setPeriod] = useState('All years');
  const [showMethod, setShowMethod] = useState(false);
  const scope = data.scopes[`${market}|${period}`] ?? data.scopes['All markets|All years'];
  const pageCopy = PAGE_COPY[page];

  function resetFilters() {
    setMarket('All markets');
    setPeriod('All years');
  }

  function navigate(nextPage: PageId) {
    setPage(nextPage);
    if (nextPage === 'markets') setMarket('All markets');
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-mark">PL</div>
        <nav aria-label="Primary navigation">
          {NAV_ITEMS.map((item) => (
            <button aria-label={item.label} aria-current={page === item.id ? 'page' : undefined} className={page === item.id ? 'nav-button active' : 'nav-button'} key={item.id} onClick={() => navigate(item.id)} title={`${item.label}${item.state === 'planned' ? ' · planned' : ''}`} type="button">
              <span>{item.icon}</span>{item.state === 'planned' && <i className="planned-dot" />}
            </button>
          ))}
        </nav>
        <button aria-label="Methodology" className="nav-button help" title="Methodology" type="button" onClick={() => setShowMethod(true)}>?</button>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div className="brand-lockup"><div><strong>PlateLens</strong><span>Marketplace intelligence</span></div><span className="status-pill"><i /> Audited source</span></div>
          <div className="top-actions"><button className="method-button" type="button" onClick={() => setShowMethod(true)}>Metric dictionary</button><div className="user-chip"><div className="avatar">{initials(displayName)}</div><span><b>{firstName(displayName)}</b><small>{role}</small></span></div></div>
        </header>

        <div className="content">
          <div className="eyebrow"><span>{pageCopy.eyebrow}</span><b>/</b><span>{NAV_ITEMS.find((item) => item.id === page)?.label}</span></div>
          <div className="title-row"><div><h1>{pageCopy.title}</h1><p>{pageCopy.subtitle}</p></div><div className="period-control"><span>Source window</span><strong>{formatDate(data.source.date_min)} — {formatDate(data.source.date_max)}</strong><b>●</b></div></div>

          <section className="filter-bar" aria-label="Global filters">
            <label><span className="filter-label">Analysis period</span><select value={period} onChange={(event) => setPeriod(event.target.value)}>{data.filters.periods.map((item) => <option key={item}>{item}</option>)}</select></label>
            {page === 'markets' ? <div className="filter-lock"><span className="filter-label">Comparison scope</span><button type="button" disabled>All cleaned markets <b>✓</b></button></div> : <label><span className="filter-label">Clean market</span><select value={market} onChange={(event) => setMarket(event.target.value)}>{data.filters.markets.map((item) => <option key={item}>{item}</option>)}</select></label>}
            <div className="filter-lock"><span className="filter-label">Transaction rule</span><button type="button" disabled>Valid INR only <b>✓</b></button></div>
            <button className="reset-button" type="button" onClick={resetFilters}>↻ Reset</button>
            <div className="record-count"><i /> {page === 'markets' ? `${formatNumber(data.market_views[period]?.summary?.active_markets ?? 0)} markets compared` : page === 'cuisines' || page === 'decision' ? `${formatNumber(data.cuisine_views[period]?.pairs?.filter((row) => market === 'All markets' || row.market === market).length ?? 0)} cuisine-market signals` : `${formatNumber(scope.metrics?.valid_transactions ?? 0)} records in view`}</div>
          </section>

          {scope.empty && !['markets', 'cuisines', 'decision'].includes(page) ? <EmptyState /> : page === 'overview' ? <Overview data={data} scope={scope} goTo={navigate} /> : page === 'customers' ? <CustomerGrowth scope={scope} market={market} period={period} /> : page === 'markets' ? <MarketIntelligence view={data.market_views[period]} mapping={data.location_mapping} /> : page === 'cuisines' ? <CuisineOpportunity view={data.cuisine_views[period]} market={market} mapping={data.cuisine_mapping} restaurantMapping={data.restaurant_mapping} restaurantObservations={data.restaurant_observations} /> : page === 'decision' ? <DecisionLab view={data.cuisine_views[period]} market={market} period={period} /> : page === 'reliability' ? <Reliability data={data} /> : <PlannedModule page={page} goTo={navigate} />}

          <p className="disclaimer">Independent portfolio analysis using a public or synthetic dataset. Not affiliated with Zomato, Swiggy, or another delivery company.</p>
        </div>
      </section>

      {showMethod && <Methodology data={data} close={() => setShowMethod(false)} />}
    </main>
  );
}

function Overview({ data, scope, goTo }: { data: AnalyticsData; scope: Scope; goTo: (page: PageId) => void }) {
  const metrics = scope.metrics!;
  return <>
    <section className="kpi-grid" aria-label="Key marketplace metrics">
      <Kpi label="Valid transactions" value={formatNumber(metrics.valid_transactions)} note="Pass the strict transaction rule" tone="teal" definition="Distinct valid orders." />
      <Kpi label="Gross sales" value={formatCrore(metrics.gross_sales)} note="Observed valid INR sales" tone="coral" definition="Sum of valid positive INR sales." />
      <Kpi label="Active customers" value={formatNumber(metrics.active_customers)} note="Unique customers in scope" tone="blue" definition="Customers with at least one valid transaction." />
      <Kpi label="Repeat customer rate" value={formatPercent(metrics.repeat_rate)} note="Not cohort retention" tone="amber" definition="Customers with 2+ transactions divided by active customers." />
      <Kpi label="Avg. transaction value" value={formatRupee(metrics.average_transaction_value)} note="Source grain requires care" tone="violet" definition="Gross sales divided by valid transactions." warning />
    </section>
    <section className="analysis-grid">
      <TrendPanel monthly={scope.monthly ?? []} />
      <article className="panel brief-panel">
        <div className="panel-head"><div><span className="section-kicker">Decision brief</span><h2>What deserves attention</h2></div><span className="confidence">{scope.insight?.confidence} confidence</span></div>
        <div className="brief-callout"><span>01</span><div><b>{scope.insight?.headline}</b><p>{scope.insight?.evidence}</p></div></div>
        <div className="brief-item"><i className="risk-icon">!</i><div><b>Interpret value with caution</b><p>The average transaction value is unusually high for food delivery and may reflect a non-standard transaction grain.</p></div></div>
        <div className="brief-item"><i className="action-icon">↗</i><div><b>Recommended next analysis</b><p>{scope.insight?.action}</p></div></div>
        <button className="primary-button" type="button" onClick={() => goTo('customers')}>Explore customer growth <span>→</span></button>
      </article>
    </section>
    <section className="overview-lower">
      <article className="panel market-panel"><div className="panel-head"><div><span className="section-kicker">Demand footprint</span><h2>Highest-volume source markets</h2></div><span className="coverage-note">Raw locality labels · mapping pending</span></div><div className="market-list">{data.market_summary.slice(0, 5).map((row, index) => <div className="market-row" key={row.market}><span className="rank">0{index + 1}</span><b>{row.market}</b><span>{formatNumber(row.orders)} txns</span><div><i style={{ width: `${row.orders / data.market_summary[0].orders * 100}%` }} /></div><strong>{formatCrore(row.sales)}</strong></div>)}</div></article>
      <article className="panel integrity-card"><span className="section-kicker">Evidence boundary</span><h2>Why recommendations stay cautious</h2><p>Restaurant IDs almost never repeat, market labels mix locality and metro names, and menu coverage is only {formatPercent(data.quality.menu_coverage)}. PlateLens keeps those constraints visible instead of inventing precision.</p><button type="button" onClick={() => goTo('reliability')}>Review source reliability <span>→</span></button></article>
    </section>
  </>;
}

function TrendPanel({ monthly }: { monthly: MonthlyPoint[] }) {
  const [metric, setMetric] = useState<'orders' | 'sales'>('orders');
  const values = monthly.map((point) => metric === 'orders' ? point.orders : point.sales);
  const max = Math.max(...values, 1);
  return <article className="panel trend-panel">
    <div className="panel-head"><div><span className="section-kicker">Marketplace momentum</span><h2>Monthly performance</h2></div><div className="segmented" role="group" aria-label="Metric"><button aria-pressed={metric === 'orders'} className={metric === 'orders' ? 'selected' : ''} onClick={() => setMetric('orders')} type="button">Transactions</button><button aria-pressed={metric === 'sales'} className={metric === 'sales' ? 'selected' : ''} onClick={() => setMetric('sales')} type="button">Sales</button></div></div>
    <div className="chart-wrap" aria-label={`${metric} by month`} role="img"><div className="y-labels"><span>{metric === 'orders' ? compact(max) : formatCrore(max)}</span><span>{metric === 'orders' ? compact(max * .66) : formatCrore(max * .66)}</span><span>{metric === 'orders' ? compact(max * .33) : formatCrore(max * .33)}</span><span>0</span></div><div className="bar-chart">{values.map((value, index) => <span key={`${monthly[index].month}-${metric}`} title={`${monthly[index].month}: ${metric === 'orders' ? formatNumber(value) : formatCrore(value)}`} style={{ height: `${Math.max(5, value / max * 100)}%` }} />)}</div></div>
    <div className="chart-axis"><span>{shortMonth(monthly[0]?.month)}</span><span>{shortMonth(monthly[Math.floor(monthly.length / 2)]?.month)}</span><span>{shortMonth(monthly.at(-1)?.month)}</span></div>
    <div className="chart-foot"><span><i className="dot coral" /> {metric === 'orders' ? 'Valid transactions' : 'Gross sales'}</span><span>Partial boundary months remain labelled</span></div>
  </article>;
}

function CustomerGrowth({ scope, market, period }: { scope: Scope; market: string; period: string }) {
  const metrics = scope.metrics!;
  const segments = scope.segments ?? [];
  return <>
    <section className="kpi-grid customer-kpis">
      <Kpi label="Active customers" value={formatNumber(metrics.active_customers)} note={`${market} · ${period}`} tone="blue" definition="Unique customers with a valid transaction." />
      <Kpi label="New customers" value={formatNumber(metrics.new_customers)} note="First observed in scope" tone="teal" definition="Customers first observed in the filtered market during this period." />
      <Kpi label="Repeat customers" value={formatNumber(metrics.repeat_customers)} note="2+ transactions in scope" tone="coral" definition="Active customers with two or more transactions in this scope." />
      <Kpi label="Repeat customer rate" value={formatPercent(metrics.repeat_rate)} note="Distinct from retention" tone="amber" definition="Repeat customers divided by active customers." />
      <Kpi label="Transactions / customer" value={metrics.orders_per_customer.toFixed(2)} note="Frequency in scope" tone="violet" definition="Valid transactions divided by active customers." />
    </section>
    <section className="customer-grid">
      <CustomerTrend monthly={scope.monthly ?? []} />
      <FrequencyChart values={scope.frequency ?? []} />
    </section>
    <section className="customer-grid cohort-row">
      <CohortHeatmap cohorts={scope.cohorts ?? []} />
      <SegmentSummary segments={segments} insight={scope.insight} />
    </section>
    <SegmentTable segments={segments} market={market} period={period} />
  </>;
}

function CustomerTrend({ monthly }: { monthly: MonthlyPoint[] }) {
  const max = Math.max(...monthly.map((point) => point.new_customers + point.returning_customers), 1);
  return <article className="panel customer-trend"><div className="panel-head"><div><span className="section-kicker">Acquisition vs return</span><h2>Monthly active customer mix</h2></div><span className="coverage-note">First observed in filtered market</span></div><div className="stacked-chart">{monthly.map((point) => <div className="stack-group" key={point.month} title={`${point.month}: ${formatNumber(point.new_customers)} new, ${formatNumber(point.returning_customers)} returning`}><span className="returning" style={{ height: `${point.returning_customers / max * 100}%` }} /><span className="new" style={{ height: `${point.new_customers / max * 100}%` }} /></div>)}</div><div className="chart-axis"><span>{shortMonth(monthly[0]?.month)}</span><span>{shortMonth(monthly[Math.floor(monthly.length / 2)]?.month)}</span><span>{shortMonth(monthly.at(-1)?.month)}</span></div><div className="chart-foot"><span><i className="dot coral" /> New customers</span><span><i className="dot teal-dot" /> Returning customers</span></div></article>;
}

function FrequencyChart({ values }: { values: { frequency: string; customers: number }[] }) {
  const max = Math.max(...values.map((item) => item.customers), 1);
  return <article className="panel frequency-panel"><div className="panel-head"><div><span className="section-kicker">Habit depth</span><h2>Transaction frequency</h2></div></div><div className="frequency-list">{values.map((item) => <div key={item.frequency}><span>{item.frequency} {item.frequency === '1' ? 'transaction' : 'transactions'}</span><div><i style={{ width: `${item.customers / max * 100}%` }} /></div><b>{formatNumber(item.customers)}</b></div>)}</div><p className="panel-note">Frequency is calculated inside the selected scope; it is not a lifetime app-engagement measure.</p></article>;
}

function CohortHeatmap({ cohorts }: { cohorts: { cohort: string; size: number; retention: number[] }[] }) {
  if (!cohorts.length) return <article className="panel heatmap-panel"><EmptyState compact /></article>;
  return <article className="panel heatmap-panel"><div className="panel-head"><div><span className="section-kicker">True retention</span><h2>Acquisition cohort retention</h2></div><span className="coverage-note">M0–M6</span></div><div className="heatmap-scroll"><table className="heatmap"><thead><tr><th>Cohort</th><th>Size</th>{cohorts[0].retention.map((_, index) => <th key={index}>M{index}</th>)}</tr></thead><tbody>{cohorts.map((row) => <tr key={row.cohort}><th>{row.cohort}</th><td>{formatNumber(row.size)}</td>{row.retention.map((value, index) => <td key={index} style={{ backgroundColor: heatColor(value) }} title={`${value}% retained at month ${index}`}>{value.toFixed(1)}%</td>)}</tr>)}</tbody></table></div><p className="panel-note">Cohort size remains visible. M0 is acquisition month; later cells measure returned activity, not repeat-rate.</p></article>;
}

function SegmentSummary({ segments, insight }: { segments: Segment[]; insight?: Scope['insight'] }) {
  const total = segments.reduce((sum, segment) => sum + segment.customers, 0) || 1;
  return <article className="panel segment-summary"><div className="panel-head"><div><span className="section-kicker">Lifecycle signal</span><h2>Customer segment mix</h2></div><span className="confidence">{insight?.confidence} confidence</span></div><div className="segment-bars">{segments.slice(0, 6).map((segment, index) => <div key={segment.segment}><span><i style={{ background: segmentColor(index) }} />{segment.segment}</span><b>{formatPercent(segment.customers / total)}</b><div><i style={{ width: `${segment.customers / total * 100}%`, background: segmentColor(index) }} /></div></div>)}</div><div className="segment-insight"><b>{insight?.headline}</b><p>{insight?.action}</p></div></article>;
}

function SegmentTable({ segments, market, period }: { segments: Segment[]; market: string; period: string }) {
  return <article className="panel segment-table-panel"><div className="panel-head"><div><span className="section-kicker">Action workspace</span><h2>Segment evidence &amp; recommended action</h2></div><button className="export-button" type="button" onClick={() => exportSegments(segments, market, period)}>↓ Export CSV</button></div><div className="table-scroll"><table className="data-table"><thead><tr><th>Segment</th><th>Customers</th><th>Share</th><th>Txns / customer</th><th>Sales / customer</th><th>Repeat rate</th><th>Median recency</th><th>Recommended action</th></tr></thead><tbody>{segments.map((segment) => <tr key={segment.segment}><th>{segment.segment}</th><td>{formatNumber(segment.customers)}</td><td>{formatPercent(segment.customer_share)}</td><td>{segment.orders_per_customer.toFixed(2)}</td><td>{formatRupee(segment.sales_per_customer)}</td><td>{formatPercent(segment.repeat_rate)}</td><td>{Math.round(segment.median_recency)} days</td><td>{segment.action}</td></tr>)}</tbody></table></div></article>;
}

function MarketIntelligence({ view, mapping }: { view: MarketView; mapping: AnalyticsData['location_mapping'] }) {
  const [minimumOrders, setMinimumOrders] = useState(view.minimum_orders ?? 200);
  const [sortBy, setSortBy] = useState<'orders' | 'growth_orders' | 'repeat_rate' | 'sales'>('orders');
  const [selectedMarket, setSelectedMarket] = useState('');
  if (view.empty || !view.summary) return <EmptyState />;
  const eligible = view.markets.filter((row) => row.orders >= minimumOrders && row.previous_orders >= Math.max(50, minimumOrders / 2) && row.growth_orders !== null);
  const ranked = [...eligible].sort((a, b) => (b[sortBy] ?? -Infinity) - (a[sortBy] ?? -Infinity));
  const fastest = [...eligible].sort((a, b) => (b.growth_orders ?? -Infinity) - (a.growth_orders ?? -Infinity))[0];
  const highestRepeat = [...eligible].sort((a, b) => b.repeat_rate - a.repeat_rate)[0];
  const selected = view.markets.find((row) => row.market === selectedMarket) ?? ranked[0] ?? view.markets[0];

  return <>
    <div className="market-window"><div><span>Current comparable window</span><b>{view.current_window}</b></div><i>versus</i><div><span>Previous equal-length window</span><b>{view.comparison_window}</b></div><strong>{eligible.length} eligible markets</strong></div>
    <section className="kpi-grid market-kpis">
      <Kpi label="Active cleaned markets" value={formatNumber(view.summary.active_markets)} note={`${mapping.raw_labels} raw labels normalized`} tone="blue" definition="Cleaned markets with at least one valid transaction in the current comparison window." />
      <Kpi label="Largest market" value={view.summary.largest_market ?? '—'} note={`${formatNumber(view.summary.largest_market_orders)} transactions`} tone="coral" definition="Market with the most valid transactions in the current comparable window." />
      <Kpi label="Fastest eligible growth" value={fastest?.market ?? '—'} note={fastest?.growth_orders === null || !fastest ? 'Insufficient comparison' : `${formatSignedPercent(fastest.growth_orders)} transactions`} tone="teal" definition="Highest transaction growth among markets passing the selected current and comparison-period thresholds." />
      <Kpi label="Highest repeat rate" value={highestRepeat?.market ?? '—'} note={highestRepeat ? formatPercent(highestRepeat.repeat_rate) : 'Insufficient comparison'} tone="amber" definition="Highest within-window repeat customer rate among eligible markets." />
      <Kpi label="Top-five concentration" value={formatPercent(view.summary.top_five_concentration)} note="Share of current transactions" tone="violet" definition="Transaction share held by the five largest cleaned markets." />
    </section>

    <section className="market-controls panel"><div><div><span className="section-kicker">Eligibility control</span><h2>Minimum current transactions</h2></div><output aria-live="polite">{formatNumber(minimumOrders)}</output></div><input aria-label="Minimum current transactions" type="range" min="100" max="1000" step="100" value={minimumOrders} onChange={(event) => setMinimumOrders(Number(event.target.value))} /><p>Growth also requires at least {formatNumber(Math.max(50, minimumOrders / 2))} transactions in the comparison window. This prevents tiny bases from dominating the ranking.</p></section>

    <section className="market-analysis-grid">
      <MarketQuadrant markets={eligible} selected={selected.market} select={setSelectedMarket} />
      <MarketBrief market={selected} />
    </section>

    <MarketTrendCards markets={ranked.slice(0, 4)} />

    <article className="panel market-table-panel"><div className="panel-head"><div><span className="section-kicker">Evidence table</span><h2>Eligible market ranking</h2></div><div className="table-actions"><select aria-label="Rank markets by" value={sortBy} onChange={(event) => setSortBy(event.target.value as typeof sortBy)}><option value="orders">Rank by transactions</option><option value="growth_orders">Rank by growth</option><option value="repeat_rate">Rank by repeat rate</option><option value="sales">Rank by sales</option></select><button className="export-button" type="button" onClick={() => exportMarkets(ranked, view.period)}>↓ Export CSV</button></div></div><div className="table-scroll"><table className="data-table market-table"><thead><tr><th>Market</th><th>Transactions</th><th>Growth</th><th>Customers</th><th>Repeat rate</th><th>Avg. txn value</th><th>Txn share</th><th>Confidence</th></tr></thead><tbody>{ranked.map((row) => <tr aria-label={`Select ${row.market}`} aria-selected={selected.market === row.market} className={selected.market === row.market ? 'selected-row' : ''} key={row.market} tabIndex={0} onClick={() => setSelectedMarket(row.market)} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); setSelectedMarket(row.market); } }}><th>{row.market}</th><td>{formatNumber(row.orders)}</td><td className={growthClass(row.growth_orders)}>{formatSignedPercent(row.growth_orders)}</td><td>{formatNumber(row.customers)}</td><td>{formatPercent(row.repeat_rate)}</td><td>{formatRupee(row.average_transaction_value)}</td><td>{formatPercent(row.order_share)}</td><td><span className={`confidence inline-confidence ${row.confidence.toLowerCase()}`}>{row.confidence}</span></td></tr>)}</tbody></table></div></article>

    <div className="market-method-note"><b>Mapping coverage</b><p>{formatPercent(mapping.mapped_rows / (mapping.mapped_rows + mapping.unknown_rows))} of rows carry a non-unknown cleaned market; {formatNumber(mapping.review_pending_labels)} low-volume labels remain queued for manual review. Cuisine-demand comparison stays disabled until proportional cuisine allocation is implemented in the next phase.</p></div>
  </>;
}

function MarketQuadrant({ markets, selected, select }: { markets: MarketRow[]; selected: string; select: (market: string) => void }) {
  const visible = [...markets].sort((a, b) => b.orders - a.orders).slice(0, 30);
  const maxOrders = Math.max(...visible.map((row) => row.orders), 1);
  const minOrders = Math.min(...visible.map((row) => row.orders), 1);
  return <article className="panel quadrant-panel"><div className="panel-head"><div><span className="section-kicker">Scale × momentum</span><h2>Market growth quadrant</h2></div><span className="coverage-note">Select a point to diagnose</span></div><div className="quadrant" role="img" aria-label="Eligible markets plotted by transaction scale and growth"><span className="quadrant-label q1">Scale &amp; protect</span><span className="quadrant-label q2">Investigate decline</span><span className="quadrant-label q3">Selective bets</span><span className="quadrant-label q4">Build evidence</span><i className="axis vertical" /><i className="axis horizontal" />{visible.map((row) => { const x = scatterX(row.orders, minOrders, maxOrders); const y = scatterY(row.growth_orders ?? 0); const size = 9 + Math.sqrt(row.orders / maxOrders) * 13; return <button aria-label={`${row.market}: ${formatNumber(row.orders)} transactions, ${formatSignedPercent(row.growth_orders)} growth`} className={`market-point ${row.confidence.toLowerCase()} ${selected === row.market ? 'selected' : ''}`} key={row.market} onClick={() => select(row.market)} style={{ left: `${x}%`, bottom: `${y}%`, width: size, height: size }} title={`${row.market} · ${formatNumber(row.orders)} txns · ${formatSignedPercent(row.growth_orders)} growth`} type="button" />; })}</div><div className="quadrant-axis-labels"><span>Lower scale</span><b>Transaction scale →</b><span>Higher scale</span></div><div className="quadrant-legend"><span><i className="high" /> High confidence</span><span><i className="medium" /> Medium</span><span><i className="low" /> Low</span></div></article>;
}

function MarketBrief({ market }: { market: MarketRow }) {
  const signal = market.growth_orders === null ? 'Comparison base is insufficient' : market.growth_orders >= .2 ? 'Demand is expanding materially' : market.growth_orders < -.1 ? 'Demand is contracting' : 'Demand is broadly stable';
  const action = market.growth_orders !== null && market.growth_orders >= .2 && market.repeat_rate < .02 ? 'Validate whether acquisition quality can improve: growth is strong, but within-window repeat behavior remains low.' : market.growth_orders !== null && market.growth_orders < -.1 ? 'Diagnose category, customer-mix and instrumentation shifts before committing incremental growth spend.' : 'Protect the current base and compare customer mix before changing investment.';
  return <article className="panel market-brief"><div className="panel-head"><div><span className="section-kicker">Selected market</span><h2>{market.market}</h2></div><span className={`confidence ${market.confidence.toLowerCase()}`}>{market.confidence} confidence</span></div><div className="market-hero-metric"><span>Transaction growth</span><strong className={growthClass(market.growth_orders)}>{formatSignedPercent(market.growth_orders)}</strong><small>{formatNumber(market.previous_orders)} → {formatNumber(market.orders)} transactions</small></div><div className="brief-callout market-signal"><span>01</span><div><b>{signal}</b><p>{action}</p></div></div><dl className="market-facts"><div><dt>Customer reach</dt><dd>{formatNumber(market.customers)}</dd></div><div><dt>Repeat rate</dt><dd>{formatPercent(market.repeat_rate)}</dd></div><div><dt>Average transaction value</dt><dd>{formatRupee(market.average_transaction_value)}</dd></div><div><dt>Transaction share</dt><dd>{formatPercent(market.order_share)}</dd></div></dl><p className="hypothesis-note">Recommended actions are diagnostic hypotheses, not causal conclusions.</p></article>;
}

function MarketTrendCards({ markets }: { markets: MarketRow[] }) {
  return <section className="market-trend-section"><div className="section-row"><div><span className="section-kicker">Comparable movement</span><h2>Monthly transaction pulse</h2></div><span>Top eligible markets by current scale</span></div><div className="market-trend-grid">{markets.map((market) => { const max = Math.max(...market.monthly_orders.map((point) => point.orders), 1); return <article className="panel mini-trend" key={market.market}><div><b>{market.market}</b><span className={growthClass(market.growth_orders)}>{formatSignedPercent(market.growth_orders)}</span></div><div>{market.monthly_orders.map((point) => <i key={point.month} title={`${point.month}: ${point.orders} transactions`} style={{ height: `${Math.max(5, point.orders / max * 100)}%` }} />)}</div><small>{formatNumber(market.orders)} current-window transactions</small></article>; })}</div></section>;
}

function CuisineOpportunity({ view, market, mapping, restaurantMapping, restaurantObservations }: { view: CuisineView; market: string; mapping: AnalyticsData['cuisine_mapping']; restaurantMapping: AnalyticsData['restaurant_mapping']; restaurantObservations: AnalyticsData['restaurant_observations'] }) {
  const [minimumOrders, setMinimumOrders] = useState(view.minimum_allocated_orders ?? 100);
  const [sortBy, setSortBy] = useState<'opportunity_score' | 'allocated_orders' | 'growth' | 'demand_to_listing_index'>('opportunity_score');
  const [selectedKey, setSelectedKey] = useState('');
  if (view.empty || !view.summary) return <EmptyState />;
  const scopedPairs = view.pairs.filter((row) => market === 'All markets' || row.market === market);
  const eligible = scopedPairs.filter((row) => row.allocated_orders >= minimumOrders && row.previous_allocated_orders >= Math.max(25, minimumOrders / 2) && row.growth !== null);
  const ranked = [...eligible].sort((a, b) => (b[sortBy] ?? -Infinity) - (a[sortBy] ?? -Infinity));
  const selected = scopedPairs.find((row) => `${row.market}|${row.cuisine}` === selectedKey) ?? ranked[0] ?? scopedPairs[0];
  const cuisineSummary: CuisineSummary[] = market === 'All markets' ? view.cuisines : scopedPairs.map((row) => ({ cuisine: row.cuisine, allocated_orders: row.allocated_orders, allocated_sales: row.allocated_sales, customers: row.customers, markets: 1, observed_listings: row.observed_listings })).sort((a, b) => b.allocated_orders - a.allocated_orders);
  const topCuisine = cuisineSummary[0];
  const topOpportunity = [...eligible].sort((a, b) => b.opportunity_score - a.opportunity_score)[0];

  return <>
    <div className="market-window cuisine-window"><div><span>Current comparable window</span><b>{view.current_window}</b></div><i>versus</i><div><span>Previous equal-length window</span><b>{view.comparison_window}</b></div><strong>{market === 'All markets' ? 'All cleaned markets' : market}</strong></div>
    <section className="kpi-grid cuisine-kpis">
      <Kpi label="Canonical cuisines" value={formatNumber(mapping.canonical_cuisines)} note={`${mapping.raw_tokens} raw tokens reviewed`} tone="blue" definition="Distinct cuisine labels remaining after normalization and removal of non-cuisine marketing text." />
      <Kpi label="Highest observed demand" value={topCuisine?.cuisine ?? '—'} note={topCuisine ? `${formatDecimal(topCuisine.allocated_orders)} allocated txns` : 'No evidence'} tone="coral" definition="Cuisine with the most proportionally allocated transactions in the selected market scope." />
      <Kpi label="Eligible opportunities" value={formatNumber(eligible.length)} note={`${formatNumber(minimumOrders)}+ allocated transactions`} tone="teal" definition="Cuisine-market pairs passing current and comparison-period sample thresholds." />
      <Kpi label="Top opportunity signal" value={topOpportunity ? `${topOpportunity.market} · ${topOpportunity.cuisine}` : '—'} note={topOpportunity ? `Score ${topOpportunity.opportunity_score.toFixed(1)} / 100` : 'Insufficient comparison'} tone="amber" definition="Confidence-adjusted descriptive score combining demand, growth, customer reach, demand-to-listing index and data coverage." />
      <Kpi label="Cuisine field coverage" value={formatPercent(mapping.cuisine_coverage)} note={`${formatNumber(mapping.excluded_token_rows)} invalid token rows excluded`} tone="violet" definition="Source rows with an observed restaurant cuisine value." />
    </section>

    <section className="market-controls panel cuisine-controls"><div><div><span className="section-kicker">Evidence threshold</span><h2>Minimum allocated transactions</h2></div><output aria-live="polite">{formatNumber(minimumOrders)}</output></div><input aria-label="Minimum allocated transactions" type="range" min="50" max="500" step="50" value={minimumOrders} onChange={(event) => setMinimumOrders(Number(event.target.value))} /><p>Each multi-cuisine transaction contributes 1/n to its cuisines. Comparison evidence must reach at least {formatNumber(Math.max(25, minimumOrders / 2))} allocated transactions.</p></section>

    <section className="cuisine-analysis-grid">
      <CuisineDemandChart cuisines={cuisineSummary.slice(0, 10)} />
      {selected ? <CuisineBrief pair={selected} /> : <article className="panel"><EmptyState compact /></article>}
    </section>

    <CuisineHeatmap pairs={scopedPairs} select={(pair) => setSelectedKey(`${pair.market}|${pair.cuisine}`)} />

    <article className="panel cuisine-table-panel"><div className="panel-head"><div><span className="section-kicker">Category action queue</span><h2>Eligible cuisine-market opportunities</h2></div><div className="table-actions"><select aria-label="Rank opportunities by" value={sortBy} onChange={(event) => setSortBy(event.target.value as typeof sortBy)}><option value="opportunity_score">Rank by opportunity signal</option><option value="allocated_orders">Rank by demand</option><option value="growth">Rank by growth</option><option value="demand_to_listing_index">Rank by demand/listing index</option></select><button className="export-button" type="button" onClick={() => exportCuisinePairs(ranked, view.period, market)}>↓ Export CSV</button></div></div><div className="table-scroll"><table className="data-table cuisine-table"><thead><tr><th>Market · Cuisine</th><th>Signal</th><th>Allocated txns</th><th>Growth</th><th>Customers</th><th>Listings</th><th>Demand / listing</th><th>Rating cov.</th><th>Menu cov.</th><th>Confidence</th><th>Recommended action</th></tr></thead><tbody>{ranked.map((row) => { const key = `${row.market}|${row.cuisine}`; const selectedRow = selected && `${selected.market}|${selected.cuisine}` === key; return <tr aria-label={`Select ${row.market} ${row.cuisine}`} aria-selected={selectedRow} className={selectedRow ? 'selected-row' : ''} key={key} tabIndex={0} onClick={() => setSelectedKey(key)} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); setSelectedKey(key); } }}><th><b>{row.market}</b><span>{row.cuisine}</span></th><td><strong className="score-cell">{row.opportunity_score.toFixed(1)}</strong></td><td>{formatDecimal(row.allocated_orders)}</td><td className={growthClass(row.growth)}>{formatSignedPercent(row.growth)}</td><td>{formatNumber(row.customers)}</td><td>{formatNumber(row.observed_listings)}</td><td>{row.demand_to_listing_index?.toFixed(2) ?? '—'}×</td><td>{formatPercent(row.rating_coverage)}</td><td>{formatPercent(row.menu_coverage)}</td><td><span className={`confidence inline-confidence ${row.confidence.toLowerCase()}`}>{row.confidence}</span></td><td>{row.recommended_action}</td></tr>; })}</tbody></table></div></article>

    <RestaurantEvidence mapping={restaurantMapping} observations={restaurantObservations} />
    <div className="market-method-note cuisine-method-note"><b>Analytical boundary</b><p>Allocated transaction and sales totals reconcile because every valid cuisine-covered row contributes exactly 1.0 across its observed cuisines. “Observed listings” uses conservative normalized restaurant names—not durable outlet supply. Restaurant performance is intentionally not ranked because only {formatNumber(restaurantMapping.restaurant_ids_repeated)} restaurant IDs repeat.</p></div>
  </>;
}

function CuisineDemandChart({ cuisines }: { cuisines: CuisineSummary[] }) {
  const max = Math.max(...cuisines.map((row) => row.allocated_orders), 1);
  return <article className="panel cuisine-demand"><div className="panel-head"><div><span className="section-kicker">Allocated demand</span><h2>Leading cuisine demand</h2></div><span className="coverage-note">Additive 1/n allocation</span></div><div className="cuisine-demand-list">{cuisines.map((row, index) => <div key={row.cuisine}><span className="rank">{String(index + 1).padStart(2, '0')}</span><b>{row.cuisine}</b><div><i style={{ width: `${row.allocated_orders / max * 100}%` }} /></div><strong>{formatDecimal(row.allocated_orders)}</strong><small>{formatCrore(row.allocated_sales)}</small></div>)}</div></article>;
}

function CuisineBrief({ pair }: { pair: CuisinePair }) {
  return <article className="panel cuisine-brief"><div className="panel-head"><div><span className="section-kicker">Selected signal</span><h2>{pair.market} · {pair.cuisine}</h2></div><span className={`confidence ${pair.confidence.toLowerCase()}`}>{pair.confidence} confidence</span></div><div className="opportunity-score"><div><span>Opportunity signal</span><strong>{pair.opportunity_score.toFixed(1)}</strong><small>/ 100</small></div><i><b style={{ width: `${pair.opportunity_score}%` }} /></i></div><div className="brief-callout cuisine-action"><span>01</span><div><b>Recommended investigation</b><p>{pair.recommended_action}</p></div></div><dl className="market-facts"><div><dt>Allocated transaction growth</dt><dd className={growthClass(pair.growth)}>{formatSignedPercent(pair.growth)}</dd></div><div><dt>Customer reach</dt><dd>{formatNumber(pair.customers)}</dd></div><div><dt>Observed normalized listings</dt><dd>{formatNumber(pair.observed_listings)}</dd></div><div><dt>Demand-to-listing index</dt><dd>{pair.demand_to_listing_index?.toFixed(2) ?? '—'}×</dd></div><div><dt>Rating / menu coverage</dt><dd>{formatPercent(pair.rating_coverage)} / {formatPercent(pair.menu_coverage)}</dd></div></dl><p className="hypothesis-note">A high signal prioritizes investigation; it does not prove unmet supply or causal demand.</p></article>;
}

function CuisineHeatmap({ pairs, select }: { pairs: CuisinePair[]; select: (pair: CuisinePair) => void }) {
  const marketTotals = new Map<string, number>(); const cuisineTotals = new Map<string, number>();
  for (const row of pairs) { marketTotals.set(row.market, (marketTotals.get(row.market) ?? 0) + row.allocated_orders); cuisineTotals.set(row.cuisine, (cuisineTotals.get(row.cuisine) ?? 0) + row.allocated_orders); }
  const markets = [...marketTotals.entries()].sort((a, b) => b[1] - a[1]).slice(0, 7).map(([name]) => name);
  const cuisines = [...cuisineTotals.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8).map(([name]) => name);
  const lookup = new Map(pairs.map((row) => [`${row.market}|${row.cuisine}`, row]));
  const max = Math.max(...pairs.filter((row) => markets.includes(row.market) && cuisines.includes(row.cuisine)).map((row) => row.allocated_orders), 1);
  return <article className="panel cuisine-heatmap-panel"><div className="panel-head"><div><span className="section-kicker">Demand footprint</span><h2>Cuisine-market demand heatmap</h2></div><span className="coverage-note">Click a cell to inspect</span></div><div className="heatmap-scroll"><table className="heatmap cuisine-heatmap"><thead><tr><th>Market</th>{cuisines.map((cuisine) => <th key={cuisine}>{cuisine}</th>)}</tr></thead><tbody>{markets.map((marketName) => <tr key={marketName}><th>{marketName}</th>{cuisines.map((cuisine) => { const pair = lookup.get(`${marketName}|${cuisine}`); return <td key={cuisine} style={{ backgroundColor: cuisineHeat(pair?.allocated_orders ?? 0, max) }}>{pair ? <button aria-label={`${marketName} ${cuisine}: ${formatDecimal(pair.allocated_orders)} allocated transactions`} type="button" onClick={() => select(pair)} title={`${marketName} · ${cuisine}: ${formatDecimal(pair.allocated_orders)} allocated transactions`}>{formatDecimal(pair.allocated_orders)}</button> : '—'}</td>; })}</tr>)}</tbody></table></div><p className="panel-note">Darker cells represent greater proportionally allocated transaction demand. This view does not imply individual restaurant performance.</p></article>;
}

function RestaurantEvidence({ mapping, observations }: { mapping: AnalyticsData['restaurant_mapping']; observations: AnalyticsData['restaurant_observations'] }) {
  return <section className="restaurant-evidence"><article className="panel restaurant-context"><span className="section-kicker">Restaurant identity audit</span><h2>Conservative name normalization</h2><div className="restaurant-audit-metrics"><div><strong>{formatNumber(mapping.raw_names)}</strong><span>Raw names</span></div><div><strong>{formatNumber(mapping.normalized_names)}</strong><span>Normalized names</span></div><div><strong>{formatNumber(mapping.repeat_normalized_names)}</strong><span>Repeated names</span></div><div><strong>{formatNumber(mapping.restaurant_ids_repeated)}</strong><span>Repeated IDs</span></div></div><p>Normalization only standardizes case, punctuation, accents and “&amp;”. It does not remove outlet locations or fuzzy-merge brands, protecting against false chain matches.</p></article><article className="panel observed-chains"><div className="panel-head"><div><span className="section-kicker">Coverage context</span><h2>Most-observed normalized names</h2></div></div><div>{observations.slice(0, 7).map((row) => <div key={row.normalized_name}><b>{titleCase(row.normalized_name)}</b><span>{formatNumber(row.observed_rows)} rows</span><small>{formatNumber(row.distinct_restaurant_ids)} IDs · {formatNumber(row.markets)} markets</small></div>)}</div></article></section>;
}

function Reliability({ data }: { data: AnalyticsData }) {
  const q = data.quality;
  const issues = [
    { issue: 'Zero sales', rows: q.zero_sales, treatment: 'Excluded from business KPIs', severity: 'High' },
    { issue: 'Missing sales', rows: q.missing_sales, treatment: 'Excluded; preserved in audit totals', severity: 'High' },
    { issue: 'Unsupported currency', rows: q.unsupported_currency, treatment: 'USD rows excluded from INR KPIs', severity: 'High' },
    { issue: 'Missing rating', rows: Math.round(q.raw_rows * (1 - q.rating_coverage)), treatment: 'No imputation; coverage always shown', severity: 'Medium' },
    { issue: 'Missing menu attributes', rows: Math.round(q.raw_rows * (1 - q.menu_coverage)), treatment: 'Menu analysis marked low coverage', severity: 'Medium' },
  ];
  return <>
    <section className="kpi-grid reliability-kpis"><Kpi label="Valid transaction rate" value={formatPercent(q.valid_rate)} note={`${formatNumber(q.valid_transactions)} rows retained`} tone="teal" definition="Rows passing the strict business KPI rule." /><Kpi label="Rating coverage" value={formatPercent(q.rating_coverage)} note="Never imputed" tone="amber" definition="Rows with observed restaurant ratings." /><Kpi label="Menu coverage" value={formatPercent(q.menu_coverage)} note="Low-confidence analysis" tone="coral" definition="Rows with observed menu item count." warning /><Kpi label="Restaurant match" value={formatPercent(q.restaurant_match_rate)} note="Source-provided match flag" tone="blue" definition="Rows passing the source restaurant-match flag." /><Kpi label="Schema integrity" value="36 / 36" note="0 duplicate order IDs" tone="violet" definition="Expected source columns present and order IDs unique." /></section>
    <section className="reliability-grid"><article className="panel quality-overview"><div className="panel-head"><div><span className="section-kicker">Audit trail</span><h2>Transaction reconciliation</h2></div><span className="confidence high">High confidence</span></div><div className="reconciliation"><div><strong>{formatNumber(q.raw_rows)}</strong><span>Raw rows</span></div><b>−</b><div><strong>{formatNumber(q.excluded_transactions)}</strong><span>Excluded rows</span></div><b>=</b><div className="valid"><strong>{formatNumber(q.valid_transactions)}</strong><span>Valid transactions</span></div></div><div className="quality-rule"><b>Valid transaction rule</b><code>order_id present · MM/DD/YYYY date parses · source flag true · sales &gt; 0 · currency = INR</code></div></article><article className="panel source-card"><span className="section-kicker">Source fingerprint</span><h2>{data.source.filename}</h2><dl><div><dt>Rows</dt><dd>{formatNumber(data.source.rows)}</dd></div><div><dt>Columns</dt><dd>{data.source.columns}</dd></div><div><dt>Date window</dt><dd>{formatDate(data.source.date_min)} — {formatDate(data.source.date_max)}</dd></div><div><dt>Date format</dt><dd>{data.source.date_format}</dd></div><div><dt>Checksum</dt><dd title={data.source.sha256}>{data.source.sha256.slice(0, 12)}…</dd></div></dl></article></section>
    <article className="panel issue-table"><div className="panel-head"><div><span className="section-kicker">Known limitations</span><h2>Quality issues and metric treatment</h2></div></div><div className="table-scroll"><table className="data-table"><thead><tr><th>Issue</th><th>Affected rows</th><th>Severity</th><th>Implemented treatment</th></tr></thead><tbody>{issues.map((item) => <tr key={item.issue}><th>{item.issue}</th><td>{formatNumber(item.rows)}</td><td><span className={`severity ${item.severity.toLowerCase()}`}>{item.severity}</span></td><td>{item.treatment}</td></tr>)}</tbody></table></div></article>
    <div className="responsibility-note"><b>Responsible analytics boundary</b><p>No delivery-time, cancellation, discount, payment, commission, funnel or campaign metrics are shown because those fields do not exist in the source. Demographic differences are descriptive only—not causal targeting recommendations.</p></div>
  </>;
}

type DecisionWeights = { demand: number; growth: number; reach: number; gap: number; quality: number };
type DecisionDimension = keyof DecisionWeights;
type DecisionScenario = { id: string; name: string; weights: DecisionWeights; confidenceDiscount: boolean };
type DecisionRow = CuisinePair & { lab_score: number; rank: number; dimensions: Record<DecisionDimension, number>; baseline_rank: number | null; rank_delta: number | null };

const DEFAULT_DECISION_WEIGHTS: DecisionWeights = { demand: 25, growth: 25, reach: 20, gap: 15, quality: 15 };
const BASE_DECISION_SCENARIO: DecisionScenario = { id: 'balanced', name: 'Balanced guardrails', weights: DEFAULT_DECISION_WEIGHTS, confidenceDiscount: true };
const DECISION_DIMENSIONS: { key: DecisionDimension; label: string; description: string }[] = [
  { key: 'demand', label: 'Demand scale', description: 'Allocated transactions in the current window.' },
  { key: 'growth', label: 'Growth momentum', description: 'Comparable-window transaction growth.' },
  { key: 'reach', label: 'Customer reach', description: 'Distinct customers reached by the pair.' },
  { key: 'gap', label: 'Coverage gap', description: 'Relative demand-to-listing index.' },
  { key: 'quality', label: 'Data quality', description: 'Rating and menu field coverage.' },
];

function DecisionLab({ view, market, period }: { view: CuisineView; market: string; period: string }) {
  const [minimumOrders, setMinimumOrders] = useState(100);
  const [weights, setWeights] = useState<DecisionWeights>(DEFAULT_DECISION_WEIGHTS);
  const [confidenceDiscount, setConfidenceDiscount] = useState(true);
  const [scenarioName, setScenarioName] = useState('');
  const [comparisonId, setComparisonId] = useState(BASE_DECISION_SCENARIO.id);
  const [scenarios, setScenarios] = useState<DecisionScenario[]>(readDecisionScenarios);
  const scopedPairs = view.pairs.filter((row) => market === 'All markets' || row.market === market);
  const weightTotal = Object.values(weights).reduce((sum, value) => sum + value, 0);
  const currentRows = useMemo(() => scoreDecisionPairs(scopedPairs, minimumOrders, weights, confidenceDiscount), [scopedPairs, minimumOrders, weights, confidenceDiscount]);
  const baselineRows = useMemo(() => scoreDecisionPairs(scopedPairs, minimumOrders, DEFAULT_DECISION_WEIGHTS, true), [scopedPairs, minimumOrders]);
  const baselineRanks = new Map(baselineRows.map((row) => [decisionKey(row), row.rank]));
  const rankedRows: DecisionRow[] = currentRows.map((row) => ({ ...row, baseline_rank: baselineRanks.get(decisionKey(row)) ?? null, rank_delta: baselineRanks.has(decisionKey(row)) ? (baselineRanks.get(decisionKey(row))! - row.rank) : null }));
  const comparisonScenario = scenarios.find((scenario) => scenario.id === comparisonId) ?? BASE_DECISION_SCENARIO;
  const comparisonRows = useMemo(() => scoreDecisionPairs(scopedPairs, minimumOrders, comparisonScenario.weights, comparisonScenario.confidenceDiscount), [scopedPairs, minimumOrders, comparisonScenario]);
  const top = rankedRows[0];
  const baselineTop = baselineRows[0];

  function updateWeight(key: DecisionDimension, value: number) {
    setWeights((current) => ({ ...current, [key]: value }));
  }

  function loadScenario(scenario: DecisionScenario) {
    setWeights(scenario.weights);
    setConfidenceDiscount(scenario.confidenceDiscount);
    setComparisonId(scenario.id);
  }

  function saveScenario() {
    const name = scenarioName.trim();
    if (!name) return;
    const scenario: DecisionScenario = { id: `scenario-${Date.now()}`, name: name.slice(0, 40), weights: { ...weights }, confidenceDiscount };
    const next = [...scenarios.filter((item) => item.id !== scenario.id), scenario];
    setScenarios(next);
    persistDecisionScenarios(next);
    setScenarioName('');
    setComparisonId(scenario.id);
  }

  function removeScenario(id: string) {
    const next = scenarios.filter((scenario) => scenario.id !== id);
    setScenarios(next);
    persistDecisionScenarios(next);
    if (comparisonId === id) setComparisonId(BASE_DECISION_SCENARIO.id);
  }

  if (view.empty || !view.summary) return <EmptyState />;

  return <>
    <div className="market-window decision-window"><div><span>Current comparable window</span><b>{view.current_window}</b></div><i>versus</i><div><span>Previous equal-length window</span><b>{view.comparison_window}</b></div><strong>{market === 'All markets' ? 'All cleaned markets' : market}</strong></div>

    <section className="decision-intro panel"><div><span className="decision-tag">Live scoring sandbox</span><h2>Make the trade-offs explicit</h2><p>Adjust the evidence mix, compare it with a saved scenario, and export a ranked investigation brief. Every signal stays bounded by the same cuisine allocation and sample-size rules.</p></div><div className="decision-intro-stat"><span>Current lab leader</span><strong>{top ? `${top.market} · ${top.cuisine}` : '—'}</strong><small>{top ? `${top.lab_score.toFixed(1)} / 100` : 'No eligible evidence'}</small></div></section>

    <section className="decision-layout">
      <DecisionWeightsPanel weights={weights} updateWeight={updateWeight} total={weightTotal} />
      <div className="decision-side-column">
        <article className="panel decision-guardrails"><div className="panel-head"><div><span className="section-kicker">Evidence guardrails</span><h2>Keep the ranking defensible</h2></div><span className="confidence high">Always on</span></div><label className="decision-range"><span><b>Minimum allocated transactions</b><output aria-live="polite">{formatNumber(minimumOrders)}</output></span><input aria-label="Decision minimum allocated transactions" type="range" min="50" max="500" step="50" value={minimumOrders} onChange={(event) => setMinimumOrders(Number(event.target.value))} /></label><label className="decision-check"><input aria-label="Apply confidence discount" type="checkbox" checked={confidenceDiscount} onChange={(event) => setConfidenceDiscount(event.target.checked)} /><span><b>Apply confidence discount</b><small>Medium evidence is multiplied by 0.85; low evidence by 0.65.</small></span></label><p className="panel-note">Comparison evidence must reach at least {formatNumber(Math.max(25, minimumOrders / 2))} allocated transactions. Scores are relative within this filtered view.</p></article>

        <article className="panel decision-presets"><div className="panel-head"><div><span className="section-kicker">Saved presets</span><h2>Scenario library</h2></div><span className="coverage-note">Stored on this device</span></div><div className="save-scenario"><input aria-label="Scenario name" placeholder="Name this weighting" value={scenarioName} onChange={(event) => setScenarioName(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') saveScenario(); }} /><button type="button" onClick={saveScenario} disabled={!scenarioName.trim()}>Save</button></div><div className="preset-list">{scenarios.map((scenario) => <div className={scenario.id === comparisonId ? 'preset-row selected' : 'preset-row'} key={scenario.id}><div><b>{scenario.name}</b><small>{scenarioSummary(scenario)} · {scenario.confidenceDiscount ? 'confidence adjusted' : 'no discount'}</small></div><div><button type="button" onClick={() => loadScenario(scenario)}>Load</button>{scenario.id !== BASE_DECISION_SCENARIO.id && <button className="preset-remove" type="button" onClick={() => removeScenario(scenario.id)} aria-label={`Remove ${scenario.name}`}>×</button>}</div></div>)}</div><p className="panel-note">Presets are local device preferences; they do not change the underlying source metrics.</p></article>
      </div>
    </section>

    <DecisionScenarioCompare current={rankedRows} comparison={comparisonRows} comparisonScenario={comparisonScenario} scenarios={scenarios} comparisonId={comparisonId} setComparisonId={setComparisonId} baselineTop={baselineTop} />

    <article className="panel decision-table-panel"><div className="panel-head"><div><span className="section-kicker">Decision brief</span><h2>Ranked investigation queue</h2></div><div className="table-actions"><span className="decision-count">{formatNumber(rankedRows.length)} eligible pairs</span><button className="export-button" type="button" onClick={() => exportDecisionBrief(rankedRows, weights, confidenceDiscount, market, period, minimumOrders)}>↓ Export brief</button></div></div><div className="table-scroll"><table className="data-table decision-table"><thead><tr><th>Rank · market / cuisine</th><th>Lab score</th><th>Move</th><th>Demand</th><th>Growth</th><th>Reach</th><th>Gap</th><th>Quality</th><th>Confidence</th><th>Recommended next action</th></tr></thead><tbody>{rankedRows.slice(0, 25).map((row) => <tr key={decisionKey(row)}><th><div className="decision-rank"><span>{String(row.rank).padStart(2, '0')}</span><div><b>{row.market}</b><small>{row.cuisine}</small></div></div></th><td><strong className="score-cell">{row.lab_score.toFixed(1)}</strong></td><td className={rankMovementClass(row.rank_delta)}>{rankMovement(row.rank_delta)}</td><td><DecisionDimensionCell value={row.dimensions.demand} /></td><td><DecisionDimensionCell value={row.dimensions.growth} /></td><td><DecisionDimensionCell value={row.dimensions.reach} /></td><td><DecisionDimensionCell value={row.dimensions.gap} /></td><td><DecisionDimensionCell value={row.dimensions.quality} /></td><td><span className={`confidence inline-confidence ${row.confidence.toLowerCase()}`}>{row.confidence}</span></td><td>{row.recommended_action}</td></tr>)}</tbody></table></div>{rankedRows.length > 25 && <p className="panel-note decision-table-note">Showing the top 25 of {formatNumber(rankedRows.length)} eligible pairs. Export the brief for the full ranked queue.</p>}</article>

    <section className="decision-footer-grid"><article className="panel decision-brief-card"><span className="section-kicker">How to use this signal</span><h2>{top ? `${top.market} · ${top.cuisine} is the current investigation lead.` : 'No pair clears the selected evidence threshold.'}</h2><p>{top ? `The lab gives this pair a ${top.lab_score.toFixed(1)} score under the current weighting. The baseline score was ${baselineTop ? `${baselineTop.market} · ${baselineTop.cuisine}` : 'not available'}; use the movement column to see what changed.` : 'Lower the threshold only when the resulting evidence remains appropriate for the decision being made.'}</p><div className="brief-formula"><span>Score formula</span><b>Demand {weights.demand}% · Growth {weights.growth}% · Reach {weights.reach}% · Gap {weights.gap}% · Quality {weights.quality}%</b><small>Weights are normalized to 100% for calculation. Confidence adjustment: {confidenceDiscount ? 'on' : 'off'}.</small></div></article><article className="panel decision-boundary-card"><span className="section-kicker">Decision boundary</span><h2>Prioritisation is not proof</h2><p>The score is a transparent relative ranking for Product, Growth and Category teams. It does not forecast demand, prove unmet supply, or replace restaurant-level validation.</p><div><b>Observed supply context</b><span>Restaurant listings are conservative normalized names; outlet IDs rarely repeat.</span></div><div><b>Data quality context</b><span>Rating and menu coverage remain visible beside every opportunity.</span></div></article></section>
  </>;
}

function DecisionWeightsPanel({ weights, updateWeight, total }: { weights: DecisionWeights; updateWeight: (key: DecisionDimension, value: number) => void; total: number }) {
  return <article className="panel decision-weight-panel"><div className="panel-head"><div><span className="section-kicker">Configurable score</span><h2>What should matter most?</h2></div><span className={total === 100 ? 'weight-total valid' : 'weight-total'}>{total}% total</span></div><p className="decision-panel-copy">Set the relative importance of each evidence dimension. The calculation normalizes any total to 100% so you can explore trade-offs without breaking the score.</p><div className="decision-weight-list">{DECISION_DIMENSIONS.map((dimension) => <label className="decision-weight" key={dimension.key}><span><b>{dimension.label}</b><output>{weights[dimension.key]}%</output></span><input aria-label={`${dimension.label} weight`} type="range" min="0" max="50" step="5" value={weights[dimension.key]} onChange={(event) => updateWeight(dimension.key, Number(event.target.value))} /><small>{dimension.description}</small></label>)}</div><div className="weight-foot"><span>Suggested starting point</span><b>Balanced guardrails</b><button type="button" onClick={() => DECISION_DIMENSIONS.forEach((dimension) => updateWeight(dimension.key, DEFAULT_DECISION_WEIGHTS[dimension.key]))}>Reset weights</button></div></article>;
}

function DecisionScenarioCompare({ current, comparison, comparisonScenario, scenarios, comparisonId, setComparisonId, baselineTop }: { current: DecisionRow[]; comparison: DecisionRow[]; comparisonScenario: DecisionScenario; scenarios: DecisionScenario[]; comparisonId: string; setComparisonId: (id: string) => void; baselineTop?: DecisionRow }) {
  const currentTop = current[0];
  const comparisonTop = comparison[0];
  const sameLeader = currentTop && comparisonTop && decisionKey(currentTop) === decisionKey(comparisonTop);
  return <article className="panel decision-compare-panel"><div className="panel-head"><div><span className="section-kicker">Scenario comparison</span><h2>See what the weighting changes</h2></div><label className="compare-select"><span>Compare current lab with</span><select aria-label="Compare current lab with" value={comparisonId} onChange={(event) => setComparisonId(event.target.value)}>{scenarios.map((scenario) => <option key={scenario.id} value={scenario.id}>{scenario.name}</option>)}</select></label></div><div className="decision-compare-grid"><div className="compare-card current"><span>Current lab</span><strong>{currentTop ? `${currentTop.market} · ${currentTop.cuisine}` : '—'}</strong><b>{currentTop ? currentTop.lab_score.toFixed(1) : '—'} <small>/ 100</small></b><p>Active weights and guardrails</p></div><div className="compare-arrow">↔</div><div className="compare-card"><span>{comparisonScenario.name}</span><strong>{comparisonTop ? `${comparisonTop.market} · ${comparisonTop.cuisine}` : '—'}</strong><b>{comparisonTop ? comparisonTop.lab_score.toFixed(1) : '—'} <small>/ 100</small></b><p>{comparisonScenario.confidenceDiscount ? 'Confidence adjusted' : 'No confidence discount'}</p></div></div><div className="decision-comparison-note"><b>{sameLeader ? 'Leader is stable under both scenarios.' : 'Leader changes under this scenario.'}</b><span>{baselineTop && comparisonTop ? `Balanced baseline leads with ${baselineTop.market} · ${baselineTop.cuisine}; compare rank movement before acting.` : 'Use a broader filter or lower threshold to create a comparable evidence base.'}</span></div></article>;
}

function DecisionDimensionCell({ value }: { value: number }) { return <span className="dimension-cell"><i style={{ width: `${Math.max(4, value)}%` }} /><b>{Math.round(value)}</b></span>; }

function scoreDecisionPairs(pairs: CuisinePair[], minimumOrders: number, weights: DecisionWeights, confidenceDiscount: boolean): DecisionRow[] {
  const comparisonMinimum = Math.max(25, minimumOrders / 2);
  const eligible = pairs.filter((row) => row.allocated_orders >= minimumOrders && row.previous_allocated_orders >= comparisonMinimum && row.growth !== null);
  const values: Record<DecisionDimension, number[]> = {
    demand: eligible.map((row) => row.allocated_orders),
    growth: eligible.map((row) => row.growth ?? -1),
    reach: eligible.map((row) => row.customers),
    gap: eligible.map((row) => row.demand_to_listing_index ?? 0),
    quality: eligible.map((row) => (row.rating_coverage + row.menu_coverage) / 2),
  };
  const normalized = normalizeDecisionWeights(weights);
  const scored = eligible.map((row) => {
    const dimensions = {
      demand: percentileScore(row.allocated_orders, values.demand),
      growth: percentileScore(row.growth ?? -1, values.growth),
      reach: percentileScore(row.customers, values.reach),
      gap: percentileScore(row.demand_to_listing_index ?? 0, values.gap),
      quality: percentileScore((row.rating_coverage + row.menu_coverage) / 2, values.quality),
    } satisfies Record<DecisionDimension, number>;
    const rawScore = DECISION_DIMENSIONS.reduce((sum, dimension) => sum + dimensions[dimension.key] * normalized[dimension.key], 0);
    const confidenceFactor = confidenceDiscount ? ({ High: 1, Medium: .85, Low: .65 } as const)[row.confidence] : 1;
    return { ...row, dimensions, lab_score: rawScore * confidenceFactor };
  });
  return scored.sort((a, b) => b.lab_score - a.lab_score || b.allocated_orders - a.allocated_orders || decisionKey(a).localeCompare(decisionKey(b))).map((row, index) => ({ ...row, rank: index + 1, baseline_rank: null, rank_delta: null }));
}

function normalizeDecisionWeights(weights: DecisionWeights): DecisionWeights {
  const total = Object.values(weights).reduce((sum, value) => sum + value, 0);
  if (!total) return { demand: 1, growth: 0, reach: 0, gap: 0, quality: 0 };
  return { demand: weights.demand / total, growth: weights.growth / total, reach: weights.reach / total, gap: weights.gap / total, quality: weights.quality / total };
}

function percentileScore(value: number, values: number[]) { if (!values.length) return 0; return values.filter((candidate) => candidate <= value).length / values.length * 100; }
function decisionKey(row: Pick<CuisinePair, 'market' | 'cuisine'>) { return `${row.market}|${row.cuisine}`; }
function scenarioSummary(scenario: DecisionScenario) { return `D${scenario.weights.demand} · G${scenario.weights.growth} · R${scenario.weights.reach} · Gap${scenario.weights.gap} · Q${scenario.weights.quality}`; }
function rankMovement(value: number | null) { if (value === null) return 'new'; if (value > 0) return `↑${value}`; if (value < 0) return `↓${Math.abs(value)}`; return '—'; }
function rankMovementClass(value: number | null) { return value === null ? 'rank-new' : value > 0 ? 'rank-up' : value < 0 ? 'rank-down' : 'rank-flat'; }
function readDecisionScenarios(): DecisionScenario[] { if (typeof window === 'undefined') return [BASE_DECISION_SCENARIO]; try { const stored = JSON.parse(window.localStorage.getItem('platelens-decision-scenarios') ?? '[]') as DecisionScenario[]; const valid = Array.isArray(stored) ? stored.filter((scenario) => scenario && scenario.id && scenario.id !== BASE_DECISION_SCENARIO.id && scenario.name && scenario.weights) : []; return [BASE_DECISION_SCENARIO, ...valid]; } catch { return [BASE_DECISION_SCENARIO]; } }
function persistDecisionScenarios(scenarios: DecisionScenario[]) { if (typeof window === 'undefined') return; try { window.localStorage.setItem('platelens-decision-scenarios', JSON.stringify(scenarios.filter((scenario) => scenario.id !== BASE_DECISION_SCENARIO.id))); } catch { /* device storage is optional */ } }

function PlannedModule({ page, goTo }: { page: PageId; goTo: (page: PageId) => void }) {
  const steps: Record<string, string[]> = { markets: ['Create auditable locality-to-metro mapping', 'Add minimum sample eligibility rules', 'Build market scale-versus-growth quadrant'], cuisines: ['Normalise cuisine labels', 'Allocate multi-cuisine demand proportionally', 'Add demand-to-coverage opportunity scoring'], decision: ['Validate market and cuisine inputs', 'Add configurable score weights', 'Export evidence, confidence and next actions'] };
  return <section className="planned-module"><span className="planned-badge">Planned next phase</span><h2>This module has a defined build path—not placeholder metrics.</h2><p>The foundation intentionally ships Product/Growth analytics first. The next module will inherit the same audited transaction rule, global filters and confidence labels.</p><ol>{(steps[page] ?? []).map((step, index) => <li key={step}><span>0{index + 1}</span>{step}</li>)}</ol><button className="primary-button inline" type="button" onClick={() => goTo('customers')}>Return to working module <span>→</span></button></section>;
}

function Kpi({ label, value, note, tone, definition, warning = false }: { label: string; value: string; note: string; tone: string; definition: string; warning?: boolean }) {
  return <article className="kpi-card"><div className={`kpi-icon ${tone}`}>{warning ? '!' : '↗'}</div><div className="kpi-copy"><span>{label} <abbr title={definition}>i</abbr></span><strong>{value}</strong><small>{note}</small></div></article>;
}

function Methodology({ data, close }: { data: AnalyticsData; close: () => void }) {
  return <div className="modal-backdrop" role="presentation" onMouseDown={close}><section className="method-modal" role="dialog" aria-modal="true" aria-labelledby="method-title" onMouseDown={(event) => event.stopPropagation()}><div className="modal-head"><div><span className="section-kicker">Transparent by design</span><h2 id="method-title">Metric dictionary &amp; methodology</h2></div><button type="button" onClick={close} aria-label="Close">×</button></div><p>Definitions apply consistently across global filters. The source CSV is transformed into deployment-safe aggregates; raw customer records and addresses are never sent to the browser.</p><dl className="definition-list">{Object.entries(data.definitions).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{value}</dd></div>)}</dl><div className="method-foot"><span>Source SHA-256</span><code>{data.source.sha256}</code></div></section></div>;
}

function EmptyState({ compact = false }: { compact?: boolean }) { return <section className={compact ? 'empty-state compact' : 'empty-state'}><span>∅</span><h2>No defensible result for this filter</h2><p>Reset the filters or choose a broader period. PlateLens suppresses empty and insufficient evidence instead of rendering misleading charts.</p></section>; }

function exportSegments(segments: Segment[], market: string, period: string) {
  const headers = ['segment', 'customers', 'customer_share', 'orders_per_customer', 'sales_per_customer', 'repeat_rate', 'median_recency_days', 'recommended_action'];
  const rows = segments.map((segment) => [segment.segment, segment.customers, segment.customer_share, segment.orders_per_customer, segment.sales_per_customer, segment.repeat_rate, segment.median_recency, segment.action]);
  const csv = [headers, ...rows].map((row) => row.map(csvCell).join(',')).join('\n');
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = `platelens-segments-${market}-${period}.csv`.replaceAll(' ', '-').toLowerCase(); anchor.click(); URL.revokeObjectURL(url);
}

function exportMarkets(markets: MarketRow[], period: string) {
  const headers = ['market', 'transactions', 'transaction_growth', 'customers', 'repeat_rate', 'average_transaction_value', 'transaction_share', 'confidence'];
  const rows = markets.map((market) => [market.market, market.orders, market.growth_orders ?? '', market.customers, market.repeat_rate, market.average_transaction_value, market.order_share, market.confidence]);
  const csv = [headers, ...rows].map((row) => row.map(csvCell).join(',')).join('\n');
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = `platelens-market-ranking-${period}.csv`.replaceAll(' ', '-').toLowerCase(); anchor.click(); URL.revokeObjectURL(url);
}

function exportCuisinePairs(pairs: CuisinePair[], period: string, market: string) {
  const headers = ['market', 'cuisine', 'opportunity_signal', 'allocated_transactions', 'transaction_growth', 'customers', 'observed_listings', 'demand_to_listing_index', 'rating_coverage', 'menu_coverage', 'confidence', 'recommended_action'];
  const rows = pairs.map((pair) => [pair.market, pair.cuisine, pair.opportunity_score, pair.allocated_orders, pair.growth ?? '', pair.customers, pair.observed_listings, pair.demand_to_listing_index ?? '', pair.rating_coverage, pair.menu_coverage, pair.confidence, pair.recommended_action]);
  const csv = [headers, ...rows].map((row) => row.map(csvCell).join(',')).join('\n');
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = `platelens-cuisine-opportunities-${market}-${period}.csv`.replaceAll(' ', '-').toLowerCase(); anchor.click(); URL.revokeObjectURL(url);
}

function exportDecisionBrief(rows: DecisionRow[], weights: DecisionWeights, confidenceDiscount: boolean, market: string, period: string, minimumOrders: number) {
  const headers = ['rank', 'market', 'cuisine', 'lab_score', 'baseline_rank', 'rank_movement', 'demand_dimension', 'growth_dimension', 'reach_dimension', 'gap_dimension', 'quality_dimension', 'confidence', 'allocated_transactions', 'transaction_growth', 'observed_listings', 'recommended_action'];
  const metadata = [['scope', market, 'period', period, 'minimum_allocated_transactions', minimumOrders, 'confidence_discount', confidenceDiscount ? 'on' : 'off'], ['weights', scenarioSummary({ id: 'export', name: 'Export', weights, confidenceDiscount })]];
  const dataRows = rows.map((row) => [row.rank, row.market, row.cuisine, row.lab_score.toFixed(2), row.baseline_rank ?? '', rankMovement(row.rank_delta), Math.round(row.dimensions.demand), Math.round(row.dimensions.growth), Math.round(row.dimensions.reach), Math.round(row.dimensions.gap), Math.round(row.dimensions.quality), row.confidence, row.allocated_orders, row.growth ?? '', row.observed_listings, row.recommended_action]);
  const csv = [...metadata, headers, ...dataRows].map((row) => row.map(csvCell).join(',')).join('\n');
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = `platelens-decision-brief-${market}-${period}.csv`.replaceAll(' ', '-').toLowerCase(); anchor.click(); URL.revokeObjectURL(url);
}

function csvCell(value: string | number) { const text = String(value); return `"${text.replaceAll('"', '""')}"`; }
function formatNumber(value: number) { return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(value); }
function formatDecimal(value: number) { return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 1 }).format(value); }
function formatPercent(value: number) { return new Intl.NumberFormat('en-IN', { style: 'percent', maximumFractionDigits: 1 }).format(value); }
function formatSignedPercent(value: number | null) { if (value === null) return 'Not comparable'; const formatted = new Intl.NumberFormat('en-IN', { style: 'percent', maximumFractionDigits: 1, signDisplay: 'always' }).format(value); return formatted; }
function formatRupee(value: number) { return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value); }
function formatCrore(value: number) { return `₹${(value / 10_000_000).toFixed(value >= 100_000_000 ? 2 : 1)} Cr`; }
function compact(value: number) { return new Intl.NumberFormat('en-IN', { notation: 'compact', maximumFractionDigits: 1 }).format(value); }
function formatDate(value: string) { return new Intl.DateTimeFormat('en-IN', { month: 'short', year: 'numeric' }).format(new Date(`${value}T00:00:00`)); }
function shortMonth(value?: string) { if (!value) return '—'; return new Intl.DateTimeFormat('en-IN', { month: 'short', year: '2-digit' }).format(new Date(`${value}-01T00:00:00`)); }
function initials(name: string) { return name.split(/\s|@/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join('') || 'PL'; }
function firstName(name: string) { return name.includes('@') ? name.split('@')[0] : name.split(' ')[0]; }
function heatColor(value: number) { const alpha = .08 + Math.min(value, 100) / 100 * .72; return `rgba(22, 137, 120, ${alpha})`; }
function segmentColor(index: number) { return ['#f0644f', '#168978', '#5f72ad', '#d99024', '#8064a2', '#8c93a0'][index % 6]; }
function growthClass(value: number | null) { return value === null ? 'neutral-growth' : value >= 0 ? 'positive-growth' : 'negative-growth'; }
function scatterX(value: number, min: number, max: number) { if (max <= min) return 50; const scaled = (Math.log(value) - Math.log(min)) / (Math.log(max) - Math.log(min)); return 8 + scaled * 84; }
function scatterY(value: number) { const clamped = Math.max(-.75, Math.min(1.5, value)); return 8 + ((clamped + .75) / 2.25) * 84; }
function cuisineHeat(value: number, max: number) { const alpha = value <= 0 ? .02 : .08 + Math.sqrt(value / max) * .72; return `rgba(240, 100, 79, ${alpha})`; }
function titleCase(value: string) { return value.replace(/\b\w/g, (letter) => letter.toUpperCase()); }
