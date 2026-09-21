import { useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { runSupplierScenario } from "../api";

const FACTOR_LABELS = {
  revenue_slope: "Revenue trend",
  avg_days_to_payment: "Average days to pay invoices",
  days_to_payment_trend: "Days-to-payment is worsening",
  outstanding_ratio: "Share of invoices still outstanding",
  overdue_ratio: "Share of invoices overdue",
  on_time_rate: "On-time payment rate",
};

export default function SupplierDetail({ supplier }) {
  const [scenario, setScenario] = useState("early_payment");
  const [paymentDaysReduction, setPaymentDaysReduction] = useState("20");
  const [targetDependency, setTargetDependency] = useState("0");
  const [scenarioResult, setScenarioResult] = useState(null);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [scenarioError, setScenarioError] = useState("");

  useEffect(() => {
    if (!supplier) {
      return;
    }

    const currentDependency = supplier.risk?.dependency?.weight ?? supplier.dependency_weight;
    setScenario("early_payment");
    setPaymentDaysReduction("20");
    setTargetDependency(String(Math.max(0, currentDependency - 0.1)));
    setScenarioResult(null);
    setScenarioError("");
  }, [supplier]);

  if (!supplier) {
    return <div className="supplier-detail empty">Select a supplier to see the detail view.</div>;
  }

  const currentDependency = supplier.risk?.dependency?.weight ?? supplier.dependency_weight;

  async function handleScenarioSubmit(event) {
    event.preventDefault();
    setScenarioError("");

    const reduction = Number(paymentDaysReduction);
    const dependency = Number(targetDependency);

    if (scenario === "early_payment" && (!Number.isFinite(reduction) || reduction <= 0)) {
      setScenarioError("Payment-day reduction must be greater than 0.");
      return;
    }

    if (
      scenario === "reduce_dependency" &&
      (!Number.isFinite(dependency) || dependency < 0 || dependency >= currentDependency)
    ) {
      setScenarioError("Target dependency must be at least 0% and lower than the current dependency.");
      return;
    }

    const payload = scenario === "early_payment"
      ? { scenario, payment_days_reduction: reduction }
      : { scenario, dependency_weight: dependency };

    setScenarioLoading(true);
    try {
      const result = await runSupplierScenario(supplier.id, payload);
      setScenarioResult(result);
    } catch (error) {
      setScenarioError(error.message || "Unable to run scenario.");
    } finally {
      setScenarioLoading(false);
    }
  }

  function renderScenarioState(state) {
    return (
      <div className="scenario-state">
        <div>
          <span>Risk level</span>
          <strong>{state.risk_level}</strong>
        </div>
        <div>
          <span>Risk score</span>
          <strong>{(state.score * 100).toFixed(0)}%</strong>
        </div>
        <div>
          <span>Dependency</span>
          <strong>{(state.dependency.weight * 100).toFixed(0)}%</strong>
        </div>
        <div>
          <span>Replaceability</span>
          <strong>{state.dependency.replaceability}</strong>
        </div>
        <div>
          <span>Intervention</span>
          <strong>{state.intervention.action}</strong>
        </div>
        <div>
          <span>Priority</span>
          <strong>{state.intervention.priority}</strong>
        </div>
        <div>
          <span>Why</span>
          <p>{state.intervention.reason}</p>
        </div>
      </div>
    );
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

      <section className="scenario-workspace" aria-labelledby="scenario-title">
        <div className="scenario-heading">
          <h3 id="scenario-title">What-if simulation</h3>
          <p>
            Explore how a change in supplier payment behavior or dependency could affect the current risk model output. This is a simulated scenario, not a prediction of actual future outcomes.
          </p>
        </div>

        <form className="scenario-form" onSubmit={handleScenarioSubmit}>
          <label>
            Scenario
            <select value={scenario} onChange={(event) => setScenario(event.target.value)}>
              <option value="early_payment">Early payment</option>
              <option value="reduce_dependency">Reduce dependency</option>
            </select>
          </label>

          {scenario === "early_payment" ? (
            <label>
              Payment days reduction
              <input
                type="number"
                min="0.1"
                step="0.1"
                value={paymentDaysReduction}
                onChange={(event) => setPaymentDaysReduction(event.target.value)}
              />
            </label>
          ) : (
            <label>
              Target dependency ({(currentDependency * 100).toFixed(0)}% current)
              <input
                type="number"
                min="0"
                max={Math.max(0, currentDependency * 100 - 0.1)}
                step="0.1"
                value={(Number(targetDependency) * 100).toString()}
                onChange={(event) => setTargetDependency(String(Number(event.target.value) / 100))}
              />
            </label>
          )}

          <button type="submit" disabled={scenarioLoading}>
            {scenarioLoading ? "Simulating..." : "Simulate scenario"}
          </button>
        </form>

        {scenarioError && <p className="scenario-error">{scenarioError}</p>}

        {scenarioResult && (
          <div className="scenario-result">
            <div className="scenario-result-heading">
              <h4>Baseline vs simulated</h4>
              <span>{scenarioResult.scenario}</span>
            </div>
            <div className="scenario-columns">
              <div>
                <h5>Baseline</h5>
                {renderScenarioState(scenarioResult.baseline)}
              </div>
              <div>
                <h5>Simulated</h5>
                {renderScenarioState(scenarioResult.simulated)}
              </div>
            </div>
          </div>
        )}
      </section>

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
