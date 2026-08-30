"use client"

import { useRef, useState } from "react"
import { toast } from "sonner"
import { Upload } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { api, ApiError } from "@/lib/api"
import { useAuth } from "@/lib/auth"

const MAX_SIZE = 10 * 1024 * 1024

type UploadDialogProps = {
  onUploaded: () => void
}

export function UploadDialog({ onUploaded }: UploadDialogProps) {
  const { token, logout } = useAuth()
  const inputRef = useRef<HTMLInputElement>(null)
  const [open, setOpen] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [pending, setPending] = useState(false)

  async function handleUpload() {
    if (!token || !file) return
    setPending(true)
    try {
      await api.uploadDocument(token, file)
      toast.success("Upload started. Indexing runs in the background.")
      setOpen(false)
      setFile(null)
      onUploaded()
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        logout()
        return
      }
      toast.error(error instanceof Error ? error.message : "Upload failed")
    } finally {
      setPending(false)
    }
  }

  function onFileChange(next: File | null) {
    if (!next) {
      setFile(null)
      return
    }
    if (next.type !== "application/pdf") {
      toast.error("Only PDF files are supported.")
      return
    }
    if (next.size > MAX_SIZE) {
      toast.error("File is larger than 10 MB.")
      return
    }
    setFile(next)
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next)
        if (!next) setFile(null)
      }}
    >
      <DialogTrigger asChild>
        <Button>
          <Upload data-icon="inline-start" />
          Upload PDF
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Upload a document</DialogTitle>
          <DialogDescription>
            PDFs only, up to 10 MB. You can ask questions once indexing is
            complete.
          </DialogDescription>
        </DialogHeader>
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="flex min-h-32 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted/40 px-4 py-8 text-center transition-colors hover:bg-muted"
        >
          <Upload className="mb-2 size-5 text-muted-foreground" />
          <p className="text-sm text-foreground">
            {file ? file.name : "Choose a PDF"}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {file
              ? `${(file.size / (1024 * 1024)).toFixed(1)} MB`
              : "Click to browse"}
          </p>
        </button>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
        />
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleUpload} disabled={!file || pending}>
            {pending ? "Uploading…" : "Upload"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
