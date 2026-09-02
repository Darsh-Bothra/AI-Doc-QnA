import { afterEach, describe, expect, mock, test } from "bun:test"
import { ApiError, api } from "./api"

const originalFetch = globalThis.fetch
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    statusText: status === 200 ? "OK" : "Error",
    headers: { "Content-Type": "application/json" },
  })
}

function mockFetch(
  handler: (url: string, init?: RequestInit) => Response | Promise<Response>
) {
  const fetchMock = mock(
    async (input: RequestInfo | URL, init?: RequestInit) => {
      const url =
        typeof input === "string"
          ? input
          : input instanceof URL
            ? input.href
            : input.url
      return handler(url, init)
    }
  )
  globalThis.fetch = fetchMock as typeof fetch
  return fetchMock
}

afterEach(() => {
  globalThis.fetch = originalFetch
  mock.restore()
})

describe("ApiError", () => {
  test("stores status and message", () => {
    const error = new ApiError(401, "Invalid credentials")
    expect(error).toBeInstanceOf(Error)
    expect(error.name).toBe("ApiError")
    expect(error.status).toBe(401)
    expect(error.message).toBe("Invalid credentials")
  })
})

describe("api", () => {
  test("login posts credentials and returns the token payload", async () => {
    const fetchMock = mockFetch((url, init) => {
      expect(url).toBe(`${API_URL}/auth/login`)
      expect(init?.method).toBe("POST")
      expect(init?.body).toBe(
        JSON.stringify({ email: "user@example.com", password: "secret" })
      )
      return jsonResponse({ access_token: "tok_123", token_type: "bearer" })
    })

    const result = await api.login("user@example.com", "secret")

    expect(result).toEqual({ access_token: "tok_123", token_type: "bearer" })
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  test("authenticated requests send a Bearer token", async () => {
    mockFetch((_url, init) => {
      const headers = new Headers(init?.headers)
      expect(headers.get("Authorization")).toBe("Bearer tok_123")
      expect(headers.get("Content-Type")).toBe("application/json")
      return jsonResponse({ total_count: 0, documents: [] })
    })

    const result = await api.listDocuments("tok_123")
    expect(result).toEqual({ total_count: 0, documents: [] })
  })

  test("uploadDocument sends FormData without forcing JSON content type", async () => {
    mockFetch((_url, init) => {
      const headers = new Headers(init?.headers)
      expect(headers.get("Content-Type")).toBeNull()
      expect(headers.get("Authorization")).toBe("Bearer tok_123")
      expect(init?.body).toBeInstanceOf(FormData)
      expect(init?.method).toBe("POST")
      return jsonResponse({
        id: 1,
        name: "notes.pdf",
        status: "processing",
        error_message: null,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      })
    })

    const file = new File(["hello"], "notes.pdf", { type: "application/pdf" })
    const result = await api.uploadDocument("tok_123", file)
    expect(result.name).toBe("notes.pdf")
  })

  test("returns undefined for 204 responses", async () => {
    mockFetch(() => new Response(null, { status: 204 }))
    await expect(api.deleteDocument("tok_123", 9)).resolves.toBeUndefined()
  })

  test("throws ApiError using a string detail", async () => {
    mockFetch(() =>
      jsonResponse({ detail: "Invalid credentials" }, 401)
    )

    try {
      await api.login("user@example.com", "wrong")
      throw new Error("expected login to fail")
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError)
      expect((error as ApiError).status).toBe(401)
      expect((error as ApiError).message).toBe("Invalid credentials")
    }
  })

  test("joins FastAPI validation details", async () => {
    mockFetch(() =>
      jsonResponse(
        { detail: [{ msg: "Field required" }, "password too short"] },
        422
      )
    )

    try {
      await api.register("user@example.com", "x")
      throw new Error("expected register to fail")
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError)
      expect((error as ApiError).message).toBe(
        "Field required password too short"
      )
    }
  })

  test("falls back to status text when the error body is not JSON", async () => {
    mockFetch(
      () =>
        new Response("nope", {
          status: 503,
          statusText: "Service Unavailable",
        })
    )

    try {
      await api.getDocument("tok_123", 1)
      throw new Error("expected getDocument to fail")
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError)
      expect((error as ApiError).status).toBe(503)
      expect((error as ApiError).message).toBe("Service Unavailable")
    }
  })
})
