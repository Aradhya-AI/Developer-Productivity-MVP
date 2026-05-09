import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "https://developer-productivity-api.onrender.com";

function App() {
  const [dashboard, setDashboard] = useState(null);
  const [developerId, setDeveloperId] = useState("");
  const [month, setMonth] = useState("");
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    const params = new URLSearchParams();
    if (developerId) params.set("developer_id", developerId);
    if (month) params.set("month", month);

    setStatus("loading");
    fetch(`${API_BASE_URL}/metrics?${params.toString()}`)
      .then((response) => {
        if (!response.ok) throw new Error("Metrics API failed");
        return response.json();
      })
      .then((data) => {
        setDashboard(data);
        setDeveloperId(data.selected.developer_id);
        setMonth(data.selected.month);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, [developerId, month]);

  const maxTrend = useMemo(() => {
    if (!dashboard?.trend?.length) return 1;
    return Math.max(
      1,
      ...dashboard.trend.flatMap((item) => [
        item.lead_time_days,
        item.cycle_time_days,
        item.deployments,
        item.merged_prs,
      ])
    );
  }, [dashboard]);

  if (status === "error") {
    return (
      <main className="page">
        <section className="empty-state">
          <h1>Developer Productivity MVP</h1>
          <p>Could not load metrics. Start the Flask API on port 5000 and refresh.</p>
        </section>
      </main>
    );
  }

  if (!dashboard) {
    return (
      <main className="page">
        <section className="empty-state">
          <h1>Developer Productivity MVP</h1>
          <p>Loading dashboard...</p>
        </section>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="topbar">
        <div>
          <p className="eyebrow">Individual Contributor Dashboard</p>
          <h1>{dashboard.developer.developer_name}</h1>
          <p className="subtle">
            {dashboard.developer.level} · {dashboard.developer.team_name} ·{" "}
            {dashboard.developer.service_type}
          </p>
        </div>

        <div className="filters">
          <label>
            Developer
            <select value={developerId} onChange={(event) => setDeveloperId(event.target.value)}>
              {dashboard.options.developers.map((developer) => (
                <option key={developer.developer_id} value={developer.developer_id}>
                  {developer.developer_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Month
            <select value={month} onChange={(event) => setMonth(event.target.value)}>
              {dashboard.options.months.map((availableMonth) => (
                <option key={availableMonth} value={availableMonth}>
                  {availableMonth}
                </option>
              ))}
            </select>
          </label>
        </div>
      </header>

      <section className="metric-grid" aria-label="Developer productivity metrics">
        {dashboard.metrics.map((metric) => (
          <MetricCard key={metric.key} metric={metric} />
        ))}
      </section>

      <section className="dashboard-grid">
        <section className="panel">
          <div className="section-heading">
            <p className="eyebrow">Trend</p>
            <h2>Month-over-month flow</h2>
          </div>
          <div className="chart">
            {dashboard.trend.map((item) => (
              <div className="chart-row" key={item.month}>
                <span>{item.month}</span>
                <Bar label="Lead" value={item.lead_time_days} max={maxTrend} tone="amber" />
                <Bar label="Cycle" value={item.cycle_time_days} max={maxTrend} tone="blue" />
                <Bar label="PRs" value={item.merged_prs} max={maxTrend} tone="green" />
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="section-heading">
            <p className="eyebrow">What is happening</p>
            <h2>Interpretation</h2>
          </div>
          <ul className="insight-list">
            {dashboard.insights.map((insight) => (
              <li key={insight}>{insight}</li>
            ))}
          </ul>
        </section>

        <section className="panel actions-panel">
          <div className="section-heading">
            <p className="eyebrow">What to do</p>
            <h2>Recommended next steps</h2>
          </div>
          <div className="action-list">
            {dashboard.actions.map((action) => (
              <article className="action-item" key={action.title}>
                <h3>{action.title}</h3>
                <p>{action.detail}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="panel compact">
          <div className="section-heading">
            <p className="eyebrow">Source counts</p>
            <h2>Audit trail</h2>
          </div>
          <dl className="counts">
            <div>
              <dt>Completed issues</dt>
              <dd>{dashboard.raw_counts.completed_issues}</dd>
            </div>
            <div>
              <dt>Escaped bugs</dt>
              <dd>{dashboard.raw_counts.bugs}</dd>
            </div>
            <div>
              <dt>Prod deployments</dt>
              <dd>{dashboard.raw_counts.successful_prod_deployments}</dd>
            </div>
            <div>
              <dt>Merged PRs</dt>
              <dd>{dashboard.raw_counts.merged_prs}</dd>
            </div>
          </dl>
        </section>
      </section>
    </main>
  );
}

function MetricCard({ metric }) {
  const isBugRate = metric.key === "bug_rate";
  const displayValue = isBugRate && metric.suffix === "%" ? metric.value / 100 : metric.value;
  const displaySuffix = isBugRate ? "ratio" : metric.suffix;
  const changeText =
    metric.change === null
      ? "No previous month"
      : `${metric.change > 0 ? "+" : ""}${
          isBugRate && metric.suffix === "%" ? metric.change / 100 : metric.change
        } vs previous month`;

  return (
    <article className={`metric-card ${metric.signal}`}>
      <div>
        <p className="metric-label">{metric.label}</p>
        <p className="metric-definition">{metric.definition}</p>
      </div>
      <div>
        <p className="metric-value">
          {displayValue}
          <span>{displaySuffix}</span>
        </p>
        <p className="metric-change">{changeText}</p>
      </div>
    </article>
  );
}

function Bar({ label, value, max, tone }) {
  const width = `${Math.max(6, (value / max) * 100)}%`;
  return (
    <div className="bar-line">
      <small>{label}</small>
      <div className="bar-track" aria-label={`${label}: ${value}`}>
        <div className={`bar-fill ${tone}`} style={{ width }} />
      </div>
      <strong>{value}</strong>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
