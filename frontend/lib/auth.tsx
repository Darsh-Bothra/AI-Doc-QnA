"use client"

import { createContext, useCallback, useContext, useMemo, useSyncExternalStore } from "react"

const TOKEN_KEY = "ai_doc_qa_token"
const AUTH_EVENT = "ai-doc-qa-auth"

function subscribe(onChange: () => void) {
  window.addEventListener("storage", onChange)
  window.addEventListener(AUTH_EVENT, onChange)
  return () => {
    window.removeEventListener("storage", onChange)
    window.removeEventListener(AUTH_EVENT, onChange)
  }
}

function getToken() {
  return window.localStorage.getItem(TOKEN_KEY)
}

function getClientMounted() {
  return true
}

function getServerFalse() {
  return false
}

function getServerToken() {
  return null
}

type AuthContextValue = {
  token: string | null
  ready: boolean
  isAuthenticated: boolean
  setToken: (token: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const ready = useSyncExternalStore(
    () => () => {},
    getClientMounted,
    getServerFalse
  )
  const token = useSyncExternalStore(subscribe, getToken, getServerToken)

  const setToken = useCallback((value: string) => {
    window.localStorage.setItem(TOKEN_KEY, value)
    window.dispatchEvent(new Event(AUTH_EVENT))
  }, [])

  const logout = useCallback(() => {
    window.localStorage.removeItem(TOKEN_KEY)
    window.dispatchEvent(new Event(AUTH_EVENT))
  }, [])

  const value = useMemo(
    () => ({
      token,
      ready,
      isAuthenticated: Boolean(token),
      setToken,
      logout,
    }),
    [token, ready, setToken, logout]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider")
  }
  return context
}
