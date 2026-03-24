import { Page, Locator, expect } from '@playwright/test'

export class BasePage {
  readonly page: Page

  constructor(page: Page) {
    this.page = page
  }

  async goto(path: string = '/') {
    await this.page.goto(path)
  }

  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle')
  }

  async getToastMessage(): Promise<string | null> {
    const toast = this.page.locator('[role="alert"]').first()
    return toast.isVisible() ? await toast.textContent() : null
  }

  async clickNavMenu(menuKey: string) {
    await this.page.getByRole('link', { name: new RegExp(menuKey, 'i') }).click()
  }

  async switchLanguage(lang: 'en' | 'zh') {
    await this.page.getByRole('button', { name: /language|語言/i }).click()
    await this.page.getByRole('menuitem', { name: lang === 'en' ? /english/i : /中文/i }).click()
  }

  async confirmDialog() {
    this.page.once('dialog', async dialog => {
      await dialog.accept()
    })
  }
}

export class SourcesPage extends BasePage {
  readonly addButton: Locator
  readonly refreshAllButton: Locator
  readonly sourceCards: Locator
  readonly dialog: Locator
  readonly nameInput: Locator
  readonly urlInput: Locator
  readonly saveButton: Locator
  readonly cancelButton: Locator

  constructor(page: Page) {
    super(page)
    this.addButton = page.getByRole('button', { name: /add|新增/i })
    this.refreshAllButton = page.getByRole('button', { name: /refresh all|重新整理/i })
    this.sourceCards = page.locator('[class*="bg-white"][class*="rounded-xl"]')
    this.dialog = page.locator('[class*="rounded-2xl"]').filter({ has: page.getByRole('heading', { level: 2 }) })
    this.nameInput = page.getByPlaceholder(/enter source name/i)
    this.urlInput = page.getByPlaceholder(/enter rss url/i)
    // Use more specific selector - find the button inside the dialog
    this.saveButton = this.dialog.getByRole('button', { name: /^confirm$/i })
    this.cancelButton = this.dialog.getByRole('button', { name: /cancel/i })
  }

  async goto() {
    await super.goto('/sources')
    await this.waitForPageLoad()
  }

  async getSourceCardByName(name: string): Promise<Locator> {
    return this.page.locator('[class*="bg-white"][class*="rounded-xl"]').filter({
      hasText: name
    })
  }

  async getSourceCount(): Promise<number> {
    return await this.sourceCards.count()
  }

  async createSource(name: string, url: string) {
    await this.addButton.click()
    
    const dialog = this.page.locator('[class*="rounded-2xl"]').filter({ has: this.page.getByRole('heading', { level: 2 }) })
    await dialog.waitFor({ state: 'visible', timeout: 5000 })
    await this.page.waitForTimeout(300)
    
    const nameInput = this.page.getByPlaceholder(/enter source name/i)
    const urlInput = this.page.getByPlaceholder(/enter rss url/i)
    await nameInput.fill(name)
    await urlInput.fill(url)
    
    const saveBtn = dialog.getByRole('button', { name: /^confirm$/i })
    await saveBtn.click()
    
    await dialog.waitFor({ state: 'hidden', timeout: 15000 })
    await this.page.waitForTimeout(500)
  }

  async editSource(oldName: string, newName: string) {
    const card = await this.getSourceCardByName(oldName)
    await card.getByRole('button', { name: '✏️' }).click()
    
    const dialog = this.page.locator('[class*="rounded-2xl"]').filter({ has: this.page.getByRole('heading', { level: 2 }) })
    await dialog.waitFor({ state: 'visible', timeout: 5000 })
    await this.page.waitForTimeout(300)
    
    const nameInput = this.page.getByPlaceholder(/enter source name/i)
    await nameInput.clear()
    await nameInput.fill(newName)
    
    const saveBtn = dialog.getByRole('button', { name: /^confirm$/i })
    await saveBtn.click()
    
    await dialog.waitFor({ state: 'hidden', timeout: 15000 })
    await this.page.waitForTimeout(500)
  }

  async deleteSource(name: string) {
    const card = await this.getSourceCardByName(name)
    this.page.once('dialog', async dialog => {
      await dialog.accept()
    })
    await card.getByRole('button', { name: '🗑️' }).click()
    await this.page.waitForLoadState('networkidle')
    await this.page.waitForTimeout(500)
  }

  async refreshSource(name: string) {
    const card = await this.getSourceCardByName(name)
    await card.getByRole('button').filter({ hasText: /refresh|重新整理/i }).first().click()
    await this.page.waitForTimeout(1000)
  }

  async refreshAllSources() {
    await this.refreshAllButton.click()
    await this.page.waitForTimeout(2000)
  }

  async viewSourceFeed(name: string) {
    const card = await this.getSourceCardByName(name)
    await card.getByRole('button').filter({ hasText: /view|查看|filetext/i }).first().click()
  }

  async sourceExists(name: string): Promise<boolean> {
    const card = await this.getSourceCardByName(name)
    return await card.isVisible()
  }
}

export class FeedPage extends BasePage {
  readonly formatSelect: Locator
  readonly sortBySelect: Locator
  readonly sortOrderSelect: Locator
  readonly feedItems: Locator
  readonly downloadButton: Locator

  constructor(page: Page) {
    super(page)
    this.formatSelect = page.getByLabel(/format|格式/i)
    this.sortBySelect = page.getByLabel(/sort by|排序/i)
    this.sortOrderSelect = page.getByLabel(/order|順序/i)
    this.feedItems = page.locator('[class*="prose"]')
    this.downloadButton = page.getByRole('button', { name: /download|下載/i })
  }

  async goto() {
    await super.goto('/feed')
    await this.waitForPageLoad()
  }

  async selectFormat(format: string) {
    await this.formatSelect.selectOption(format)
  }

  async selectSortBy(sortBy: string) {
    await this.sortBySelect.selectOption(sortBy)
  }

  async selectSortOrder(order: string) {
    await this.sortOrderSelect.selectOption(order)
  }

  async getFeedContent(): Promise<string> {
    return await this.page.locator('body').innerText()
  }

  async downloadFeed() {
    const [download] = await Promise.all([
      this.page.waitForEvent('download'),
      this.downloadButton.click()
    ])
    return download
  }
}

export class HistoryPage extends BasePage {
  readonly batchCards: Locator

  constructor(page: Page) {
    super(page)
    this.batchCards = page.locator('[class*="bg-white"][class*="rounded-xl"]')
  }

  async goto() {
    await super.goto('/history')
    await this.waitForPageLoad()
  }

  async getBatchCount(): Promise<number> {
    return await this.batchCards.count()
  }

  async getBatchByIndex(index: number): Promise<Locator> {
    return this.batchCards.nth(index)
  }

  async clickBatch(index: number) {
    await this.batchCards.nth(index).click()
    await this.page.waitForTimeout(500)
  }

  async getBatchItems(): Promise<Locator[]> {
    const items = await this.page.locator('[class*="prose"] [class*="border"]').all()
    return items
  }
}

export class KeysPage extends BasePage {
  readonly addButton: Locator
  readonly keyCards: Locator
  readonly dialog: Locator
  readonly nameInput: Locator
  readonly saveButton: Locator

  constructor(page: Page) {
    super(page)
    this.addButton = page.getByRole('button', { name: /add|新增/i })
    this.keyCards = page.locator('[class*="bg-white"][class*="rounded-xl"]')
    this.dialog = page.locator('[class*="rounded-2xl"]').filter({ has: page.getByRole('heading', { level: 2 }) })
    this.nameInput = page.getByPlaceholder(/enter a name to identify this key/i)
    this.saveButton = this.dialog.getByRole('button', { name: /^confirm$/i })
  }

  async goto() {
    await super.goto('/keys')
    await this.waitForPageLoad()
  }

  async getKeyCount(): Promise<number> {
    return await this.keyCards.count()
  }

  async createKey(name: string) {
    await this.addButton.click()
    
    const dialog = this.page.locator('[class*="rounded-2xl"]').filter({ has: this.page.getByRole('heading', { level: 2 }) })
    await dialog.waitFor({ state: 'visible', timeout: 5000 })
    await this.page.waitForTimeout(300)
    
    const nameInput = this.page.getByPlaceholder(/enter a name to identify this key/i)
    await nameInput.fill(name)
    
    const confirmBtn = dialog.getByRole('button', { name: /^confirm$/i })
    await confirmBtn.click()
    
    await this.page.waitForTimeout(1500)
    
    const closeBtn = dialog.getByRole('button', { name: /^confirm$/i })
    await closeBtn.click()
    
    await dialog.waitFor({ state: 'hidden', timeout: 15000 })
    await this.page.waitForTimeout(500)
  }

  async deleteKey(name: string) {
    const card = this.keyCards.filter({ hasText: name })
    this.page.once('dialog', async dialog => {
      await dialog.accept()
    })
    await card.getByRole('button', { name: /delete|刪除/i }).click()
    await this.page.waitForLoadState('networkidle')
    await this.page.waitForTimeout(500)
  }

  async copyKey(name: string) {
    const card = this.keyCards.filter({ hasText: name })
    await card.getByRole('button').filter({ hasText: /copy|複製/i }).first().click()
  }

  async keyExists(name: string): Promise<boolean> {
    const card = this.keyCards.filter({ hasText: name })
    return await card.isVisible()
  }
}

export class StatsPage extends BasePage {
  readonly chart: Locator
  readonly daysSelect: Locator

  constructor(page: Page) {
    super(page)
    this.chart = page.locator('canvas')
    this.daysSelect = page.getByLabel(/days|天數/i)
  }

  async goto() {
    await super.goto('/stats')
    await this.waitForPageLoad()
  }

  async selectDays(days: number) {
    await this.daysSelect.selectOption(String(days))
  }

  async isChartVisible(): Promise<boolean> {
    return await this.chart.isVisible()
  }
}

export class LogsPage extends BasePage {
  readonly logCards: Locator
  readonly clearButton: Locator

  constructor(page: Page) {
    super(page)
    this.logCards = page.locator('[class*="bg-white"][class*="rounded-xl"]')
    this.clearButton = page.getByRole('button', { name: /clear|清除/i })
  }

  async goto() {
    await super.goto('/logs')
    await this.waitForPageLoad()
  }

  async getLogCount(): Promise<number> {
    return await this.logCards.count()
  }

  async clearLogs() {
    this.page.once('dialog', async dialog => {
      await dialog.accept()
    })
    await this.clearButton.click()
    await this.waitForPageLoad()
  }
}