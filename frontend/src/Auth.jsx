import { useState } from 'react'
import axios from 'axios'

const api = axios.create({ baseURL: 'http://127.0.0.1:8000/api/auth' })
const msg = (x) => {
  const d = x?.response?.data?.detail
  if (Array.isArray(d)) return d[0]?.msg || 'Check the form.'
  return typeof d === 'string' ? d : 'Cannot reach the backend on port 8000. Is uvicorn running?'
}

export default function Auth({ onAuth }) {
  const [mode, setMode] = useState('signup')
  const [f, setF] = useState({ name: '', email: '', password: '' })
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault(); setErr(''); setBusy(true)
    try {
      const body = mode === 'signup' ? f : { email: f.email, password: f.password }
      const { data } = await api.post(mode === 'signup' ? '/signup' : '/login', body)
      onAuth(data.token, data.user)
    } catch (x) { setErr(msg(x)) } finally { setBusy(false) }
  }

  return (
    <div className="authwrap">
      <div className="authbrand">LeadIt</div>
      <div className="card stack">
        <form className="stack" onSubmit={submit}>
          <h2>{mode === 'signup' ? 'Create your account' : 'Welcome back'}</h2>
          {mode === 'signup' && (
            <input className="field" placeholder="Full name" required value={f.name}
              onChange={(e) => setF({ ...f, name: e.target.value })} />
          )}
          <input className="field" type="email" placeholder="Email" required value={f.email}
            onChange={(e) => setF({ ...f, email: e.target.value })} />
          <input className="field" type="password" placeholder="Password (min 8 characters)" minLength={8} required
            value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} />
          <button className="btn" disabled={busy}>{busy ? 'Please wait...' : mode === 'signup' ? 'Sign up' : 'Log in'}</button>
          <button type="button" className="btn ghost"
            onClick={() => { setErr(''); setMode(mode === 'signup' ? 'login' : 'signup') }}>
            {mode === 'signup' ? 'I already have an account' : 'Create an account'}
          </button>
        </form>
        {err && <p className="error">{err}</p>}
      </div>
    </div>
  )
}
