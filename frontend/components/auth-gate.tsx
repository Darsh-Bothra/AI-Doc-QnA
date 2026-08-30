"use client"

import { useEffect } from "react"
import { usePathname, useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth"
import { Skeleton } from "@/components/ui/skeleton"

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { token, ready } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!ready) return
    if (!token) {
      router.replace("/login")
    }
  }, [ready, token, router, pathname])

  if (!ready || !token) {
    return (
      <div className="flex flex-1 flex-col">
        <div className="border-b border-border px-6 py-3">
          <Skeleton className="h-6 w-28" />
        </div>
        <div className="mx-auto w-full max-w-5xl space-y-4 p-6">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-40 w-full" />
        </div>
      </div>
    )
  }

  return <>{children}</>
}
