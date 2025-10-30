import { describe, expect, it, vi } from "vitest";

const redirectMock = vi.fn(() => {
  throw new Error("redirect");
});

vi.mock("next/navigation", () => ({
  redirect: redirectMock,
}));

describe("Home page redirect", () => {
  it("redirects to assets index", async () => {
    const { default: HomePage } = await import("@/app/page");
    expect(() => HomePage()).toThrowError();
    expect(redirectMock).toHaveBeenCalledWith("/assets");
  });
});
