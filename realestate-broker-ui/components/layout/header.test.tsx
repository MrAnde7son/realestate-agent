/**
 * @vitest-environment jsdom
 */

import React from "react"
import { fireEvent, render, screen } from "@testing-library/react"
import "@testing-library/jest-dom"
import { vi, describe, it, expect } from "vitest"

import Header from "./header"

const mockLogout = vi.fn()

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({
    user: {
      role: "broker",
      first_name: "Test",
      last_name: "User",
      email: "test@example.com",
    },
    logout: mockLogout,
    isAuthenticated: true,
    isLoading: false,
  }),
}))

vi.mock("@/lib/navigation-state", async () => {
  const actual = await vi.importActual<typeof import("@/lib/navigation-state")>(
    "@/lib/navigation-state"
  )

  return {
    __esModule: true,
    ...actual,
    usePersistentPathname: () => "/assets",
  }
})

vi.mock("./global-search", () => ({
  GlobalSearch: () => <div data-testid="global-search" />,
}))

vi.mock("@/components/ui/theme-toggle", () => ({
  ThemeToggle: () => <button type="button">Theme</button>,
}))

vi.mock("@/components/Logo", () => ({
  __esModule: true,
  default: () => <div data-testid="logo" />,
}))

vi.mock("next/link", () => {
  const Link = React.forwardRef<HTMLAnchorElement, any>(({ href, children, ...props }, ref) => (
    <a ref={ref} href={typeof href === "string" ? href : href?.pathname || "#"} {...props}>
      {children}
    </a>
  ))
  Link.displayName = "Link"
  return {
    __esModule: true,
    default: Link,
  }
})

describe("Header mobile navigation", () => {
  it("relies on the sheet close control when the sheet is open", async () => {
    render(<Header />)

    fireEvent.click(screen.getByLabelText("פתח תפריט ניווט"))

    const closeButtons = await screen.findAllByRole("button", { name: /close/i })
    expect(closeButtons).toHaveLength(1)
    expect(screen.queryByLabelText("סגור תפריט")).not.toBeInTheDocument()
  })
})
