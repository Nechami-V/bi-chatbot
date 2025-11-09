import { useEffect, useState } from 'react'
import { login as apiLogin, me } from '../services/api.js'

const KEY = 'access_token'

export function useAuth() {
  const [token, setToken] = useState(() => localStorage.getItem(KEY) || '')
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(!!token)
  const [error, setError] = useState('')

  useEffect(() => {
    let canceled = false
    async function fetchMe() {
      if (!token) return
      setLoading(true)
      setError('')
      try {
        const data = await me(token)
        if (!canceled) setUser(data.user)
      } catch (e) {
        if (!canceled) {
          setError(String(e?.message || e))
          setToken('')
          localStorage.removeItem(KEY)
        }
      } finally {
        if (!canceled) setLoading(false)
      }
    }
    fetchMe()
    return () => { canceled = true }
  }, [token])

  async function signIn(email, password) {
    setError('')
    const resp = await apiLogin(email, password)
    const t = resp.access_token
    setToken(t)
    localStorage.setItem(KEY, t)
    // user/me fetched by effect
  }

  function signOut() {
    setToken('')
    setUser(null)
    localStorage.removeItem(KEY)
  }

  return { token, user, loading, error, signIn, signOut }
}

