export default function Sidebar({ active, onChange }) {
  const items = [
    ["dashboard", "EOD Reconciliation"],
    ["analytics", "Analytics"],
    ["narrative", "AI Narrative"],
  ];

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">S</div>
        <div>
          <strong>SwasthiQ</strong>
          <span>Billing Intelligence</span>
        </div>
      </div>

      <nav>
        {items.map(([id, label]) => (
          <button
            key={id}
            className={active === id ? "nav-item active" : "nav-item"}
            onClick={() => onChange(id)}
          >
            <span className={`nav-icon ${id}`} />
            {label}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <span className="status-dot" />
        Deterministic engine online
      </div>
    </aside>
  );
}
