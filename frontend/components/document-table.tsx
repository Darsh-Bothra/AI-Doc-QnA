"use client"

import { useRouter } from "next/navigation"
import { MoreHorizontal, Trash2 } from "lucide-react"
import { toast } from "sonner"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { StatusBadge } from "@/components/status-badge"
import { api, ApiError } from "@/lib/api"
import { useAuth } from "@/lib/auth"
import type { Document } from "@/lib/types"

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value))
}

type DocumentTableProps = {
  documents: Document[]
  onChanged: () => void
}

export function DocumentTable({ documents, onChanged }: DocumentTableProps) {
  const router = useRouter()
  const { token, logout } = useAuth()

  async function remove(id: number) {
    if (!token) return
    try {
      await api.deleteDocument(token, id)
      toast.success("Document deleted")
      onChanged()
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        logout()
        return
      }
      toast.error(error instanceof Error ? error.message : "Delete failed")
    }
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Updated</TableHead>
          <TableHead className="w-12" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {documents.map((doc) => (
          <TableRow
            key={doc.id}
            className="cursor-pointer"
            onClick={() => router.push(`/documents/${doc.id}`)}
          >
            <TableCell className="font-medium">{doc.name}</TableCell>
            <TableCell>
              {doc.status === "failed" && doc.error_message ? (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span>
                      <StatusBadge status={doc.status} />
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>{doc.error_message}</TooltipContent>
                </Tooltip>
              ) : (
                <StatusBadge status={doc.status} />
              )}
            </TableCell>
            <TableCell className="font-mono text-xs text-muted-foreground">
              {formatDate(doc.updated_at)}
            </TableCell>
            <TableCell onClick={(event) => event.stopPropagation()}>
              <AlertDialog>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" aria-label="Actions">
                      <MoreHorizontal />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <AlertDialogTrigger asChild>
                      <DropdownMenuItem variant="destructive">
                        <Trash2 />
                        Delete
                      </DropdownMenuItem>
                    </AlertDialogTrigger>
                  </DropdownMenuContent>
                </DropdownMenu>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete this document?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This removes the file, stored chunks, and search index
                      for {doc.name}. This cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      variant="destructive"
                      onClick={() => remove(doc.id)}
                    >
                      Delete
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
