import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  // Pre-seed tokens so authGuard lets us into the settings route without a real login
  await page.addInitScript(() => {
    localStorage.setItem('wk_access_token', 'playwright-access');
    localStorage.setItem('wk_refresh_token', 'playwright-refresh');
  });

  const baseSettings = {
    ui_mode: 'dark',
    nd_options: {
      low_stim_mode: false,
      concise_recap: false,
      decision_menu_mode: false,
      dyslexia_font: false,
      font_size: 'medium',
      line_spacing: 'standard',
    },
    safety_defaults: { content_rating: 'PG13' },
    endpoint_pref: {
      provider: 'openai',
      base_url: 'https://api.openai.com/v1',
      compatibility: 'openai',
      model: '',
      manual: false,
    },
    endpoint_has_api_key: false,
  };

  await page.route('**/api/auth/settings/', route => {
    if (route.request().method() === 'GET') {
      return route.fulfill({ status: 200, json: baseSettings });
    }

    const body = route.request().postDataJSON() as Record<string, unknown>;
    const updated = { ...baseSettings, ...body, endpoint_has_api_key: true };
    return route.fulfill({ status: 200, json: updated });
  });

  await page.route('**/api/llm/validate/', route => {
    return route.fulfill({
      status: 200,
      json: {
        success: true,
        message: 'Endpoint verified and settings saved.',
        models: ['gpt-4o'],
        resolved_base_url: 'https://api.openai.com/v1',
        compatibility: 'openai',
        has_api_key: true,
      },
    });
  });
});

test('settings panel exposes endpoint controls', async ({ page }) => {
  const response = await page.goto('/settings').catch(() => null);

  if (!response || response.status() >= 400) {
    test.skip('App server not running; skipping Playwright settings smoke test.');
  }

  await expect(page.getByText('LLM Endpoint Preference')).toBeVisible();
  await expect(page.getByLabel('API key', { exact: true })).toBeVisible();
  await expect(page.getByLabel(/Provider/i)).toBeVisible();
  await expect(page.getByText(/API-provided models/i)).toBeVisible();
  await expect(page.getByText(/Custom model name/i)).toBeVisible();
});

test('saving endpoint locks API key input and shows success copy', async ({ page }) => {
  const response = await page.goto('/settings').catch(() => null);

  if (!response || response.status() >= 400) {
    test.skip('App server not running; skipping Playwright settings save flow test.');
  }

  await page.getByLabel('API key', { exact: true }).fill('sk-test-123');
  await page.getByRole('radio', { name: 'Custom model name' }).check();
  await page.getByPlaceholder('e.g., gpt-4o, claude-3-opus, llama3-70b').fill('gpt-4o');
  await page.getByRole('button', { name: 'Test & Save preference' }).click();

  await expect(page.getByText('Endpoint verified and settings saved.')).toBeVisible();
  await expect(page.getByLabel('API key', { exact: true })).toBeDisabled();
  await expect(page.getByRole('button', { name: /Enter new key/i })).toBeVisible();
});
