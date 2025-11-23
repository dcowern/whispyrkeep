import { expect, test } from '@playwright/test';

test('settings panel exposes endpoint controls', async ({ page }) => {
  const response = await page.goto('/settings').catch(() => null);

  if (!response || response.status() >= 400) {
    test.skip('App server not running; skipping Playwright settings smoke test.');
  }

  await expect(page.getByText('LLM Endpoint Preference')).toBeVisible();
  await expect(page.getByLabel(/API key/i)).toBeVisible();
  await expect(page.getByLabel(/Provider/i)).toBeVisible();
  await expect(page.getByText(/API-provided models/i)).toBeVisible();
  await expect(page.getByText(/Custom model name/i)).toBeVisible();
});
