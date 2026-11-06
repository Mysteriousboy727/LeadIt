import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import axios from 'axios'
import App from './App.jsx'
import Auth from './Auth.jsx'
import './index.css'

function Gate() {
  const [user, setUser] = useState(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const tok = localStorage.getItem('leadit_token')
    if (!tok) { setReady(true); return }
    axios.get('http://127.0.0.1:8000/api/auth/me', { headers: { Authorization: 'Bearer ' + tok } })
      .then((r) => setUser(r.data))
      .catch(() => localStorage.removeItem('leadit_token'))
      .finally(() => setReady(true))
  }, [])

  const onAuth = (token, u) => { localStorage.setItem('leadit_token', token); setUser(u) }
  const logout = () => { localStorage.removeItem('leadit_token'); setUser(null) }

  if (!ready) return null
  if (!user) return <Auth onAuth={onAuth} />
  return (
    <>
      <App />
      <button className="btn ghost logout" onClick={logout}>Log out ({user.name})</button>
    </>
  )
}

createRoot(document.getElementById('root')).render(<Gate />)
