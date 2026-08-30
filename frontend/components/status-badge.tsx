import { Badge } from "@/components/ui/badge"
import type { DocumentStatus } from "@/lib/types"

const labels: Record<DocumentStatus, string> = {
  processing: "Processing",
  completed: "Ready",
  failed: "Failed",
}

const variants: Record<DocumentStatus, "secondary" | "outline" | "destructive"> = {
  processing: "secondary",
  completed: "outline",
  failed: "destructive",
}

export function StatusBadge({ status }: { status: DocumentStatus }) {
  return <Badge variant={variants[status]}>{labels[status]}</Badge>
}
