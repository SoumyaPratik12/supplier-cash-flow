import React from "react";

const RISK_LEVELS = ["High", "Medium", "Low"];

function countBy(items, key, value) {
  return items.filter((item) => item[key] === value).length;
}

export default function PortfolioDashboard({ suppliers }) {
  const totalSuppliers = suppliers.length;

  const riskCounts = Object.fromEntries(
    RISK_LEVELS.map((level) => [
      level,
      countBy(suppliers, "risk_level", level),
    ])
  );

  const actionCounts = suppliers.reduce((counts, supplier) => {
    const action = supplier.recommended_action || "Monitor";
    counts[action] = (counts[action] || 0) + 1;
    return counts;
  }, {});

  const riskPercent = (count) =>
    totalSuppliers === 0
      ? 0
      : Math.round((count / totalSuppliers) * 100);

  return (
    <section className="portfolio-dashboard">
      <div className="portfolio-header">
        <div>
          <p className="eyebrow">Portfolio overview</p>
          <h2>Supplier Risk Intelligence</h2>
          <p className="portfolio-description">
            Identify suppliers that require attention and understand the
            intervention currently suggested by the risk model.
          </p>
        </div>
      </div>

      <div className="portfolio-metrics">
        <div className="portfolio-metric">
          <span>Total suppliers</span>
          <strong>{totalSuppliers}</strong>
        </div>

        <div className="portfolio-metric">
          <span>High risk</span>
          <strong>{riskCounts.High}</strong>
        </div>

        <div className="portfolio-metric">
          <span>Medium risk</span>
          <strong>{riskCounts.Medium}</strong>
        </div>

        <div className="portfolio-metric">
          <span>Low risk</span>
          <strong>{riskCounts.Low}</strong>
        </div>
      </div>

      <div className="portfolio-grid">
        <div className="portfolio-card">
          <div className="portfolio-card-header">
            <h3>Risk distribution</h3>
            <span>{totalSuppliers} suppliers</span>
          </div>

          <div className="risk-distribution">
            {RISK_LEVELS.map((level) => (
              <div className="risk-distribution-row" key={level}>
                <div className="risk-distribution-label">
                  <span>{level}</span>
                  <strong>{riskCounts[level]}</strong>
                </div>

                <div className="risk-bar-track">
                  <div
                    className={`risk-bar risk-bar-${level.toLowerCase()}`}
                    style={{
                      width: `${riskPercent(riskCounts[level])}%`,
                    }}
                  />
                </div>

                <span className="risk-distribution-percent">
                  {riskPercent(riskCounts[level])}%
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="portfolio-card">
          <div className="portfolio-card-header">
            <h3>Intervention overview</h3>
            <span>Current recommendations</span>
          </div>

          <div className="intervention-summary">
            <div>
              <span>Offer early payment</span>
              <strong>{actionCounts["Offer early payment"] || 0}</strong>
            </div>

            <div>
              <span>Reduce dependency</span>
              <strong>
                {actionCounts["Reduce dependency on this supplier"] || 0}
              </strong>
            </div>

            <div>
              <span>Monitor</span>
              <strong>{actionCounts.Monitor || 0}</strong>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
