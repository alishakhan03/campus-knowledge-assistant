import { CheckCircle2, FileUp, UploadCloud } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { documentApi } from '../api/endpoints'

const CATEGORIES = [
  'ACADEMIC',
  'EXAMINATION',
  'ADMISSION',
  'SCHOLARSHIP',
  'HOSTEL',
  'PLACEMENT',
  'DEPARTMENT',
  'GENERAL',
]

export default function AdminUploadPage() {
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('GENERAL')
  const [department, setDepartment] = useState('')
  const [academicYear, setAcademicYear] = useState('')
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const [success, setSuccess] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    if (!file) {
      setError('Please choose a PDF file')
      return
    }

    const formData = new FormData()
    formData.append('title', title)
    formData.append('description', description)
    formData.append('category', category)
    formData.append('department', department)
    formData.append('academic_year', academicYear)
    formData.append('file', file)

    setUploading(true)
    try {
      await documentApi.upload(formData)
      setSuccess(true)
      setTimeout(() => navigate('/admin/documents'), 900)
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <>
      <div className="topbar">
        <h1>Upload Document</h1>
      </div>
      <div className="page-body">
        <form className="card" style={{ maxWidth: 520 }} onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Title</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div className="form-group">
            <label>Category</label>
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Department (optional)</label>
            <input value={department} onChange={(e) => setDepartment(e.target.value)} />
          </div>
          <div className="form-group">
            <label>Academic Year (optional)</label>
            <input placeholder="2025-26" value={academicYear} onChange={(e) => setAcademicYear(e.target.value)} />
          </div>
          <div className="form-group">
            <label>PDF File</label>
            <label
              htmlFor="pdf-upload"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '14px 16px',
                border: '1.5px dashed var(--border)',
                borderRadius: 10,
                cursor: 'pointer',
                background: 'var(--surface-alt)',
                fontWeight: 500,
                fontSize: 13.5,
                color: file ? 'var(--text)' : 'var(--muted-text)',
              }}
            >
              <FileUp size={18} style={{ flexShrink: 0 }} />
              {file ? file.name : 'Click to choose a PDF file'}
            </label>
            <input
              id="pdf-upload"
              type="file"
              accept="application/pdf"
              onChange={(e) => setFile(e.target.files[0])}
              required
              style={{ display: 'none' }}
            />
          </div>

          {error && <div className="error-text" style={{ marginBottom: 14 }}>{error}</div>}
          {success && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                color: 'var(--success)',
                background: 'var(--success-bg)',
                padding: '8px 11px',
                borderRadius: 8,
                marginBottom: 14,
                fontSize: 13.5,
              }}
            >
              <CheckCircle2 size={15} />
              Uploaded. Processing has started in the background.
            </div>
          )}

          <button className="btn btn-primary" disabled={uploading}>
            {uploading ? <span className="spinner" /> : <UploadCloud size={16} />}
            {uploading ? 'Uploading...' : 'Upload'}
          </button>
        </form>
      </div>
    </>
  )
}
