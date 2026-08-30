import { AlertTriangle, CheckCircle2, Clock, FileStack } from 'lucide-react'
import { useEffect, useState } from 'react'
import { documentApi } from '../api/endpoints'

export default function AdminOverviewPage() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    documentApi.stats().then((res) => setStats(res.data))
  }, [])

  const cards = [
    { label: 'Total documents', value: stats?.total, icon: <FileStack size={17} /> },
    { label: 'Processed', value: stats?.processed, icon: <CheckCircle2 size={17} /> },
    { label: 'Processing', value: stats?.processing, icon: <Clock size={17} /> },
    { label: 'Failed', value: stats?.failed, icon: <AlertTriangle size={17} /> },
  ]

  return (
    <>
      <div className="topbar">
        <h1>Admin Overview</h1>
      </div>
      <div className="page-body">
        <div className="stat-grid">
          {cards.map((c) => (
            <div className="stat-card" key={c.label}>
              <div className="icon-badge">{c.icon}</div>
              <div className="value">{c.value ?? '—'}</div>
              <div className="label">{c.label}</div>
            </div>
          ))}
        </div>
        <p className="helper-text">
          Upload new PDFs from the "Upload Document" page. Documents are processed automatically:
          text is extracted, split into chunks, embedded, and stored for retrieval.
        </p>
      </div>
    </>
  )
}
