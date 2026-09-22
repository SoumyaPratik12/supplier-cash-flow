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
      <div className="portfolio-dashboard-header">
        <div>
          <p className="eyebrow">Portfolio overview</p>
          <h2>Supplier risk snapshot</h2>
          <p>
            A current view of financial risk and recommended supplier
            interventions across the portfolio.
          </p>
        </div>

        <span className="portfolio-dashboard-count">
          {totalSuppliers} suppliers
        </span>
      </div>

      <div className="portfolio-metrics">
        <div className="portfolio-metric portfolio-metric-total">
          <span>Total suppliers</span>
          <strong>{totalSuppliers}</strong>
          <small>Supplier network</small>
        </div>

        <div className="portfolio-metric portfolio-metric-high">
          <span>High risk</span>
          <strong>{riskCounts.High}</strong>
          <small>Requires attention</small>
        </div>

        <div className="portfolio-metric portfolio-metric-medium">
          <span>Medium risk</span>
          <strong>{riskCounts.Medium}</strong>
          <small>Requires monitoring</small>
        </div>

        <div className="portfolio-metric portfolio-metric-low">
          <span>Low risk</span>
          <strong>{riskCounts.Low}</strong>
          <small>Currently lower risk</small>
        </div>
      </div>

      <div className="portfolio-grid">
        <div className="portfolio-card">
          <div className="portfolio-card-header">
            <div>
              <p className="portfolio-card-kicker">Portfolio health</p>
              <h3>Risk distribution</h3>
            </div>

            <span>{totalSuppliers} suppliers</span>
          </div>

          <div className="risk-distribution">
            {RISK_LEVELS.map((level) => (
              <div className="risk-distribution-row" key={level}>
                <div className="risk-distribution-label">
                  <span
                    className={`risk-indicator risk-indicator-${level.toLowerCase()}`}
                  />

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
            <div>
              <p className="portfolio-card-kicker">Decision support</p>
              <h3>Intervention overview</h3>
            </div>

            <span>Current recommendations</span>
          </div>

          <div className="intervention-summary">
            <div className="intervention-summary-item">
              <span className="intervention-summary-icon payment">↗</span>

              <div>
                <span>Offer early payment</span>
                <small>High-risk suppliers with higher dependency</small>
              </div>

              <strong>{actionCounts["Offer early payment"] || 0}</strong>
            </div>

            <div className="intervention-summary-item">
              <span className="intervention-summary-icon dependency">↔</span>

              <div>
                <span>Reduce dependency</span>
                <small>High-risk suppliers with lower dependency</small>
              </div>

              <strong>
                {actionCounts["Reduce dependency on this supplier"] || 0}
              </strong>
            </div>

            <div className="intervention-summary-item">
              <span className="intervention-summary-icon monitor">•</span>

              <div>
                <span>Monitor</span>
                <small>Suppliers without a high-risk intervention</small>
              </div>

              <strong>{actionCounts.Monitor || 0}</strong>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
