import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: 'html',
  timeout: 120000,
  expect: {
    timeout: 20000,
  },
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:51086',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    /* Ensure each test starts with clean storage state */
    storageState: process.env.CI ? undefined : undefined,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      /* Per-project storage state for isolation */
    },
  ],
  webServer: process.env.CI ? undefined : {
    command: 'echo "Using existing server"',
    url: 'http://localhost:51086',
    reuseExistingServer: true,
    timeout: 5000,
  },
})