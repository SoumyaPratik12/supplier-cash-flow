const RISK_COLOR = {
  Low: "#2e7d32",
  Medium: "#ed6c02",
  High: "#c62828",
};

export default function SupplierList({ suppliers, selectedId, onSelect }) {
  return (
    <div className="supplier-list">
      <h2>Suppliers, ranked by intervention priority</h2>
      <p className="hint">Sorted by risk score × dependency weight — the top row is who to call first.</p>
      <table>
        <thead>
          <tr>
            <th>Supplier</th>
            <th>Industry</th>
            <th>Risk</th>
            <th>Recommended action</th>
          </tr>
        </thead>
        <tbody>
          {suppliers.map((s) => (
            <tr
              key={s.id}
              className={s.id === selectedId ? "selected" : ""}
              onClick={() => onSelect(s.id)}
            >
              <td>{s.name}</td>
              <td>{s.industry}</td>
              <td>
                <span className="risk-badge" style={{ backgroundColor: RISK_COLOR[s.risk_level] }}>
                  {s.risk_level}
                </span>
              </td>
              <td>{s.recommended_action}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
