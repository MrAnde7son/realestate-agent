/**
 * @vitest-environment jsdom
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { vi } from "vitest";

import AppSidebar from "@/components/layout/app-sidebar";

const mockLogout = vi.fn();

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
  usePathname: () => "/assets",
}));

vi.mock("next/link", () => ({
  __esModule: true,
  default: ({ href, children, ...props }: any) => (
    <a href={typeof href === "string" ? href : href?.pathname || "#"} {...props}>
      {children}
    </a>
  ),
}));

describe("AppSidebar accessibility when collapsed", () => {
  beforeEach(() => {
    mockLogout.mockClear();
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

