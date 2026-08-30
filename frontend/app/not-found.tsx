import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function NotFound() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-4 px-6">
      <p className="text-sm text-muted-foreground">Page not found</p>
      <Button asChild>
        <Link href="/documents">Back to documents</Link>
      </Button>
    </main>
  )
}
