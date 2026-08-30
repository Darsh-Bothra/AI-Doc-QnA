import type { ReactNode } from "react"
import { AppHeader } from "@/components/app-header"
import { AuthGate } from "@/components/auth-gate"

export default function WorkspaceLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <AuthGate>
      <div className="flex min-h-full flex-1 flex-col">
        <AppHeader />
        {children}
      </div>
    </AuthGate>
  )
}
