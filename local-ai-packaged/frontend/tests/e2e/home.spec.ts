import { test, expect } from '@playwright/test';

test('Home page loads and shows links', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Welcome to Local AI Packaged' })).toBeVisible();
  await expect(page.getByText('Backend:')).toBeVisible();
  await expect(page.getByText('http://localhost:8000')).toBeVisible();
});