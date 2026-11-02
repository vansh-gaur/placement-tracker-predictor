export default function StatsCards({ stats, statuses }) {
  if (!stats) return null

  return (
    <section className="stats">
      <div className="stat-card">
        <span className="stat-label">Total applications</span>
        <strong>{stats.total}</strong>
      </div>
      <div className="stat-card">
        <span className="stat-label">Offers</span>
        <strong>{stats.offers}</strong>
      </div>
      {statuses.map((status) => (
        <div className="stat-card" key={status}>
          <span className="stat-label">{status}</span>
          <strong>{stats.by_status[status] ?? 0}</strong>
        </div>
      ))}
    </section>
  )
}
