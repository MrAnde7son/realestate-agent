import { test, expect } from "@playwright/test";

test("member cannot open admin analytics", async ({ page }) => {
  await page.goto("http://localhost:3000/admin/analytics");
  await expect(page).toHaveURL("http://localhost:3000/");
});
