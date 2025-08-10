import { test, expect } from '@playwright/test';
import { loginUser, uploadReceipt, waitForReceiptProcessing } from './utils/test-utils';

test.describe('JPG Upload to Cloudinary Flow', () => {
  test('should upload JPG receipt and process with Cloudinary', async ({ page }) => {
    // Login
    await loginUser(page, 'test@example.com', 'password123');
    
    // Upload JPG receipt
    await uploadReceipt(page, './sampleReceipts/test-receipt.jpg');
    
    // Wait for processing and verify Cloudinary storage
    await page.waitForSelector('[data-testid=storage-provider]');
    const storageProvider = await page.locator('[data-testid=storage-provider]').textContent();
    expect(storageProvider).toContain('cloudinary');
    
    // Verify Cloudinary ID is present
    await expect(page.locator('[data-testid=cloudinary-id]')).toBeVisible();
    
    // Test reprocess functionality
    await page.click('[data-testid=reprocess-paddle-button]');
    await page.waitForSelector('[data-testid=reprocess-success]', { timeout: 30000 });
    
    // Verify telemetry is preserved
    await expect(page.locator('[data-testid=needs-review]')).toBeVisible();
    await expect(page.locator('[data-testid=ocr-latency]')).toBeVisible();
  });
});
