import { useEffect, useState } from "react";
import { api } from "./api";
import SupplierList from "./components/SupplierList.jsx";
import SupplierDetail from "./components/SupplierDetail.jsx";

export default function App() {
  const [suppliers, setSuppliers] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .listSuppliers()
      .then((data) => {
        setSuppliers(data);
        if (data.length > 0) setSelectedId(data[0].id);
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (selectedId == null) return;
    api.getSupplier(selectedId).then(setSelectedSupplier).catch((err) => setError(err.message));
  }, [selectedId]);

  return (
    <div className="app">
      <header>
        <h1>Supplier Cash-Flow Predictor</h1>
        <p className="hint">
          Demo data is fully synthetic — see the backend README for generation assumptions. No LLM in the scoring
          path.
        </p>
      </header>

      {error && <div className="error">Couldn't reach the API at the configured URL: {error}</div>}

      <main>
        <SupplierList suppliers={suppliers} selectedId={selectedId} onSelect={setSelectedId} />
        <SupplierDetail supplier={selectedSupplier} />
      </main>
    </div>
  );
}
