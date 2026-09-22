import { useEffect, useState } from "react";
import { api } from "./api";
import PortfolioDashboard from "./components/PortfolioDashboard";
import PrioritySupplierQueue from "./components/PrioritySupplierQueue";
import SupplierList from "./components/SupplierList.jsx";
import SupplierDetail from "./components/SupplierDetail.jsx";

const NAV_ITEMS = [
  { id: "overview", label: "Overview" },
  { id: "suppliers", label: "Suppliers" },
  { id: "risk", label: "Risk Intelligence" },
  { id: "scenarios", label: "Scenarios" },
];

export default function App() {
  const [suppliers, setSuppliers] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [supplierSearch, setSupplierSearch] = useState("");
  const [supplierRiskFilter, setSupplierRiskFilter] = useState("All");
  const [supplierActionFilter, setSupplierActionFilter] = useState("All");
  const [supplierLoading, setSupplierLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeNav, setActiveNav] = useState("overview");

  useEffect(() => {
    api
      .listSuppliers()
      .then((data) => {
        setSuppliers(data);
        if (data.length > 0) {
          setSelectedId(data[0].id);
        }
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (selectedId == null) return;

    setSupplierLoading(true);
    setError(null);

    api
      .getSupplier(selectedId)
      .then(setSelectedSupplier)
      .catch((err) => {
        setSelectedSupplier(null);
        setError(err.message);
      })
      .finally(() => setSupplierLoading(false));
  }, [selectedId]);

  const selectedSummary = suppliers.find(
    (supplier) => supplier.id === selectedId
  );

  function handleNavigation(itemId) {
    setActiveNav(itemId);

    if (itemId === "suppliers") {
      document
        .getElementById("suppliers-page")
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    if (itemId === "overview") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  const filteredSuppliers = suppliers.filter((supplier) => {
    const query = supplierSearch.trim().toLowerCase();

    const matchesSearch =
      !query ||
      supplier.name?.toLowerCase().includes(query) ||
      supplier.industry?.toLowerCase().includes(query);

    const matchesRisk =
      supplierRiskFilter === "All" ||
      supplier.risk_level === supplierRiskFilter;

    const matchesAction =
      supplierActionFilter === "All" ||
      supplier.recommended_action === supplierActionFilter;

    return matchesSearch && matchesRisk && matchesAction;
  });

  return (
    <div className="saas-app">
      <header className="saas-topbar">
        <div className="saas-brand">
          <div className="saas-brand-mark">S</div>
          <div>
            <strong>SupplierIQ</strong>
            <span>Supplier Financial Intelligence</span>
          </div>
        </div>

        <div className="saas-topbar-actions">
          <button
            type="button"
            className="saas-search-button"
            onClick={() =>
              document
                .getElementById("supplier-workspace")
                ?.scrollIntoView({ behavior: "smooth", block: "start" })
            }
          >
            <span>⌕</span>
            <span>Search suppliers</span>
            <kbd>⌘ K</kbd>
          </button>

          <div className="saas-workspace-menu">
            <div className="saas-avatar">SP</div>
            <div className="saas-workspace-info">
              <strong>Demo Workspace</strong>
              <span>Procurement</span>
            </div>
            <span className="saas-chevron">⌄</span>
          </div>
        </div>
      </header>

      <div className="saas-body">
        <aside className="saas-sidebar">
          <div className="saas-sidebar-section">
            <span className="saas-sidebar-label">Workspace</span>
            <nav aria-label="Main navigation">
              {NAV_ITEMS.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={`saas-nav-item ${
                    activeNav === item.id ? "active" : ""
                  }`}
                  onClick={() => handleNavigation(item.id)}
                >
                  <span className="saas-nav-icon">
                    {item.id === "overview" && "▦"}
                    {item.id === "suppliers" && "◫"}
                    {item.id === "risk" && "◒"}
                    {item.id === "scenarios" && "◇"}
                  </span>
                  <span>{item.label}</span>
                </button>
              ))}
            </nav>
          </div>

          <div className="saas-sidebar-bottom">
            <div className="saas-sidebar-section">
              <span className="saas-sidebar-label">System</span>
              <button type="button" className="saas-nav-item">
                <span className="saas-nav-icon">⚙</span>
                <span>Settings</span>
              </button>
            </div>

            <div className="saas-sidebar-footer">
              <span className="saas-status-dot" />
              <div>
                <strong>System operational</strong>
                <span>Risk engine online</span>
              </div>
            </div>
          </div>
        </aside>

        <main className="saas-content">
          {error && (
            <div className="error" role="alert">
              Couldn't reach the API at the configured URL: {error}
            </div>
          )}

          {activeNav === "risk" ? (
            <main className="saas-main">
              <section className="page-header">
                <div>
                  <p className="eyebrow">Network intelligence</p>
                  <h1>Risk Intelligence</h1>
                  <p className="page-description">
                    Understand financial risk across your supplier network.
                  </p>
                </div>
              </section>

              <PortfolioDashboard suppliers={suppliers} />
            </main>
          ) : activeNav === "scenarios" ? (
            <main className="saas-main scenarios-page">
              <section className="page-header">
                <div>
                  <p className="eyebrow">Scenario analysis</p>
                  <h1>Scenarios</h1>
                  <p className="page-description">
                    Test supplier interventions before taking action.
                  </p>
                </div>
              </section>

              <section className="scenario-page-selector">
                <label htmlFor="scenario-supplier">Supplier</label>
                <select
                  id="scenario-supplier"
                  value={selectedId ?? ""}
                  onChange={(event) => setSelectedId(Number(event.target.value))}
                  disabled={suppliers.length === 0}
                >
                  {suppliers.length === 0 ? (
                    <option value="">No suppliers available</option>
                  ) : (
                    suppliers.map((supplier) => (
                      <option key={supplier.id} value={supplier.id}>
                        {supplier.name} · {supplier.industry}
                      </option>
                    ))
                  )}
                </select>
              </section>

              {supplierLoading ? (
                <div className="supplier-detail empty">
                  Loading scenario workspace...
                </div>
              ) : selectedSupplier ? (
                <ScenarioWorkspace supplier={selectedSupplier} />
              ) : (
                <div className="supplier-detail empty">
                  Select a supplier to run an intervention scenario.
                </div>
              )}

              {selectedSummary && (
                <section className="scenario-decision-context">
                  <p className="eyebrow">Decision context</p>
                  <h2>{selectedSummary.name}</h2>
                  <div className="scenario-context-grid">
                    <div>
                      <span>What the scenario changes</span>
                      <strong>
                        Payment timing or supplier dependency assumptions
                      </strong>
                    </div>
                    <div>
                      <span>Current risk impact</span>
                      <strong>{selectedSummary.risk_level} risk</strong>
                    </div>
                    <div>
                      <span>Intervention implication</span>
                      <strong>{selectedSummary.recommended_action}</strong>
                    </div>
                  </div>
                </section>
              )}
            </main>
          ) : (
            <>
          <section className="saas-page-header">
            <div>
              <p className="eyebrow">Overview</p>
              <h1>Supplier portfolio</h1>
              <p>
                Monitor financial risk, supplier dependency, and intervention
                opportunities across your supplier network.
              </p>
            </div>

            <div className="saas-page-header-meta">
              <span className="saas-live-indicator">
                <span />
                Live model data
              </span>
              <span>{suppliers.length} suppliers</span>
            </div>
          </section>

          <PortfolioDashboard suppliers={suppliers} />

          <section
            id="supplier-workspace"
            className="decision-workspace"
            aria-labelledby="workspace-title"
          >
            <div className="decision-workspace-header">
              <div>
                <p className="eyebrow">Decision workspace</p>
                <h2 id="workspace-title">
                  {selectedSummary
                    ? selectedSummary.name
                    : "Select a supplier"}
                </h2>
                {selectedSummary && (
                  <p className="decision-workspace-context">
                    {selectedSummary.industry} · Currently selected from the
                    supplier attention queue
                  </p>
                )}
              </div>

              {selectedSummary && (
                <div className="decision-workspace-status">
                  <span>Current risk</span>
                  <strong>{selectedSummary.risk_level}</strong>
                </div>
              )}
            </div>

            <PrioritySupplierQueue
              suppliers={suppliers}
              onSelectSupplier={setSelectedId}
            />

            {supplierLoading ? (
              <div className="supplier-detail empty">
                Loading supplier decision workspace...
              </div>
            ) : (
              <div className="supplier-workspace">
                <SupplierList
                  suppliers={suppliers}
                  selectedId={selectedId}
                  onSelect={setSelectedId}
                />
                <SupplierDetail supplier={selectedSupplier} />
              </div>
            )}
          </section>

          <section id="suppliers-page" className="suppliers-page">
            <div className="suppliers-page-header">
              <div>
                <p className="eyebrow">Supplier network</p>
                <h2>Suppliers</h2>
                <p className="suppliers-page-description">
                  Manage and review financial risk across your supplier
                  network.
                </p>
              </div>

              <div className="suppliers-page-count">
                <strong>{filteredSuppliers.length}</strong>
                <span>
                  {filteredSuppliers.length === 1 ? "supplier" : "suppliers"}
                </span>
              </div>
            </div>

            <div className="supplier-filters">
              <label className="supplier-search">
                <span className="supplier-filter-label">Search</span>
                <input
                  type="search"
                  placeholder="Search suppliers..."
                  value={supplierSearch}
                  onChange={(event) => setSupplierSearch(event.target.value)}
                />
              </label>

              <label className="supplier-filter">
                <span className="supplier-filter-label">Risk</span>
                <select
                  value={supplierRiskFilter}
                  onChange={(event) =>
                    setSupplierRiskFilter(event.target.value)
                  }
                >
                  <option value="All">All risk levels</option>
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
                </select>
              </label>

              <label className="supplier-filter">
                <span className="supplier-filter-label">Action</span>
                <select
                  value={supplierActionFilter}
                  onChange={(event) =>
                    setSupplierActionFilter(event.target.value)
                  }
                >
                  <option value="All">All actions</option>
                  <option value="Offer early payment">
                    Offer early payment
                  </option>
                  <option value="Reduce dependency">
                    Reduce dependency
                  </option>
                  <option value="Monitor">Monitor</option>
                </select>
              </label>
            </div>

            <PrioritySupplierQueue
              suppliers={filteredSuppliers}
              onSelectSupplier={setSelectedId}
            />
          </section>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
