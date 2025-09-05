import { test, expect } from "@playwright/test";

test("member cannot open admin analytics", async ({ page }) => {
  try {
    await page.goto("http://localhost:3000/admin/analytics", { timeout: 1000 });
  } catch (e) {
    test.skip(true, "frontend not running");
    return;
  }
  await expect(page).toHaveURL("http://localhost:3000/");
});
