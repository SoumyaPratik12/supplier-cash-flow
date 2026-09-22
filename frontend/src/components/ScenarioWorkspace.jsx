import { useEffect, useState } from "react";

import { runSupplierScenario } from "../api";

export default function ScenarioWorkspace({ supplier }) {
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

    const currentDependency =
      supplier.risk?.dependency?.weight ?? supplier.dependency_weight;
    setScenario("early_payment");
    setPaymentDaysReduction("20");
    setTargetDependency(String(Math.max(0, currentDependency - 0.1)));
    setScenarioResult(null);
    setScenarioError("");
  }, [supplier]);

  if (!supplier) {
    return null;
  }

  const currentDependency =
    supplier.risk?.dependency?.weight ?? supplier.dependency_weight;

  async function handleScenarioSubmit(event) {
    event.preventDefault();
    setScenarioError("");

    const reduction = Number(paymentDaysReduction);
    const dependency = Number(targetDependency);

    if (
      scenario === "early_payment" &&
      (!Number.isFinite(reduction) || reduction <= 0)
    ) {
      setScenarioError("Payment-day reduction must be greater than 0.");
      return;
    }

    if (
      scenario === "reduce_dependency" &&
      (!Number.isFinite(dependency) ||
        dependency < 0 ||
        dependency >= currentDependency)
    ) {
      setScenarioError(
        "Target dependency must be at least 0% and lower than the current dependency."
      );
      return;
    }

    const payload =
      scenario === "early_payment"
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

  return (
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
          <select
            value={scenario}
            onChange={(event) => setScenario(event.target.value)}
          >
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
              onChange={(event) =>
                setPaymentDaysReduction(event.target.value)
              }
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
              onChange={(event) =>
                setTargetDependency(String(Number(event.target.value) / 100))
              }
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
  );
}
