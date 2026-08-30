import { AlertCircle, CheckCircle2, Clock, Eye, FileX2, RefreshCw, Search, Trash2, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { documentApi } from '../api/endpoints'

const STATUS_ICON = {
  PROCESSED: <CheckCircle2 size={12} />,
  PROCESSING: <Clock size={12} />,
  UPLOADED: <Clock size={12} />,
  FAILED: <AlertCircle size={12} />,
}

export default function AdminDocumentsPage() {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)
  const [preview, setPreview] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')

  async function load() {
    setLoading(true)
    const res = await documentApi.list()
    setDocuments(res.data)
    setLoading(false)
  }

  const filteredDocuments = documents.filter((d) => {
    const q = searchQuery.trim().toLowerCase()
    if (!q) return true
    return (
      d.title.toLowerCase().includes(q) ||
      d.category.toLowerCase().includes(q) ||
      (d.department || '').toLowerCase().includes(q) ||
      (d.academic_year || '').toLowerCase().includes(q)
    )
  })

  useEffect(() => {
    load()
  }, [])

  useEffect(() => {
    return () => {
      if (preview?.url) URL.revokeObjectURL(preview.url)
    }
  }, [preview])

  async function handleDelete(id) {
    if (!window.confirm('Delete this document? This also removes its indexed content.')) return
    setBusyId(id)
    try {
      await documentApi.remove(id)
      setDocuments((prev) => prev.filter((d) => d.id !== id))
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete document')
    } finally {
      setBusyId(null)
    }
  }

  async function handleReprocess(id) {
    setBusyId(id)
    try {
      const res = await documentApi.reprocess(id)
      setDocuments((prev) => prev.map((d) => (d.id === id ? res.data : d)))
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to reprocess document')
    } finally {
      setBusyId(null)
    }
  }

  async function handleView(doc) {
    setBusyId(doc.id)
    try {
      const url = await documentApi.fetchFileObjectUrl(doc.id)
      setPreview({ title: doc.title, url })
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to load document preview')
    } finally {
      setBusyId(null)
    }
  }

  function closePreview() {
    setPreview(null)
  }

  return (
    <>
      <div className="topbar">
        <h1>Documents</h1>
      </div>
      <div className="page-body">
        <div className="input-wrap" style={{ maxWidth: 360, marginBottom: 16 }}>
          <Search size={16} />
          <input
            placeholder="Search by title, category, department, year..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          {loading ? (
            <div style={{ padding: 32, textAlign: 'center' }} className="helper-text">
              <span className="spinner" style={{ marginRight: 8 }} />
              Loading documents...
            </div>
          ) : filteredDocuments.length === 0 ? (
            <div style={{ padding: 40, textAlign: 'center' }}>
              <FileX2 size={28} style={{ color: 'var(--muted-text)', marginBottom: 8 }} />
              <div className="helper-text">
                {documents.length === 0 ? 'No documents uploaded yet.' : 'No documents match your search.'}
              </div>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Category</th>
                    <th>Department</th>
                    <th>Academic Year</th>
                    <th>Status</th>
                    <th>Uploaded</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredDocuments.map((d) => (
                    <tr key={d.id}>
                      <td style={{ fontWeight: 600 }}>{d.title}</td>
                      <td>{d.category}</td>
                      <td>{d.department || '—'}</td>
                      <td>{d.academic_year || '—'}</td>
                      <td>
                        <span className={`status-badge status-${d.status}`}>
                          {STATUS_ICON[d.status]}
                          {d.status}
                        </span>
                        {d.status === 'FAILED' && d.processing_error && (
                          <div className="helper-text" style={{ marginTop: 4, maxWidth: 220 }}>
                            {d.processing_error}
                          </div>
                        )}
                      </td>
                      <td>{new Date(d.created_at).toLocaleDateString()}</td>
                      <td>
                        <div className="table-actions">
                          <button disabled={busyId === d.id} onClick={() => handleView(d)}>
                            <Eye size={13} />
                            View
                          </button>
                          <button disabled={busyId === d.id} onClick={() => handleReprocess(d.id)}>
                            <RefreshCw size={13} />
                            Reprocess
                          </button>
                          <button className="danger" disabled={busyId === d.id} onClick={() => handleDelete(d.id)}>
                            <Trash2 size={13} />
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {preview && (
        <div
          onClick={closePreview}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.55)',
            zIndex: 100,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 24,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'var(--surface)',
              borderRadius: 14,
              width: '100%',
              maxWidth: 860,
              height: '85vh',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              boxShadow: 'var(--shadow-lg)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '14px 18px',
                borderBottom: '1px solid var(--border)',
              }}
            >
              <div style={{ fontWeight: 700, fontSize: 14.5 }}>{preview.title}</div>
              <button className="icon-btn" onClick={closePreview} aria-label="Close preview">
                <X size={18} />
              </button>
            </div>
            <iframe src={preview.url} title={preview.title} style={{ flex: 1, border: 'none' }} />
          </div>
        </div>
      )}
    </>
  )
}