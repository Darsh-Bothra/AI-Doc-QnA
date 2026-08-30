"use client"

import { useEffect, useState } from "react"
import { toast } from "sonner"
import { SourceList } from "@/components/source-list"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { api, ApiError } from "@/lib/api"
import { useAuth } from "@/lib/auth"
import type { Document, SearchResponse } from "@/lib/types"

export function SearchView() {
  const { token, logout } = useAuth()
  const [documents, setDocuments] = useState<Document[]>([])
  const [question, setQuestion] = useState("")
  const [documentId, setDocumentId] = useState("all")
  const [result, setResult] = useState<SearchResponse | null>(null)
  const [pending, setPending] = useState(false)

  useEffect(() => {
    if (!token) return
    let cancelled = false
    api
      .listDocuments(token)
      .then((list) => {
        if (cancelled) return
        setDocuments(list.documents.filter((doc) => doc.status === "completed"))
      })
      .catch((error: unknown) => {
        if (cancelled) return
        if (error instanceof ApiError && error.status === 401) {
          logout()
        }
      })
    return () => {
      cancelled = true
    }
  }, [token, logout])

  async function onSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!token) return
    setPending(true)
    try {
      const response = await api.search(token, {
        question,
        document_id: documentId === "all" ? undefined : Number(documentId),
      })
      setResult(response)
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        logout()
        return
      }
      toast.error(error instanceof Error ? error.message : "Search failed")
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-6 py-8">
      <div className="space-y-1">
        <h1 className="text-xl font-medium tracking-tight">Search</h1>
        <p className="text-sm text-muted-foreground">
          Semantic search over your indexed chunks. Scope to one document or
          search everything.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Query</CardTitle>
          <CardDescription>
            Returns matching passages without generating an answer.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={onSearch}>
            <div className="space-y-2">
              <Label htmlFor="question">Question</Label>
              <Input
                id="question"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Find passages about…"
                maxLength={2000}
                required
              />
            </div>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
              <div className="space-y-2 sm:flex-1">
                <Label>Document</Label>
                <Select value={documentId} onValueChange={setDocumentId}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="All documents" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All documents</SelectItem>
                    {documents.map((doc) => (
                      <SelectItem key={doc.id} value={String(doc.id)}>
                        {doc.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button type="submit" disabled={pending || !question.trim()}>
                {pending ? "Searching…" : "Search"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {result ? (
        <Card>
          <CardHeader>
            <CardTitle>Results</CardTitle>
            <CardDescription>
              {result.results.length} hit
              {result.results.length === 1 ? "" : "s"} for “{result.question}”
            </CardDescription>
          </CardHeader>
          <CardContent>
            <SourceList sources={result.results} />
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}
