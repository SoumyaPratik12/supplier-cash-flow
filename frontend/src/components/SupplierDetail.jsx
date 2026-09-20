import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

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
    return <div className="supplier-detail empty">Select a supplier to see the detail view.</div>;
  }

  const chartData = supplier.revenue_history.map((snap) => ({
    period: snap.period,
    revenue: snap.revenue,
  }));
  if (supplier.risk) {
    chartData.push({ period: "Forecast", revenue: null, forecast: supplier.risk.forecast_next_period });
    if (chartData.length >= 2) {
      chartData[chartData.length - 2].forecast = chartData[chartData.length - 2].revenue;
    }
  }

  return (
    <div className="supplier-detail">
      <h2>{supplier.name}</h2>
      <p className="hint">
        {supplier.industry} · Order volume ${supplier.order_volume.toLocaleString()}
      </p>

      {supplier.risk && (
        <div className="risk-panel">
          <div>
            <strong>Risk level:</strong> {supplier.risk.risk_level} (score {supplier.risk.score})
          </div>
          <div>
            <strong>Recommended action:</strong> {supplier.risk.recommended_action}
          </div>

          {supplier.risk.intervention && (
            <div className="intervention-section">
              <strong>Intervention:</strong>

              <div className="intervention-details">
                <div>
                  <span>Action</span>
                  <strong>{supplier.risk.intervention.action}</strong>
                </div>

                <div>
                  <span>Priority</span>
                  <strong>{supplier.risk.intervention.priority}</strong>
                </div>

                <div>
                  <span>Reason</span>
                  <p>{supplier.risk.intervention.reason}</p>
                </div>
              </div>
            </div>
          )}

          <div>
            <strong>Why:</strong>
            <ul>
              {supplier.risk.top_factors.map((f) => (
                <li key={f}>{FACTOR_LABELS[f] || f}</li>
              ))}
            </ul>
          </div>
          {supplier.risk?.dependency && (
            <div className="dependency-section">
              <h3>Supplier dependency</h3>

              <div className="dependency-summary">
                <span className="dependency-level">
                  {supplier.risk.dependency.level}
                </span>

                <span>
                  {(supplier.risk.dependency.weight * 100).toFixed(0)}% dependency weight
                </span>
              </div>

              <p>{supplier.risk.dependency.replaceability}</p>
            </div>
          )}
        </div>
      )}

      <h3>Revenue trend + next-period forecast</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="revenue" stroke="#1565c0" name="Actual revenue" connectNulls />
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
    </div>
  );
}
