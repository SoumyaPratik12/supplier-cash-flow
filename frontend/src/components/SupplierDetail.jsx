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
    return (
      <div className="supplier-detail empty">
        Select a supplier from the attention queue to inspect its financial risk
        and intervention options.
      </div>
    );
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

          {supplier.risk?.dependency && (
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

      <section
        className="scenario-workspace decision-section"
        aria-labelledby="scenario-title"
      >
        <div className="scenario-heading">
          <div>
            <p className="eyebrow">04 · Scenario analysis</p>
            <h3 id="scenario-title">What-if simulation</h3>
          </div>

          <p>
            Explore how a change in supplier payment behavior or dependency
            could affect the current risk model output.
          </p>
        </div>

        <div className="scenario-disclaimer">
          What-if simulation — not a prediction of actual future outcomes.
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

        {scenarioError && (
          <p className="scenario-error" role="alert">
            {scenarioError}
          </p>
        )}

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
