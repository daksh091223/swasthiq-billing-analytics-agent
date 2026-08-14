export default function RankingTable({ title, rows, valueLabel, formatValue }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <h3>{title}</h3>
        <span>{valueLabel}</span>
      </div>

      {!rows?.length ? (
        <div className="empty-state">No medicine data.</div>
      ) : (
        <div className="ranking-list">
          {rows.slice(0, 5).map((row, index) => (
            <div className="ranking-row" key={row.drug_name}>
              <span className="rank">{index + 1}</span>
              <span className="medicine-name">{row.drug_name}</span>
              <strong>{formatValue(row)}</strong>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
