import { test, expect } from "@playwright/test"

test("admin can manage users when backend is available", async ({ page }) => {
  await page.route("**/admin/users", async (route) => {
    if (route.request().resourceType() === "document") {
      const headers = {
        ...route.request().headers(),
        "x-test-skip-admin": "true",
      }
      await route.continue({ headers })
    } else {
      await route.continue()
    }
  })

  type User = {
    id: number
    email: string
    username: string
    first_name: string
    last_name: string
    full_name: string
    role: "admin" | "broker" | "appraiser" | "investor" | "viewer"
    phone_number: string | null
    company: string | null
    organization_name: string
    is_active: boolean
    status: "active" | "inactive"
    created_at: string
    updated_at: string
    last_login: string | null
  }

  const users: User[] = [
    {
      id: 1,
      email: "admin@example.com",
      username: "admin",
      first_name: "Admin",
      last_name: "User",
      full_name: "Admin User",
      role: "admin",
      phone_number: "+97250000000",
      company: "Nadlaner",
      organization_name: "Nadlaner",
      is_active: true,
      status: "active",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_login: new Date().toISOString(),
    },
  ]

  let nextId = 2

  await page.route("**/api/admin/users/**", async (route) => {
    const url = new URL(route.request().url)
    const method = route.request().method()

    if (method === "GET") {
      const pageParam = Number(url.searchParams.get("page") || "1")
      const pageSize = Number(url.searchParams.get("page_size") || "10")
      const start = (pageParam - 1) * pageSize
      const paginated = users.slice(start, start + pageSize)
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: paginated,
          pagination: {
            count: users.length,
            page: pageParam,
            page_size: pageSize,
            total_pages: Math.max(1, Math.ceil(users.length / pageSize)),
          },
        }),
      })
      return
    }

    if (method === "POST" && url.pathname.endsWith("/reset-password/")) {
      const userId = Number(url.pathname.split("/").slice(-2)[0])
      const user = users.find((u) => u.id === userId)
      if (!user) {
        await route.fulfill({ status: 404, body: JSON.stringify({ error: "Not found" }) })
        return
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: { ...user, temporary_password: "TempPass!23" } }),
      })
      return
    }

    if (method === "POST" && url.pathname.endsWith("/deactivate/")) {
      const userId = Number(url.pathname.split("/").slice(-2)[0])
      const user = users.find((u) => u.id === userId)
      if (user) {
        user.is_active = false
        user.status = "inactive"
        user.updated_at = new Date().toISOString()
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: user }),
      })
      return
    }

    if (method === "POST" && url.pathname.endsWith("/activate/")) {
      const userId = Number(url.pathname.split("/").slice(-2)[0])
      const user = users.find((u) => u.id === userId)
      if (user) {
        user.is_active = true
        user.status = "active"
        user.updated_at = new Date().toISOString()
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: user }),
      })
      return
    }

    if (method === "POST") {
      const payload = await route.request().postDataJSON()
      const created: User = {
        id: nextId++,
        email: payload.email,
        username: payload.email,
        first_name: payload.first_name || "",
        last_name: payload.last_name || "",
        full_name: `${payload.first_name || ""} ${payload.last_name || ""}`.trim() || payload.email,
        role: payload.role,
        phone_number: payload.phone_number || null,
        company: payload.company || null,
        organization_name: payload.organization_name || "",
        is_active: payload.is_active ?? true,
        status: (payload.is_active ?? true) ? "active" : "inactive",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        last_login: null,
      }
      users.push(created)
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({ data: { ...created, temporary_password: "TempPass!23" } }),
      })
      return
    }

    if (method === "PATCH") {
      const payload = await route.request().postDataJSON()
      const userId = Number(url.pathname.split("/").slice(-2)[0])
      const user = users.find((u) => u.id === userId)
      if (user) {
        Object.assign(user, payload)
        user.full_name = `${user.first_name || ""} ${user.last_name || ""}`.trim() || user.email
        user.updated_at = new Date().toISOString()
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: user }),
      })
      return
    }

    if (method === "DELETE") {
      const userId = Number(url.pathname.split("/").slice(-2)[0])
      const index = users.findIndex((u) => u.id === userId)
      if (index >= 0) {
        users.splice(index, 1)
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ message: "User deleted" }),
      })
      return
    }

    await route.fallback()
  })

  try {
    await page.goto("http://localhost:3000/admin/users", { timeout: 2000 })
  } catch (error) {
    test.skip(true, "frontend not running")
    return
  }

  await expect(page.getByRole("heading", { name: "ניהול משתמשים" })).toBeVisible()
  await expect(page.getByText("Admin User")).toBeVisible()

  await page.getByRole("button", { name: "הוסף משתמש" }).click()
  await page.getByLabel("שם פרטי").fill("Dana")
  await page.getByLabel("שם משפחה").fill("Levi")
  await page.getByLabel("דוא״ל").fill("dana@example.com")
  await page.getByLabel("טלפון").fill("+97250000001")
  await page.getByLabel("ארגון").fill("Acme")
  await page.getByRole("button", { name: "הוסף משתמש" }).click()

  await expect(page.getByText("Dana Levi")).toBeVisible()

  const danaRow = page.getByRole("row", { name: /Dana Levi/ })
  await danaRow.getByRole("combobox").click()
  await page.getByRole("option", { name: "שמאי" }).click()

  const actionsTrigger = danaRow.locator('button[aria-haspopup="menu"]')
  await actionsTrigger.click()
  await page.getByRole("menuitem", { name: "השבתה" }).click()
  await expect(danaRow.getByText("מושבת")).toBeVisible()

  await actionsTrigger.click()
  await page.getByRole("menuitem", { name: "איפוס סיסמה" }).click()
  await expect(page.getByText("הסיסמה אופסה")).toBeVisible()

  await actionsTrigger.click()
  await page.getByRole("menuitem", { name: "מחיקה" }).click()
  await page.getByRole("button", { name: "מחיקה" }).click()
  await expect(page.getByText("Dana Levi")).toHaveCount(0)
})
