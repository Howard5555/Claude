// Renders index.html frame by frame in headless Chromium, writing frames/0000.jpg ...
// Usage: node render.mjs [firstFrame] [lastFrame]
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const root = path.dirname(new URL(import.meta.url).pathname);
const types = { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2' };
const server = http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'content-type': types[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
}).listen(0, '127.0.0.1');
await new Promise(r => server.once('listening', r));
const port = server.address().port;

const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
page.on('pageerror', e => console.error('PAGE ERROR', e.message));
page.on('console', m => { if (m.type() === 'error') console.error('CONSOLE', m.text()); });
await page.goto(`http://127.0.0.1:${port}/index.html`);
await page.waitForFunction(() => window.sceneReady === true, null, { timeout: 60000 });

const total = await page.evaluate(() => window.TOTAL_FRAMES);
const first = +(process.argv[2] ?? 0), last = +(process.argv[3] ?? total - 1);
fs.mkdirSync(path.join(root, 'frames'), { recursive: true });
const t0 = Date.now();
for (let i = first; i <= last; i++) {
  const url = await page.evaluate(n => window.renderFrame(n), i);
  fs.writeFileSync(path.join(root, 'frames', String(i).padStart(4, '0') + '.jpg'), Buffer.from(url.split(',')[1], 'base64'));
  if (i % 15 === 0) console.log(`frame ${i}/${last}  ${((Date.now() - t0) / (i - first + 1) / 1000).toFixed(2)} s/frame`);
}
await browser.close(); server.close();
