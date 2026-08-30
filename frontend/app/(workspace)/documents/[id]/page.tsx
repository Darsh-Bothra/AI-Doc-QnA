"use client"

import { useParams } from "next/navigation"
import { AskView } from "@/components/ask-view"

export default function DocumentPage() {
  const params = useParams<{ id: string }>()
  const id = Number(params.id)

  if (!Number.isFinite(id) || id < 1) {
    return (
      <p className="px-6 py-8 text-sm text-muted-foreground">Invalid document.</p>
    )
  }

  return <AskView documentId={id} />
}
