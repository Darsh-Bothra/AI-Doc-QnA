"use client"

import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { useAuth } from "@/lib/auth"
import { cn } from "@/lib/utils"

const links = [
  { href: "/documents", label: "Documents" },
  { href: "/search", label: "Search" },
]

export function AppHeader() {
  const pathname = usePathname()
  const router = useRouter()
  const { logout } = useAuth()

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-5xl items-center gap-6 px-6">
        <Link href="/documents" className="flex items-center gap-2 text-sm font-medium">
          <FileText className="size-4" />
          Doc QA
        </Link>
        <nav className="flex items-center gap-1">
          {links.map((link) => {
            const active =
              pathname === link.href || pathname.startsWith(`${link.href}/`)
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "rounded-md px-2.5 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground",
                  active && "bg-muted text-foreground"
                )}
              >
                {link.label}
              </Link>
            )
          })}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <Separator orientation="vertical" className="hidden h-4 sm:block" />
          <Button
            variant="ghost"
            onClick={() => {
              logout()
              router.replace("/login")
            }}
          >
            Sign out
          </Button>
        </div>
      </div>
    </header>
  )
}
