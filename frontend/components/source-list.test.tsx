import { describe, expect, test } from "bun:test"
import { renderToStaticMarkup } from "react-dom/server"
import { SourceList } from "./source-list"

describe("SourceList", () => {
  test("shows an empty state when there are no sources", () => {
    const html = renderToStaticMarkup(<SourceList sources={[]} />)
    expect(html).toContain("No sources were returned for this query.")
  })
})
