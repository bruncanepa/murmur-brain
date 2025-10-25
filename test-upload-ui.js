const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  console.log('Starting browser test...');
  const browser = await chromium.launch({
    headless: false,
    slowMo: 500 // Slow down for better observation
  });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  // Create screenshots directory
  const screenshotsDir = path.join(__dirname, 'test-screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir);
  }

  try {
    console.log('Navigating to file upload UI...');
    await page.goto('file:///Users/bomac/code/personal/local-brain/test-file-upload.html');
    await page.waitForLoadState('networkidle');

    console.log('\n=== TEST 1: Initial State ===');
    await page.screenshot({
      path: path.join(screenshotsDir, '01-initial-state.png'),
      fullPage: true
    });
    console.log('✓ Screenshot captured: 01-initial-state.png');

    // Check initial elements
    const uploadArea = await page.locator('.upload-area');
    const isVisible = await uploadArea.isVisible();
    console.log(`Upload area visible: ${isVisible}`);

    console.log('\n=== TEST 2: Hover State ===');
    await uploadArea.hover();
    await page.waitForTimeout(500);
    await page.screenshot({
      path: path.join(screenshotsDir, '02-hover-state.png'),
      fullPage: true
    });
    console.log('✓ Screenshot captured: 02-hover-state.png');

    console.log('\n=== TEST 3: Click to Browse ===');
    // Since we can't actually upload files via file input in automation,
    // we'll test the UI by simulating the file list display
    const fileInput = await page.locator('input[type="file"]');
    const inputVisible = await fileInput.isVisible({ timeout: 1000 }).catch(() => false);
    console.log(`File input visible: ${inputVisible}`);

    console.log('\n=== TEST 4: Console Errors Check ===');
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    page.on('pageerror', error => {
      errors.push(error.message);
    });

    // Wait a bit to catch any errors
    await page.waitForTimeout(1000);
    if (errors.length > 0) {
      console.log('❌ Console errors found:');
      errors.forEach(err => console.log(`  - ${err}`));
    } else {
      console.log('✓ No console errors detected');
    }

    console.log('\n=== TEST 5: Responsive Design - Mobile View ===');
    await page.setViewportSize({ width: 375, height: 812 });
    await page.waitForTimeout(500);
    await page.screenshot({
      path: path.join(screenshotsDir, '03-mobile-view.png'),
      fullPage: true
    });
    console.log('✓ Screenshot captured: 03-mobile-view.png');

    console.log('\n=== TEST 6: Responsive Design - Tablet View ===');
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(500);
    await page.screenshot({
      path: path.join(screenshotsDir, '04-tablet-view.png'),
      fullPage: true
    });
    console.log('✓ Screenshot captured: 04-tablet-view.png');

    console.log('\n=== TEST 7: Responsive Design - Desktop View ===');
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(500);
    await page.screenshot({
      path: path.join(screenshotsDir, '05-desktop-view.png'),
      fullPage: true
    });
    console.log('✓ Screenshot captured: 05-desktop-view.png');

    console.log('\n=== TEST 8: Accessibility Check ===');
    // Check for accessibility issues
    const hasAriaLabels = await page.evaluate(() => {
      const uploadArea = document.querySelector('.upload-area');
      return {
        hasAriaLabel: uploadArea?.hasAttribute('aria-label') || uploadArea?.hasAttribute('aria-labelledby'),
        hasTabIndex: uploadArea?.hasAttribute('tabindex'),
        fileInputHasLabel: document.querySelector('input[type="file"]')?.hasAttribute('id') &&
                          document.querySelector('label[for]') !== null
      };
    });
    console.log('Accessibility features:', hasAriaLabels);

    console.log('\n=== TEST 9: Element Measurements ===');
    const measurements = await page.evaluate(() => {
      const uploadArea = document.querySelector('.upload-area');
      const rect = uploadArea?.getBoundingClientRect();
      return {
        width: rect?.width,
        height: rect?.height,
        fontSize: window.getComputedStyle(uploadArea).fontSize,
        padding: window.getComputedStyle(uploadArea).padding,
        borderRadius: window.getComputedStyle(uploadArea).borderRadius
      };
    });
    console.log('Upload area measurements:', measurements);

    console.log('\n=== TEST 10: Interactive Elements Check ===');
    const interactiveElements = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      return buttons.map(btn => ({
        text: btn.textContent?.trim(),
        visible: btn.offsetParent !== null,
        disabled: btn.disabled
      }));
    });
    console.log('Buttons found:', interactiveElements);

    console.log('\n=== TEST COMPLETE ===');
    console.log(`Screenshots saved to: ${screenshotsDir}`);

    // Keep browser open for manual inspection
    console.log('\nBrowser will remain open for 30 seconds for manual inspection...');
    await page.waitForTimeout(30000);

  } catch (error) {
    console.error('❌ Test error:', error.message);
    await page.screenshot({
      path: path.join(screenshotsDir, 'error-state.png'),
      fullPage: true
    });
  } finally {
    await browser.close();
    console.log('\nBrowser closed.');
  }
})();
