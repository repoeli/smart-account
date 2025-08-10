import { test, expect } from '@playwright/test';
import { loginUser, uploadReceipt } from './utils/test-utils';

test.describe('Reprocess Migration to Cloudinary', () => {
  test('should migrate external receipt to Cloudinary on reprocess', async ({ page }) => {
    // Login
    await loginUser(page, 'test@example.com', 'password123');
    
    // Navigate to receipts list
    await page.goto('/receipts');
    
    // Find a receipt without Cloudinary telemetry
    const receiptWithoutCloudinary = page.locator('[data-testid=receipt-item]:not([data-testid=has-cloudinary])').first();
    await expect(receiptWithoutCloudinary).toBeVisible();
    
    // Click on the receipt to view details
    await receiptWithoutCloudinary.click();
    
    // Verify it doesn't have Cloudinary telemetry initially
    await expect(page.locator('[data-testid=storage-provider]')).toContainText('local');
    await expect(page.locator('[data-testid=cloudinary-id]')).not.toBeVisible();
    
    // Trigger reprocess
    await page.click('[data-testid=reprocess-paddle-button]');
    await page.waitForSelector('[data-testid=reprocess-success]', { timeout: 30000 });
    
    // Verify migration to Cloudinary
    await expect(page.locator('[data-testid=storage-provider]')).toContainText('cloudinary');
    await expect(page.locator('[data-testid=cloudinary-id]')).toBeVisible();
    
    // Verify telemetry is updated
    await expect(page.locator('[data-testid=needs-review]')).toBeVisible();
    await expect(page.locator('[data-testid=ocr-latency]')).toBeVisible();
  });
});
