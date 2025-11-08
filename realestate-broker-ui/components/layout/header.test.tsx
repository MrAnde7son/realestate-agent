/**
 * @vitest-environment jsdom
 */

import React from "react"
import { render, screen, fireEvent } from "@testing-library/react"
import "@testing-library/jest-dom"
import { beforeEach, describe, expect, it, vi } from "vitest"

import Header from "@/components/layout/header"

const mockLogout = vi.fn()
const mockUsePathname = vi.fn()

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({
    user: {
      role: "broker",
      first_name: "Test",
      last_name: "User",
      email: "test@example.com",
    },
    logout: mockLogout,
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

vi.mock("@/components/Logo", () => ({
  __esModule: true,
  default: () => <div data-testid="logo">Logo</div>,
}))

vi.mock("@/components/layout/global-search", () => ({
  GlobalSearch: () => <div data-testid="global-search" />,
}))

vi.mock("@/components/ui/theme-toggle", () => ({
  ThemeToggle: () => <div data-testid="theme-toggle" />,
}))

describe("Header mobile navigation", () => {
  beforeEach(() => {
    mockUsePathname.mockReset()
    mockLogout.mockClear()
  })

  it("marks nested routes as active in the mobile navigation sheet", async () => {
    mockUsePathname.mockImplementation(() => "/assets/123")

    render(<Header />)

    const openMenuButton = screen.getByRole("button", { name: "פתח תפריט ניווט" })
    fireEvent.click(openMenuButton)

    const assetsLink = await screen.findByRole("link", { name: "נכסים" })
    expect(assetsLink).toHaveAttribute("aria-current", "page")
  })
})
