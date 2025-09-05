import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: '__tests__',
  testMatch: /.*\.spec\.ts/,
  use: {
    baseURL: 'http://localhost:3000',
  },
})
