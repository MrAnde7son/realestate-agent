import { describe, expect, it } from "vitest";

const loadConfig = async () => {
  const module = await import("../next.config.mjs");
  return module.default;
};

describe("next.config.mjs", () => {
  it("allows image domains from Madlan processors", async () => {
    const nextConfig = await loadConfig();
    const remotePatterns = nextConfig.images?.remotePatterns || [];

    expect(remotePatterns).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ hostname: "images-processor.madlan.co.il" }),
        expect.objectContaining({ hostname: "images2.madlan.co.il" }),
      ])
    );
  });
});
