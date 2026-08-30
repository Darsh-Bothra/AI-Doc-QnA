"use client"

import { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"
import { toast } from "sonner"
import { SourceList } from "@/components/source-list"
import { StatusBadge } from "@/components/status-badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import { api, ApiError } from "@/lib/api"
import { useAuth } from "@/lib/auth"
import type { AskResponse, Document } from "@/lib/types"

export function AskView({ documentId }: { documentId: number }) {
  const { token, logout } = useAuth()
  const [document, setDocument] = useState<Document | null>(null)
  const [query, setQuery] = useState("")
  const [result, setResult] = useState<AskResponse | null>(null)
  const [loadingDoc, setLoadingDoc] = useState(true)
  const [asking, setAsking] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!token) return
    try {
      const next = await api.getDocument(token, documentId)
      setDocument(next)
      setError(null)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        logout()
        return
      }
      setError(err instanceof Error ? err.message : "Document not found")
    } finally {
      setLoadingDoc(false)
    }
  }, [token, documentId, logout])

  useEffect(() => {
    if (!token) return
    let cancelled = false
    api
      .getDocument(token, documentId)
      .then((next) => {
        if (cancelled) return
        setDocument(next)
        setError(null)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        if (err instanceof ApiError && err.status === 401) {
          logout()
          return
        }
        setError(err instanceof Error ? err.message : "Document not found")
      })
      .finally(() => {
        if (!cancelled) setLoadingDoc(false)
      })
    return () => {
      cancelled = true
    }
  }, [token, documentId, logout])

  useEffect(() => {
    if (document?.status !== "processing") return
    const id = window.setInterval(() => {
      void load()
    }, 3000)
    return () => window.clearInterval(id)
  }, [document?.status, load])

  async function onAsk(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!token) return
    setAsking(true)
    setResult(null)
    try {
      const response = await api.ask(token, documentId, query)
      setResult(response)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        logout()
        return
      }
      toast.error(err instanceof Error ? err.message : "Ask failed")
    } finally {
      setAsking(false)
    }
  }

  if (loadingDoc) {
    return (
      <div className="mx-auto w-full max-w-5xl space-y-4 px-6 py-8">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  if (error || !document) {
    return (
      <div className="mx-auto w-full max-w-5xl px-6 py-8">
        <Alert variant="destructive">
          <AlertTitle>Unable to load document</AlertTitle>
          <AlertDescription>{error ?? "Not found"}</AlertDescription>
        </Alert>
      </div>
    )
  }

  const ready = document.status === "completed"

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-6 py-8">
      <div className="space-y-3">
        <Button variant="ghost" size="sm" asChild className="-ml-2 w-fit">
          <Link href="/documents">
            <ArrowLeft data-icon="inline-start" />
            Documents
          </Link>
        </Button>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-xl font-medium tracking-tight">{document.name}</h1>
          <StatusBadge status={document.status} />
        </div>
      </div>

      {document.status === "processing" ? (
        <Alert>
          <AlertTitle>Indexing in progress</AlertTitle>
          <AlertDescription>
            This file is being extracted and embedded. Questions will be
            available when the status is ready.
          </AlertDescription>
        </Alert>
      ) : null}

      {document.status === "failed" ? (
        <Alert variant="destructive">
          <AlertTitle>Indexing failed</AlertTitle>
          <AlertDescription>
            {document.error_message ?? "This document cannot be queried."}
          </AlertDescription>
        </Alert>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Ask</CardTitle>
            <CardDescription>
              Answers are grounded in retrieved passages from this file.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-3" onSubmit={onAsk}>
              <Textarea
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="What does this document say about…"
                rows={5}
                maxLength={2000}
                disabled={!ready || asking}
              />
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs text-muted-foreground">{query.length}/2000</p>
                <Button type="submit" disabled={!ready || asking || !query.trim()}>
                  {asking ? "Asking…" : "Ask"}
                </Button>
              </div>
            </form>
            {result ? (
              <div className="mt-6 border-t border-border pt-4">
                <p className="mb-2 text-xs font-medium text-muted-foreground">
                  Answer
                </p>
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {result.answer}
                </p>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Sources</CardTitle>
            <CardDescription>
              Passages used for the latest answer, with similarity scores.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {result ? (
              <SourceList sources={result.sources} />
            ) : (
              <p className="text-sm text-muted-foreground">
                Sources appear here after you ask a question.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
