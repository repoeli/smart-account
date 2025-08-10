import { test, expect, Page } from '@playwright/test';

export async function loginUser(page: Page, email: string, password: string) {
  await page.goto('/login');
  await page.fill('[data-testid=email-input]', email);
  await page.fill('[data-testid=password-input]', password);
  await page.click('[data-testid=login-button]');
  await page.waitForURL('/dashboard');
}

export async function uploadReceipt(page: Page, filePath: string) {
  await page.goto('/receipts/upload');
  const fileInput = page.locator('[data-testid=file-input]');
  await fileInput.setInputFiles(filePath);
  await page.click('[data-testid=upload-button]');
  await page.waitForSelector('[data-testid=upload-success]', { timeout: 30000 });
}

export async function waitForReceiptProcessing(page: Page, receiptId: string) {
  await page.goto(/receipts/);
  await page.waitForSelector('[data-testid=receipt-processed]', { timeout: 60000 });
}
