/**
 * @vitest-environment jsdom
 */

import React from "react"
import { render, screen, within } from "@testing-library/react"
import "@testing-library/jest-dom"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { MobileBottomNav } from "@/components/layout/mobile-bottom-nav"

const mockUsePathname = vi.fn()

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({
    user: {
      role: "broker",
      first_name: "Test",
      last_name: "User",
      email: "test@example.com",
    },
    logout: vi.fn(),
  }),
}))

vi.mock("next/navigation", () => ({
  usePathname: () => mockUsePathname(),
}))

vi.mock("next/link", () => {
  const Link = React.forwardRef<HTMLAnchorElement, any>(
    ({ href, children, ...props }, ref) => (
      <a ref={ref} href={typeof href === "string" ? href : href?.pathname || "#"} {...props}>
        {children}
      </a>
    )
  )
  Link.displayName = "Link"
  return {
    __esModule: true,
    default: Link,
  }
})

describe("MobileBottomNav", () => {
  beforeEach(() => {
    mockUsePathname.mockReset()
  })

  it("highlights the active quick access item", () => {
    mockUsePathname.mockImplementation(() => "/alerts")

    render(<MobileBottomNav />)

    const nav = screen.getByLabelText("תפריט ניווט תחתון")
    const alertsLink = within(nav).getByRole("link", { name: "התראות" })

    expect(alertsLink).toHaveAttribute("aria-current", "page")
    expect(within(nav).getAllByRole("link")).toHaveLength(4)
  })
})
