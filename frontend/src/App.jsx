import { useEffect, useState } from "react";
import { api } from "./api";
import PortfolioDashboard from "./components/PortfolioDashboard";
import PrioritySupplierQueue from "./components/PrioritySupplierQueue";
import SupplierList from "./components/SupplierList.jsx";
import SupplierDetail from "./components/SupplierDetail.jsx";

export default function App() {
  const [suppliers, setSuppliers] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [supplierLoading, setSupplierLoading] = useState(false);
  const [error, setError] = useState(null);

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

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <p className="eyebrow">Supply chain + financial risk intelligence</p>
          <h1>Supplier Cash-Flow Predictor</h1>
          <p className="hint">
            Synthetic demo data · Explainable risk scoring · No LLM in the
            scoring path
          </p>
        </div>
      </header>

      {error && (
        <div className="error" role="alert">
          Couldn't reach the API at the configured URL: {error}
        </div>
      )}

      <PortfolioDashboard suppliers={suppliers} />

      <PrioritySupplierQueue
        suppliers={suppliers}
        onSelectSupplier={setSelectedId}
      />

      <section className="decision-workspace" aria-labelledby="workspace-title">
        <div className="decision-workspace-header">
          <div>
            <p className="eyebrow">Decision workspace</p>
            <h2 id="workspace-title">
              {selectedSummary ? selectedSummary.name : "Select a supplier"}
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

        {supplierLoading ? (
          <div className="supplier-detail empty">
            Loading supplier decision workspace...
          </div>
        ) : (
          <main className="supplier-workspace">
            <SupplierList
              suppliers={suppliers}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
            <SupplierDetail supplier={selectedSupplier} />
          </main>
        )}
      </section>
    </div>
  );
}
