"use client"

import { useCallback, useEffect, useState } from "react"
import { FileText } from "lucide-react"
import { toast } from "sonner"
import { DocumentTable } from "@/components/document-table"
import { UploadDialog } from "@/components/upload-dialog"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { api, ApiError } from "@/lib/api"
import { useAuth } from "@/lib/auth"
import type { Document } from "@/lib/types"

export function DocumentsView() {
  const { token, logout } = useAuth()
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    if (!token) return
    try {
      const result = await api.listDocuments(token)
      setDocuments(result.documents)
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        logout()
        return
      }
      toast.error(error instanceof Error ? error.message : "Could not load documents")
    } finally {
      setLoading(false)
    }
  }, [token, logout])

  useEffect(() => {
    if (!token) return
    let cancelled = false
    api
      .listDocuments(token)
      .then((result) => {
        if (cancelled) return
        setDocuments(result.documents)
      })
      .catch((error: unknown) => {
        if (cancelled) return
        if (error instanceof ApiError && error.status === 401) {
          logout()
          return
        }
        toast.error(error instanceof Error ? error.message : "Could not load documents")
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [token, logout])

  const hasProcessing = documents.some((doc) => doc.status === "processing")

  useEffect(() => {
    if (!hasProcessing) return
    const id = window.setInterval(() => {
      void load()
    }, 3000)
    return () => window.clearInterval(id)
  }, [hasProcessing, load])

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-6 py-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-1">
          <h1 className="text-xl font-medium tracking-tight">Documents</h1>
          <p className="text-sm text-muted-foreground">
            Upload PDFs, wait until they are ready, then ask or search.
          </p>
        </div>
        <UploadDialog onUploaded={() => void load()} />
      </div>

      {loading ? (
        <Skeleton className="h-64 w-full" />
      ) : documents.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <FileText className="mb-3 size-6 text-muted-foreground" />
            <p className="text-sm font-medium">No documents yet</p>
            <p className="mt-1 max-w-sm text-sm text-muted-foreground">
              Upload a PDF to extract, index, and question it. Indexing usually
              takes a few seconds.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card className="py-0">
          <CardContent className="px-0">
            <DocumentTable documents={documents} onChanged={() => void load()} />
          </CardContent>
        </Card>
      )}
    </div>
  )
}
