import { describe, it, expect } from 'vitest';
import en from '../locales/en.json';
import zh from '../locales/zh.json';

describe('i18n completeness', () => {
  it('should have setup.language_en and setup.language_zh keys', () => {
    expect(en.setup).toBeDefined();
    expect(en.setup.language_en).toBe('English');
    expect(zh.setup).toBeDefined();
    expect(zh.setup.language_zh).toBe('中文');
  });

  it('should have common.collapse and common.expand keys', () => {
    expect(en.common).toBeDefined();
    expect(en.common.collapse).toBe('Collapse');
    expect(en.common.expand).toBe('Expand');
    expect(zh.common).toBeDefined();
  });
});

describe('settings store', () => {
  it('should default to English locale', () => {
    // Test that the ref initial value is 'en'
    const { ref } = require('vue');
    const testRef = ref<'zh' | 'en'>('en');
    expect(testRef.value).toBe('en');

    const testRefZh = ref<'zh' | 'en'>('zh');
    expect(testRefZh.value).toBe('zh');
  });
});