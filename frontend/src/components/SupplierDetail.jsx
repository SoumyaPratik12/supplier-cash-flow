import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import ScenarioWorkspace from "./ScenarioWorkspace";

const FACTOR_LABELS = {
  revenue_slope: "Revenue trend",
  avg_days_to_payment: "Average days to pay invoices",
  days_to_payment_trend: "Days-to-payment is worsening",
  outstanding_ratio: "Share of invoices still outstanding",
  overdue_ratio: "Share of invoices overdue",
  on_time_rate: "On-time payment rate",
};

export default function SupplierDetail({ supplier }) {
  if (!supplier) {
    return (
      <div className="supplier-detail empty">
        Select a supplier from the attention queue to inspect its financial risk
        and intervention options.
      </div>
    );
  }

  const chartData = supplier.revenue_history.map((snap) => ({
    period: snap.period,
    revenue: snap.revenue,
  }));

  if (supplier.risk) {
    chartData.push({
      period: "Forecast",
      revenue: null,
      forecast: supplier.risk.forecast_next_period,
    });

    if (chartData.length >= 2) {
      chartData[chartData.length - 2].forecast =
        chartData[chartData.length - 2].revenue;
    }
  }

  return (
    <div className="supplier-detail">
      <div className="supplier-identity">
        <div>
          <p className="eyebrow">Supplier financial profile</p>
          <h2>{supplier.name}</h2>
          <p className="hint">
            {supplier.industry} · Order volume $
            {supplier.order_volume.toLocaleString()}
          </p>
        </div>
      </div>

      {supplier.risk && (
        <>
          <section className="risk-panel decision-section">
            <div className="decision-section-heading">
              <div>
                <p className="eyebrow">01 · Financial risk</p>
                <h3>Current risk assessment</h3>
              </div>

              <div className="risk-summary-badge">
                <span>{supplier.risk.risk_level}</span>
                <strong>{(supplier.risk.score * 100).toFixed(0)}%</strong>
              </div>
            </div>

            <div className="risk-assessment-grid">
              <div className="risk-assessment-card">
                <span>Risk level</span>
                <strong>{supplier.risk.risk_level}</strong>
              </div>

              <div className="risk-assessment-card">
                <span>Risk score</span>
                <strong>{(supplier.risk.score * 100).toFixed(0)}%</strong>
              </div>
            </div>

            <div className="risk-drivers">
              <div className="decision-subheading">
                <span className="eyebrow">Why</span>
                <h4>Key risk drivers</h4>
              </div>

              <ul>
                {supplier.risk.top_factors.map((factor) => (
                  <li key={factor}>{FACTOR_LABELS[factor] || factor}</li>
                ))}
              </ul>
            </div>
          </section>

          {supplier.risk.dependency && (
            <section className="dependency-section decision-section">
              <div className="decision-section-heading">
                <div>
                  <p className="eyebrow">02 · Supplier dependency</p>
                  <h3>How difficult is this supplier to replace?</h3>
                </div>

                <span className="dependency-level">
                  {supplier.risk.dependency.level}
                </span>
              </div>

              <div className="dependency-summary">
                <div>
                  <span>Dependency weight</span>
                  <strong>
                    {(supplier.risk.dependency.weight * 100).toFixed(0)}%
                  </strong>
                </div>

                <div>
                  <span>Replaceability</span>
                  <strong>{supplier.risk.dependency.replaceability}</strong>
                </div>
              </div>
            </section>
          )}

          {supplier.risk.intervention && (
            <section className="intervention-section decision-section">
              <div className="decision-section-heading">
                <div>
                  <p className="eyebrow">03 · Recommended intervention</p>
                  <h3>Action currently suggested by the model</h3>
                </div>

                <span
                  className={`intervention-priority intervention-priority-${supplier.risk.intervention.priority.toLowerCase()}`}
                >
                  {supplier.risk.intervention.priority} priority
                </span>
              </div>

              <div className="intervention-details">
                <div>
                  <span>Action</span>
                  <strong>{supplier.risk.intervention.action}</strong>
                </div>

                <div>
                  <span>Reason</span>
                  <p>{supplier.risk.intervention.reason}</p>
                </div>
              </div>

              <p className="decision-note">
                This is a rule-based intervention suggestion based on the
                current financial-risk and supplier-dependency state.
              </p>
            </section>
          )}
        </>
      )}

      <ScenarioWorkspace supplier={supplier} />

      <section className="revenue-section decision-section">
        <div className="decision-section-heading">
          <div>
            <p className="eyebrow">05 · Financial trend</p>
            <h3>Revenue trend + next-period forecast</h3>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="period" />
            <YAxis />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="revenue"
              stroke="#1565c0"
              name="Actual revenue"
              connectNulls
            />
            <Line
              type="monotone"
              dataKey="forecast"
              stroke="#c62828"
              strokeDasharray="5 5"
              name="Forecast"
              connectNulls
            />
          </LineChart>
        </ResponsiveContainer>
      </section>
    </div>
  );
}
