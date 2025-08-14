/*
  Warm thumbnail cache by requesting /api/thumbnails for images in the DB.
  Usage (from repo root):
    node web-app/server/workers/warm-thumbnails.js --limit 500 --sizes 300x400,800x600,1200x900 --concurrency 8
  Env:
    LV_PASSWORD (optional; defaults to LV81868LV)
    API_BASE (optional; defaults to http://localhost:5005)
*/
const path = require('path');
const axios = require('axios');
const db = require('../database/connection');

async function main() {
  const args = process.argv.slice(2);
  const getArg = (name, def) => {
    const idx = args.findIndex(a => a === `--${name}`);
    if (idx !== -1 && args[idx + 1]) return args[idx + 1];
    return def;
  };

  const limit = parseInt(getArg('limit', '0'), 10) || 0;
  const sizes = (getArg('sizes', '300x400,800x600').split(',').map(s => s.trim())).filter(Boolean);
  const concurrency = Math.max(1, parseInt(getArg('concurrency', '6'), 10));
  const apiBase = process.env.API_BASE || 'http://localhost:5005';
  const password = process.env.LV_PASSWORD || 'LV81868LV';

  await db.connect();
  const rows = await db.query(
    `SELECT drive_file_id FROM files WHERE mime_type LIKE 'image%' ORDER BY id DESC ${limit ? 'LIMIT ?' : ''}`,
    limit ? [limit] : []
  );

  const queue = [...rows.map(r => r.drive_file_id)];
  let completed = 0; let errors = 0;

  const worker = async () => {
    while (queue.length) {
      const id = queue.shift();
      try {
        for (const size of sizes) {
          await axios.get(`${apiBase}/api/thumbnails/${id}`, {
            params: { size },
            headers: { 'x-password': password },
            timeout: 30000,
            responseType: 'arraybuffer'
          });
        }
        completed += 1;
        if (completed % 50 === 0) {
          console.log(`Warmed ${completed} images (errors: ${errors})`);
        }
      } catch (e) {
        errors += 1;
        console.warn(`Warm error for ${id}: ${e.message}`);
      }
    }
  };

  const workers = Array.from({ length: concurrency }, () => worker());
  await Promise.all(workers);

  console.log(`Done. Warmed ${completed} images; errors: ${errors}`);
  process.exit(0);
}

if (require.main === module) {
  main().catch(e => { console.error(e); process.exit(1); });
}


