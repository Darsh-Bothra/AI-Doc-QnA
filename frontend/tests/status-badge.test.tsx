import { describe, expect, test } from "bun:test"
import { renderToStaticMarkup } from "react-dom/server"
import { StatusBadge } from "@/components/status-badge"

describe("StatusBadge", () => {
  test("renders a Processing label", () => {
    const html = renderToStaticMarkup(<StatusBadge status="processing" />)
    expect(html).toContain("Processing")
  })

  test("renders Ready for completed documents", () => {
    const html = renderToStaticMarkup(<StatusBadge status="completed" />)
    expect(html).toContain("Ready")
  })

  test("renders Failed for failed documents", () => {
    const html = renderToStaticMarkup(<StatusBadge status="failed" />)
    expect(html).toContain("Failed")
  })
})
