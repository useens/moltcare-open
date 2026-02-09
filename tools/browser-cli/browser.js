#!/usr/bin/env node
/**
 * Browser CLI - 基于 Playwright 的简单浏览器自动化
 * 零API成本，纯本地控制
 */

const { chromium } = require('playwright-core');
const path = require('path');
const fs = require('fs');

const SCREENSHOT_DIR = path.join(process.cwd(), '.browser-screenshots');
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

let browser = null;
let context = null;
let page = null;

const CHROMIUM_PATH = process.env.CHROMIUM_PATH || '/usr/bin/chromium';

async function ensureBrowser() {
  if (!browser) {
    browser = await chromium.launch({
      headless: true,
      executablePath: CHROMIUM_PATH,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    context = await browser.newContext({
      viewport: { width: 1280, height: 720 }
    });
    page = await context.newPage();
  }
  return page;
}

async function closeBrowser() {
  if (browser) {
    await browser.close();
    browser = null;
    context = null;
    page = null;
    console.log('✓ Browser closed');
  }
}

async function takeScreenshot(name = 'screenshot') {
  const filename = `${name}-${Date.now()}.png`;
  const filepath = path.join(SCREENSHOT_DIR, filename);
  await page.screenshot({ path: filepath, fullPage: true });
  return filepath;
}

const commands = {
  async goto(url) {
    const p = await ensureBrowser();
    await p.goto(url, { waitUntil: 'networkidle' });
    const screenshot = await takeScreenshot('navigate');
    console.log(`✓ Navigated to ${url}`);
    console.log(`📸 Screenshot: ${screenshot}`);
  },

  async click(selector) {
    const p = await ensureBrowser();
    await p.click(selector);
    const screenshot = await takeScreenshot('click');
    console.log(`✓ Clicked ${selector}`);
    console.log(`📸 Screenshot: ${screenshot}`);
  },

  async type(selector, text) {
    const p = await ensureBrowser();
    await p.fill(selector, text);
    const screenshot = await takeScreenshot('type');
    console.log(`✓ Typed "${text}" into ${selector}`);
    console.log(`📸 Screenshot: ${screenshot}`);
  },

  async screenshot(name = 'screenshot') {
    const p = await ensureBrowser();
    const filepath = await takeScreenshot(name);
    console.log(`✓ Screenshot saved: ${filepath}`);
  },

  async text(selector) {
    const p = await ensureBrowser();
    const content = await p.textContent(selector);
    console.log(content);
  },

  async url() {
    const p = await ensureBrowser();
    console.log(p.url());
  },

  async title() {
    const p = await ensureBrowser();
    console.log(await p.title());
  },

  async wait(ms = 1000) {
    await page.waitForTimeout(parseInt(ms));
    console.log(`✓ Waited ${ms}ms`);
  },

  async close() {
    await closeBrowser();
  },

  async help() {
    console.log(`
Browser CLI - 纯 Playwright 浏览器控制

Usage: browser <command> [args...]

Commands:
  goto <url>           访问网址
  click <selector>     点击元素 (CSS选择器)
  type <selector> <text>  在输入框输入文本
  screenshot [name]    截图保存
  text <selector>      获取元素文本
  url                  显示当前URL
  title                显示页面标题
  wait <ms>            等待毫秒
  close                关闭浏览器
  help                 显示帮助

Examples:
  browser goto https://example.com
  browser click "button[type=submit]"
  browser type "#username" "myname"
  browser screenshot

Screenshots saved to: ${SCREENSHOT_DIR}
`);
  }
};

async function main() {
  const args = process.argv.slice(2);
  const cmd = args[0] || 'help';
  
  if (!commands[cmd]) {
    console.error(`Unknown command: ${cmd}`);
    console.log('Run "browser help" for usage.');
    process.exit(1);
  }

  try {
    await commands[cmd](...args.slice(1));
  } catch (err) {
    console.error(`Error: ${err.message}`);
    process.exit(1);
  }

  // Auto-close on exit unless 'goto' (keep browser open for next command)
  if (cmd !== 'goto' && cmd !== 'help' && cmd !== 'close') {
    // Keep browser open for chaining commands
  }
}

// Handle cleanup
process.on('exit', () => closeBrowser());
process.on('SIGINT', async () => {
  await closeBrowser();
  process.exit(0);
});

main();
