"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth"

export default function HomePage() {
  const router = useRouter()
  const { ready, isAuthenticated } = useAuth()

  useEffect(() => {
    if (!ready) return
    router.replace(isAuthenticated ? "/documents" : "/login")
  }, [ready, isAuthenticated, router])

  return null
}
