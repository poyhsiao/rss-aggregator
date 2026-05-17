/**
 * Global teardown to ensure cleanup after all E2E tests complete.
 * This runs once after all tests finish, regardless of pass/fail.
 * No browser launch needed — browsers are managed by Playwright per-test.
 */
export default async function globalTeardown(): Promise<void> {
  // Cleanup is handled automatically by Playwright's browser context management.
  // No additional browser instances should be launched here.
}