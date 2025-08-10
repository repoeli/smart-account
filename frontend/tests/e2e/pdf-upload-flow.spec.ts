import { test, expect } from '@playwright/test';
import { loginUser, uploadReceipt } from './utils/test-utils';

test.describe('PDF Upload Flow', () => {
  test('should upload PDF receipt and show PDF badge', async ({ page }) => {
    // Login
    await loginUser(page, 'test@example.com', 'password123');
    
    // Upload PDF receipt
    await uploadReceipt(page, './sampleReceipts/test-receipt.pdf');
    
    // Verify PDF badge is displayed
    await expect(page.locator('[data-testid=pdf-badge]')).toBeVisible();
    
    // Verify raw link is available
    await expect(page.locator('[data-testid=raw-link]')).toBeVisible();
    
    // Test raw link opens in new tab
    const rawLink = page.locator('[data-testid=raw-link]');
    await expect(rawLink).toHaveAttribute('target', '_blank');
    
    // Verify storage provider is local for PDFs
    await page.waitForSelector('[data-testid=storage-provider]');
    const storageProvider = await page.locator('[data-testid=storage-provider]').textContent();
    expect(storageProvider).toContain('local');
  });
});
