import React from "react";

function formatPercent(value) {
  return `${(value * 100).toFixed(0)}%`;
}

function riskClass(riskLevel) {
  return `priority-risk priority-risk-${riskLevel.toLowerCase()}`;
}

function actionClass(action) {
  if (action === "Offer early payment") {
    return "priority-action priority-action-payment";
  }

  if (action === "Reduce dependency on this supplier") {
    return "priority-action priority-action-dependency";
  }

  return "priority-action priority-action-monitor";
}

export default function PrioritySupplierQueue({ suppliers, onSelectSupplier }) {
  if (suppliers.length === 0) {
    return (
      <section className="priority-queue">
        <div className="priority-queue-header">
          <div>
            <p className="eyebrow">Decision queue</p>
            <h2>Supplier attention queue</h2>
          </div>
        </div>

        <div className="priority-empty">No suppliers are currently available.</div>
      </section>
    );
  }

  return (
    <section className="priority-queue">
      <div className="priority-queue-header">
        <div>
          <p className="eyebrow">Decision queue</p>
          <h2>Supplier attention queue</h2>
          <p className="priority-queue-description">
            Suppliers are shown in the ranking returned by the risk engine.
            Select a supplier to inspect its financial risk, dependency,
            intervention, and scenario analysis.
          </p>
        </div>

        <span className="priority-queue-count">{suppliers.length} suppliers</span>
      </div>

      <div className="priority-table-wrapper">
        <table className="priority-table">
          <thead>
            <tr>
              <th>Supplier</th>
              <th>Industry</th>
              <th>Risk</th>
              <th>Score</th>
              <th>Dependency</th>
              <th>Intervention</th>
            </tr>
          </thead>

          <tbody>
            {suppliers.map((supplier) => (
              <tr
                key={supplier.id}
                className="priority-row"
                onClick={() => onSelectSupplier(supplier.id)}
              >
                <td>
                  <button
                    type="button"
                    className="priority-supplier-button"
                    onClick={(event) => {
                      event.stopPropagation();
                      onSelectSupplier(supplier.id);
                    }}
                  >
                    {supplier.name}
                  </button>
                </td>

                <td>{supplier.industry}</td>

                <td>
                  <span className={riskClass(supplier.risk_level)}>
                    {supplier.risk_level}
                  </span>
                </td>

                <td>{formatPercent(supplier.score)}</td>
                <td>{formatPercent(supplier.dependency_weight)}</td>

                <td>
                  <span className={actionClass(supplier.recommended_action)}>
                    {supplier.recommended_action}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
