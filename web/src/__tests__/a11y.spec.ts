import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { join } from 'path';

const webSrc = join(__dirname, '..');

describe('accessibility attributes', () => {
  it('LogCard expand/collapse button should have aria-expanded and aria-controls', () => {
    const logCardPath = join(webSrc, 'components/LogCard.vue');
    const content = readFileSync(logCardPath, 'utf-8');
    expect(content).toContain(':aria-expanded');
    expect(content).toContain('aria-controls="log-content"');
  });

  it('HistoryPage batch expand/collapse button should have aria-expanded and aria-controls', () => {
    const historyPagePath = join(webSrc, 'pages/HistoryPage.vue');
    const content = readFileSync(historyPagePath, 'utf-8');
    expect(content).toContain(':aria-expanded');
    expect(content).toContain('aria-controls');
  });

  it('ConfirmDialog buttons should have type="button" and aria-label', () => {
    const dialogPath = join(webSrc, 'components/ui/ConfirmDialog.vue');
    const content = readFileSync(dialogPath, 'utf-8');
    expect(content).toContain('type="button"');
    expect(content).toContain(':aria-label=');
  });

  it('Button component should support aria-label prop', () => {
    const buttonPath = join(webSrc, 'components/ui/Button.vue');
    const content = readFileSync(buttonPath, 'utf-8');
    expect(content).toContain(':aria-label=');
  });
});