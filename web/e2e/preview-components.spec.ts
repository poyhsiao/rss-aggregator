import { test, expect } from '@playwright/test'

/**
 * E2E BDD tests for preview components rendered inside RssPreviewDialog.
 *
 * RssPreviewDialog is opened from the History page by clicking the FileText
 * (preview) button on a batch card. It offers three format tabs:
 *   RSS  → RssXmlPreview  (xml-tag-name, xml-attr-name, xml-tag-bracket)
 *   JSON → JsonPreview    (hljs-attr, json-key, json-string …)
 *   MD   → MarkdownPreview (prose preview / source toggle)
 *
 * Each preview uses PreviewContainer which wraps content in .code-content.
 * Line numbers are provided via .code-line-number spans.
 */
test.describe('Preview Components — RSS/XML / JSON / Markdown', () => {
  // -----------------------------------------------------------------------
  // Helper: open the RssPreviewDialog from the history page
  // -----------------------------------------------------------------------
  async function openRssPreviewDialog(page: import('@playwright/test').Page): Promise<boolean> {
    await page.goto('/history')
    await page.waitForLoadState('networkidle')

    const batchCards = page.locator('[class*="bg-white"][class*="rounded-xl"]')
    const count = await batchCards.count()

    // Skip test if no data - this is acceptable in CI with fresh DB
    if (count === 0) {
      return false
    }

    // Click the purple FileText (preview) button on the first batch card
    const previewBtn = batchCards
      .first()
      .getByRole('button')
      .filter({ has: page.locator('svg.h-4.w-4.text-purple-500') })
      .first()

    await previewBtn.click()
    await page.waitForTimeout(800)

    // RssPreviewDialog renders as a fixed overlay
    const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
    const isVisible = await dialog.isVisible().catch(() => false)
    return isVisible
  }

  // -----------------------------------------------------------------------
  // Helper: close the currently-open RssPreviewDialog
  // -----------------------------------------------------------------------
  async function closeDialog(page: import('@playwright/test').Page): Promise<void> {
    const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
    // The close button is a button containing an X (close) icon in the header
    // Use aria-label or icon class to be specific
    const closeBtn = dialog.locator('button').filter({ has: page.locator('svg.h-5.w-5') }).first()
    await closeBtn.click()
    await page.waitForTimeout(1000)
    await expect(dialog).not.toBeVisible({ timeout: 5000 })
  }

  // =======================================================================
  // RSS / XML Preview
  // =======================================================================
  test.describe('RSS/XML Preview (RssXmlPreview)', () => {
    let dialogOpened = false

    test.beforeEach(async ({ page }) => {
      dialogOpened = await openRssPreviewDialog(page)
      if (!dialogOpened) {
        test.skip()
      }
    })

    test.afterEach(async ({ page }) => {
      if (dialogOpened) {
        await closeDialog(page)
      }
    })

    test('dialog opens with RSS tab selected by default', async ({ page }) => {
      const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
      // RSS button should be "active" (has light/dark background class)
      // Use .first() because /rss/i matches both "RSS" tab and "Download RSS" button
      const rssBtn = dialog.getByRole('button', { name: /rss/i }).first()
      await expect(rssBtn).toBeVisible()
      await expect(rssBtn).toHaveClass(/bg-white|bg-slate-700/)
    })

    test('XML content is syntax highlighted with xml-* classes', async ({ page }) => {
      const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
      // Wait for content to load
      await page.waitForTimeout(1500)

      // RssXmlPreview renders inside .code-content
      const codeContent = dialog.locator('.code-content')
      await expect(codeContent).toBeVisible({ timeout: 8000 })

      // Should contain XML syntax highlighting classes
      const html = await codeContent.innerHTML()
      const hasXmlHighlighting =
        html.includes('xml-tag-name') ||
        html.includes('xml-tag-bracket') ||
        html.includes('xml-attr-name')
      expect(hasXmlHighlighting).toBe(true)
    })

    test('XML content has line numbers', async ({ page }) => {
      const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
      await page.waitForTimeout(1500)

      const codeContent = dialog.locator('.code-content')
      const html = await codeContent.innerHTML()
      expect(html).toContain('code-line-number')
    })
  })

  // =======================================================================
  // JSON Preview
  // =======================================================================
  test.describe('JSON Preview (JsonPreview)', () => {
    let dialogOpened = false

    test.beforeEach(async ({ page }) => {
      dialogOpened = await openRssPreviewDialog(page)
      if (!dialogOpened) {
        test.skip()
      }
    })

    test.afterEach(async ({ page }) => {
      if (dialogOpened) {
        await closeDialog(page)
      }
    })

    test('can switch to JSON tab', async ({ page }) => {
      const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
      const jsonBtn = dialog.getByRole('button', { name: /json/i })
      await jsonBtn.click()
      await page.waitForTimeout(1000)

      // JSON content container should become visible
      const codeContent = dialog.locator('.code-content')
      await expect(codeContent).toBeVisible({ timeout: 8000 })
    })

    test('JSON content is syntax highlighted with json-* or hljs-* classes', async ({ page }) => {
      const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')

      // Switch to JSON tab
      await dialog.getByRole('button', { name: /json/i }).click()
      await page.waitForTimeout(2000)

      const codeContent = dialog.locator('.code-content')
      await expect(codeContent).toBeVisible({ timeout: 8000 })

      const html = await codeContent.innerHTML()
      const hasJsonHighlighting =
        html.includes('hljs-attr') ||
        html.includes('json-key') ||
        html.includes('json-string') ||
        html.includes('json-number')
      expect(hasJsonHighlighting).toBe(true)
    })

    test('JSON content has line numbers', async ({ page }) => {
      const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')

      // Switch to JSON tab
      await dialog.getByRole('button', { name: /json/i }).click()
      await page.waitForTimeout(2000)

      const codeContent = dialog.locator('.code-content')
      const html = await codeContent.innerHTML()
      expect(html).toContain('code-line-number')
    })
  })

  // =======================================================================
  // Markdown Preview
  // =======================================================================
  test.describe('Markdown Preview (MarkdownPreview)', () => {
    let dialogOpened = false

    test.beforeEach(async ({ page }) => {
      dialogOpened = await openRssPreviewDialog(page)
      if (!dialogOpened) {
        test.skip()
      }
    })

    test.afterEach(async ({ page }) => {
      if (dialogOpened) {
        await closeDialog(page)
      }
    })

    test('can switch to Markdown tab', async ({ page }) => {
      const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
      // Use .first() because /markdown/i matches both "Markdown" tab and "Download Markdown" button
      const mdBtn = dialog.getByRole('button', { name: /markdown/i }).first()
      await mdBtn.click()
      await page.waitForTimeout(1000)

      // Markdown tab button should be active
      await expect(mdBtn).toHaveClass(/bg-white|bg-slate-700/)
    })

    test('default view is preview mode (rendered prose)', async ({ page }) => {
      const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')

      // Switch to Markdown tab
      const mdBtn = dialog.getByRole('button', { name: /markdown/i }).first()
      await mdBtn.click()
      await page.waitForTimeout(1000)

      // Default should be preview (prose div visible, source div hidden)
      // The preview pane has class "prose prose-slate dark:prose-invert"
      const proseContent = dialog.locator('.prose, [class*="prose"]')
      await expect(proseContent.first()).toBeVisible({ timeout: 5000 })
    })

    test('can switch to source view', async ({ page }) => {
      const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')

      // Switch to Markdown tab
      const mdBtn = dialog.getByRole('button', { name: /markdown/i }).first()
      await mdBtn.click()
      await page.waitForTimeout(1000)

      // Click "Source" button (Code icon) - use exact match to avoid "Download Markdown"
      const sourceBtn = dialog.getByRole('button', { name: 'Source' }).first()
      await sourceBtn.click()
      await page.waitForTimeout(500)

      // Source view should contain md-header class (from highlightMarkdownSource)
      const html = await dialog.locator('.code-content').innerHTML()
      const hasSourceHighlighting =
        html.includes('md-header') ||
        html.includes('md-bold') ||
        html.includes('md-italic')
      expect(hasSourceHighlighting).toBe(true)
    })

    test('can switch back to preview view from source', async ({ page }) => {
      const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')

      // Switch to Markdown tab
      const mdBtn = dialog.getByRole('button', { name: /markdown/i }).first()
      await mdBtn.click()
      await page.waitForTimeout(1000)

      // Switch to source
      const sourceBtn = dialog.getByRole('button', { name: 'Source' }).first()
      await sourceBtn.click()
      await page.waitForTimeout(500)

      // Switch back to preview
      const previewBtn = dialog.getByRole('button', { name: 'Preview' }).first()
      await previewBtn.click()
      await page.waitForTimeout(500)

      // Prose content should be visible again
      const proseContent = dialog.locator('.prose, [class*="prose"]')
      await expect(proseContent.first()).toBeVisible({ timeout: 5000 })
    })
  })

  // =======================================================================
  // Copy / Download buttons (sanity check)
  // =======================================================================
  test.describe('RssPreviewDialog actions', () => {
    let dialogOpened = false

    test.beforeEach(async ({ page }) => {
      dialogOpened = await openRssPreviewDialog(page)
      if (!dialogOpened) {
        test.skip()
      }
    })

    test.afterEach(async ({ page }) => {
      if (dialogOpened) {
        await closeDialog(page)
      }
    })

    test('copy button is visible', async ({ page }) => {
      const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
      const copyBtn = dialog.getByRole('button', { name: /copy/i })
      await expect(copyBtn).toBeVisible()
    })

    test('download button is visible', async ({ page }) => {
      const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
      const downloadBtn = dialog.getByRole('button', { name: /download/i })
      await expect(downloadBtn).toBeVisible()
    })
  })
})
