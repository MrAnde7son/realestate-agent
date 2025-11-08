/**
 * @vitest-environment jsdom
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AppSidebar from "@/components/layout/app-sidebar";

const mockLogout = vi.fn();
let mockPathname = "/assets";

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
}));

vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname,
}));

vi.mock("next/link", () => {
  const Link = React.forwardRef<HTMLAnchorElement, any>(
    ({ href, children, ...props }, ref) => (
      <a ref={ref} href={typeof href === "string" ? href : href?.pathname || "#"} {...props}>
        {children}
      </a>
    )
  )
  Link.displayName = 'Link'
  return {
    __esModule: true,
    default: Link,
  }
});

describe("AppSidebar accessibility when collapsed", () => {
  beforeEach(() => {
    mockLogout.mockClear();
    mockPathname = "/assets";
    window.history.replaceState(null, "", mockPathname);
  });

  it("adds aria-labels and tooltips to collapsed navigation items", async () => {
    render(<AppSidebar isCollapsed />);

    const assetsLink = screen.getByRole("link", { name: "נכסים" });

    expect(assetsLink).toHaveAttribute("aria-label", "נכסים");
    expect(assetsLink.textContent?.trim()).toBe("");

    fireEvent.focus(assetsLink);
    fireEvent.pointerEnter(assetsLink);

    await waitFor(() => {
      expect(screen.getByRole("tooltip")).toHaveTextContent("נכסים");
    });
  });

  it("continues to show inline labels when expanded", () => {
    render(<AppSidebar isCollapsed={false} />);

    const assetsLink = screen.getByRole("link", { name: "נכסים" });
    expect(assetsLink).toHaveTextContent("נכסים");
    expect(assetsLink).not.toHaveAttribute("aria-label");
  });
});

describe("AppSidebar active navigation state", () => {
  beforeEach(() => {
    mockLogout.mockClear();
    mockPathname = "/assets";
    window.history.replaceState(null, "", mockPathname);
  });

  it("marks the exact route as active", async () => {
    render(<AppSidebar />);

    const assetsLink = screen.getByRole("link", { name: "נכסים" });

    await waitFor(() => {
      expect(assetsLink).toHaveAttribute("data-active-state", "self");
    });

    expect(assetsLink).toHaveAttribute("aria-current", "page");
    const indicator = assetsLink.querySelector("[data-active-indicator]");
    expect(indicator).not.toBeNull();
    expect(indicator?.className).toContain("opacity-100");
  });

  it("marks descendant routes with a parent indicator", async () => {
    mockPathname = "/assets/123";
    window.history.replaceState(null, "", mockPathname);

    render(<AppSidebar />);

    const assetsLink = screen.getByRole("link", { name: "נכסים" });

    await waitFor(() => {
      expect(assetsLink).toHaveAttribute("data-active-state", "descendant");
    });

    expect(assetsLink).toHaveAttribute("aria-current", "true");
    const indicator = assetsLink.querySelector("[data-active-indicator]");
    expect(indicator).not.toBeNull();
    expect(indicator?.className).toContain("opacity-60");
  });
});

