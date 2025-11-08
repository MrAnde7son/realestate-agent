import { describe, expect, it } from "vitest";
import { getRouteMatchState, normalizePath } from "./navigation-state";

describe("normalizePath", () => {
  it("ensures a leading slash and removes trailing slashes", () => {
    expect(normalizePath("assets/")).toBe("/assets");
    expect(normalizePath("/assets/")).toBe("/assets");
    expect(normalizePath("/")).toBe("/");
  });

  it("strips query strings and hashes", () => {
    expect(normalizePath("/assets?tab=details")).toBe("/assets");
    expect(normalizePath("/assets/1#overview")).toBe("/assets/1");
  });
});

describe("getRouteMatchState", () => {
  it("identifies exact matches", () => {
    expect(getRouteMatchState("/assets", "/assets")).toBe("self");
  });

  it("identifies descendant matches", () => {
    expect(getRouteMatchState("/assets", "/assets/123")).toBe("descendant");
  });

  it("treats unmatched routes as inactive", () => {
    expect(getRouteMatchState("/assets", "/deals")).toBe("inactive");
  });
});
