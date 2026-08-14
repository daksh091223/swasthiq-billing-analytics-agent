import { useMemo, useState } from "react";
import Sidebar from "./components/Sidebar";
import MetricCard from "./components/MetricCard";
import BarChart from "./components/BarChart";
import RankingTable from "./components/RankingTable";
import { analyzeBilling, generateNarrative } from "./api";

const DEMO_ROWS = [
  {
    clinic_id: "C1",
    visit_id: "V-DEMO-001",
    timestamp: "2026-07-27T13:20:00Z",
    doctor_id: "D1",
    line_items: [
      { drug_name: "OMEPRAZOLE", qty: 2, unit_price_paise: 4000 },
      { drug_name: "PARACETAMOL", qty: 2, unit_price_paise: 1000 }
    ],
    payment_mode: "upi",
    amount_paid_paise: 10000,
    discount_paise: 0,
    is_refund: false
  },
  {
    clinic_id: "C1",
    visit_id: "V-DEMO-002",
    timestamp: "2026-07-27T16:20:00Z",
    doctor_id: "D2",
    line_items: [
      { drug_name: "METFORMIN", qty: 2, unit_price_paise: 3000 }
    ],
    payment_mode: "cash",
    amount_paid_paise: 5000,
    discount_paise: 1000,
    is_refund: false
  }
];

function money(paise) {
  return `₹${((paise || 0) / 100).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function initialReport() {
  return {
    status: "complete",
    processed_rows: 0,
    rejected_rows: [],
    totals: {
      billed_paise: 0,
      collected_paise: 0,
      outstanding_paise: 0,
      refunds_paise: 0,
    },
    reconciliation: {
      cash: { billed_paise: 0, collected_paise: 0, outstanding_paise: 0, refunds_paise: 0 },
      card: { billed_paise: 0, collected_paise: 0, outstanding_paise: 0, refunds_paise: 0 },
      upi: { billed_paise: 0, collected_paise: 0, outstanding_paise: 0, refunds_paise: 0 },
    },
    analytics: {
      revenue_by_hour: [],
      peak_hour: null,
      top_medicines_by_quantity: [],
      top_medicines_by_revenue: [],
    },
  };
}

export default function App() {
  const [active, setActive] = useState("dashboard");
  const [report, setReport] = useState(initialReport);
  const [rowsText, setRowsText] = useState(JSON.stringify(DEMO_ROWS, null, 2));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [source, setSource] = useState("Demo data");
  const [narrative, setNarrative] = useState(null);
  const [narrativeLoading, setNarrativeLoading] = useState(false);

  async function runAnalysis() {
    setLoading(true);
    setError("");

    try {
      const rows = JSON.parse(rowsText);

      if (!Array.isArray(rows)) {
        throw new Error("Input must be a JSON array of billing records.");
      }

      const result = await analyzeBilling(rows);
      setReport(result);
      setSource("Live API");
    } catch (err) {
      setError(err.message || "Unable to analyze data.");
    } finally {
      setLoading(false);
    }
  }

  function loadDemo() {
    setRowsText(JSON.stringify(DEMO_ROWS, null, 2));
    setError("");
  }

  async function runNarrative() {
    setNarrativeLoading(true);
    setError("");

    try {
      const result = await generateNarrative(report);
      setNarrative(result);
    } catch (err) {
      setError(err.message || "Unable to generate narrative.");
    } finally {
      setNarrativeLoading(false);
    }
  }

  const title = {
    dashboard: "EOD Reconciliation",
    analytics: "Billing Analytics",
    narrative: "AI Narrative Summary",
  }[active];

  return (
    <div className="app-shell">
      <Sidebar active={active} onChange={setActive} />

      <main className="main">
        <header className="topbar">
          <div>
            <span className="eyebrow">End-of-day billing</span>
            <h1>{title}</h1>
          </div>

          <div className="topbar-actions">
            <span className={`report-status ${report.status}`}>
              <span />
              {report.status === "partial" ? "Partial report" : "Complete report"}
            </span>
            <span className="source-badge">{source}</span>
          </div>
        </header>

        {error && <div className="error-banner">{error}</div>}

        {active === "dashboard" && (
          <Dashboard
            report={report}
            rowsText={rowsText}
            setRowsText={setRowsText}
            runAnalysis={runAnalysis}
            loadDemo={loadDemo}
            loading={loading}
          />
        )}

        {active === "analytics" && <Analytics report={report} />}

        {active === "narrative" && (
          <Narrative
            report={report}
            narrative={narrative}
            loading={narrativeLoading}
            onGenerate={runNarrative}
          />
        )}
      </main>
    </div>
  );
}

function Dashboard({
  report,
  rowsText,
  setRowsText,
  runAnalysis,
  loadDemo,
  loading,
}) {
  const totals = report.totals;

  return (
    <>
      <section className="metric-grid">
        <MetricCard label="Total Billed" value={money(totals.billed_paise)} />
        <MetricCard label="Total Collected" value={money(totals.collected_paise)} />
        <MetricCard
          label="Outstanding"
          value={money(totals.outstanding_paise)}
          tone={totals.outstanding_paise ? "warning" : ""}
        />
        <MetricCard label="Refunds" value={money(totals.refunds_paise)} />
      </section>

      <section className="workspace-grid">
        <div className="panel input-panel">
          <div className="panel-header">
            <div>
              <h3>Billing log</h3>
              <span>Paste the day's JSON records</span>
            </div>
            <button className="secondary-button" onClick={loadDemo}>
              Load demo
            </button>
          </div>

          <textarea
            value={rowsText}
            onChange={(e) => setRowsText(e.target.value)}
            spellCheck="false"
          />

          <button className="primary-button" onClick={runAnalysis} disabled={loading}>
            {loading ? "Analyzing..." : "Run EOD analysis"}
          </button>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>Reconciliation</h3>
              <span>By payment mode</span>
            </div>
          </div>

          <div className="reconciliation-table">
            <div className="table-head">
              <span>Mode</span>
              <span>Billed</span>
              <span>Collected</span>
              <span>Outstanding</span>
              <span>Refunds</span>
            </div>

            {["cash", "card", "upi"].map((mode) => {
              const item = report.reconciliation[mode];

              return (
                <div className="table-row" key={mode}>
                  <strong>{mode.toUpperCase()}</strong>
                  <span>{money(item.billed_paise)}</span>
                  <span>{money(item.collected_paise)}</span>
                  <span>{money(item.outstanding_paise)}</span>
                  <span>{money(item.refunds_paise)}</span>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="panel rejection-panel">
        <div className="panel-header">
          <div>
            <h3>Data quality</h3>
            <span>{report.processed_rows} valid rows processed</span>
          </div>
          <strong className={report.rejected_rows.length ? "warning-text" : "success-text"}>
            {report.rejected_rows.length} rejected
          </strong>
        </div>

        {report.rejected_rows.length === 0 ? (
          <div className="success-message">All billing rows passed validation.</div>
        ) : (
          <div className="rejection-list">
            {report.rejected_rows.map((row) => (
              <div className="rejection-row" key={row.row_number}>
                <strong>Row {row.row_number}</strong>
                <span>{row.visit_id || "Unknown visit"}</span>
                <span>{row.field}</span>
                <span>{row.message}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </>
  );
}

function Analytics({ report }) {
  return (
    <>
      <section className="metric-grid analytics-metrics">
        <MetricCard
          label="Peak Hour"
          value={
            report.analytics.peak_hour === null
              ? "—"
              : `${String(report.analytics.peak_hour).padStart(2, "0")}:00`
          }
        />
        <MetricCard label="Processed Rows" value={report.processed_rows} />
        <MetricCard label="Rejected Rows" value={report.rejected_rows.length} />
        <MetricCard label="Revenue Events" value={report.analytics.revenue_by_hour.length} />
      </section>

      <section className="panel chart-panel">
        <div className="panel-header">
          <div>
            <h3>Revenue by hour</h3>
            <span>UTC hour-of-day</span>
          </div>
          {report.analytics.peak_hour !== null && (
            <strong>
              Peak: {String(report.analytics.peak_hour).padStart(2, "0")}:00
            </strong>
          )}
        </div>
        <BarChart data={report.analytics.revenue_by_hour} />
      </section>

      <section className="two-column">
        <RankingTable
          title="Top medicines by quantity"
          valueLabel="Units"
          rows={report.analytics.top_medicines_by_quantity}
          formatValue={(row) => row.quantity}
        />

        <RankingTable
          title="Top medicines by revenue"
          valueLabel="Gross revenue"
          rows={report.analytics.top_medicines_by_revenue}
          formatValue={(row) => money(row.revenue_paise)}
        />
      </section>
    </>
  );
}

function Narrative({ report, narrative, loading, onGenerate }) {
  return (
    <section className="narrative-layout">
      <div className="panel narrative-card">
        <span className="eyebrow">AI-generated layer</span>
        <h2>
          {narrative?.title || "Turn the verified EOD report into a concise operator summary."}
        </h2>

        {!narrative ? (
          <>
            <p>
              The model receives only the deterministic EOD report. It cannot
              calculate the billing figures and it cannot write raw numeric
              values into the narrative.
            </p>

            <button className="primary-button narrative-button" onClick={onGenerate} disabled={loading}>
              {loading ? "Generating..." : "Generate AI narrative"}
            </button>
          </>
        ) : (
          <>
            {narrative.sections.map((section) => (
              <div className="narrative-section" key={section.heading}>
                <h3>{section.heading}</h3>
                <p>{section.text}</p>
              </div>
            ))}
          </>
        )}

        {narrative && (
          <div className="grounding-note">
            Every displayed number comes from the deterministic report and is
            linked to the traced figure source shown alongside it.
          </div>
        )}
      </div>

      <div className="panel">
        <div className="panel-header">
          <div>
            <h3>Traced Figures</h3>
            <span>
              {narrative
                ? "Figures used by the generated narrative"
                : "Deterministic source fields"}
            </span>
          </div>
          <span className="verified-badge">Verified source</span>
        </div>

        <div className="trace-list">
          {(narrative?.traced_figures || [
            ["Total billed", "totals.billed_paise", money(report.totals.billed_paise)],
            ["Total collected", "totals.collected_paise", money(report.totals.collected_paise)],
            ["Outstanding", "totals.outstanding_paise", money(report.totals.outstanding_paise)],
            ["Refunds", "totals.refunds_paise", money(report.totals.refunds_paise)],
            [
              "Peak hour",
              "analytics.peak_hour",
              report.analytics.peak_hour === null
                ? "—"
                : `${String(report.analytics.peak_hour).padStart(2, "0")}:00 UTC`,
            ],
          ]).map((item) => {
            const isTrace = !Array.isArray(item);

            const id = isTrace ? item.id : item[1];
            const label = isTrace ? item.label : item[0];
            const source = isTrace ? item.source : item[1];
            const value = isTrace ? item.value : item[2];

            return (
              <div className="trace-row" key={id}>
                <div>
                  <strong>{label}</strong>
                  <code>{source}</code>
                </div>
                <span>{value}</span>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
