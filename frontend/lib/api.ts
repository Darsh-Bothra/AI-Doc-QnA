import type {
  AskResponse,
  Document,
  DocumentListResponse,
  LoginResponse,
  SearchResponse,
} from "@/lib/types"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

function detailMessage(detail: unknown, fallback: string) {
  if (typeof detail === "string") return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: string }).msg)
        }
        return JSON.stringify(item)
      })
      .join(" ")
  }
  return fallback
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> {
  const headers = new Headers(options.headers)
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let message = response.statusText || "Request failed"
    try {
      const body = (await response.json()) as { detail?: unknown }
      message = detailMessage(body.detail, message)
    } catch {
      // ignore non-JSON error bodies
    }
    throw new ApiError(response.status, message)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export const api = {
  register: (email: string, password: string) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  login: (email: string, password: string) =>
    request<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  listDocuments: (token: string) =>
    request<DocumentListResponse>("/documents/", {}, token),

  getDocument: (token: string, id: number) =>
    request<Document>(`/documents/${id}`, {}, token),

  uploadDocument: (token: string, file: File) => {
    const body = new FormData()
    body.append("file", file)
    return request<Document>("/documents/", { method: "POST", body }, token)
  },

  deleteDocument: (token: string, id: number) =>
    request<{ message: string }>(`/documents/${id}`, { method: "DELETE" }, token),

  search: (
    token: string,
    payload: { question: string; document_id?: number; limit?: number }
  ) =>
    request<SearchResponse>(
      "/documents/search",
      { method: "POST", body: JSON.stringify(payload) },
      token
    ),

  ask: (token: string, documentId: number, query: string) =>
    request<AskResponse>(
      `/documents/${documentId}/ask`,
      { method: "POST", body: JSON.stringify({ query }) },
      token
    ),
}
