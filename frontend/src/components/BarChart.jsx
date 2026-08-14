export default function BarChart({ data }) {
  if (!data?.length) {
    return <div className="empty-state">No revenue events for this day.</div>;
  }

  const max = Math.max(...data.map((item) => item.revenue_paise), 1);

  return (
    <div className="bar-chart">
      {data.map((item) => (
        <div className="bar-column" key={item.hour}>
          <span className="bar-value">
            ₹{(item.revenue_paise / 100).toLocaleString("en-IN")}
          </span>
          <div className="bar-track">
            <div
              className="bar"
              style={{ height: `${Math.max(5, (item.revenue_paise / max) * 100)}%` }}
            />
          </div>
          <span className="bar-label">{String(item.hour).padStart(2, "0")}:00</span>
        </div>
      ))}
    </div>
  );
}
