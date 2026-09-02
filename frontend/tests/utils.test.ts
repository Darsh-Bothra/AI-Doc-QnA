import { describe, expect, test } from "bun:test"
import { cn } from "@/lib/utils"

describe("cn", () => {
  test("joins class names", () => {
    expect(cn("px-2", "py-1")).toBe("px-2 py-1")
  })

  test("drops falsy values", () => {
    expect(cn("block", false && "hidden", undefined, "text-sm")).toBe(
      "block text-sm"
    )
  })

  test("keeps the last conflicting Tailwind class", () => {
    expect(cn("px-2", "px-4")).toBe("px-4")
  })
})
