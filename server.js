/**
 * SPVM INSIGHT — Serveur unifié
 * Node.js sert les fichiers statiques + démarre Flask + proxie /api/
 */
const http  = require('http');
const fs    = require('fs');
const path  = require('path');
const { spawn } = require('child_process');

const PORT       = parseInt(process.env.PORT) || 5200;
const FLASK_PORT = 5201;
const ROOT       = __dirname;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js':   'application/javascript',
  '.css':  'text/css',
  '.json': 'application/json',
  '.png':  'image/png',
  '.ico':  'image/x-icon',
  '.txt':  'text/plain',
};

// ── Démarrer Flask en arrière-plan ──────────────────────────────────────
let flaskReady = false;
const pythons = ['/usr/bin/python3', '/usr/local/bin/python3', 'python3'];
let flaskProc = null;

function startFlask(pythonList) {
  const py = pythonList.shift();
  if (!py) {
    console.warn('⚠  Flask introuvable — mode statique uniquement (AI désactivé)');
    return;
  }
  console.log(`🐍 Démarrage Flask avec ${py} sur :${FLASK_PORT}…`);
  const proc = spawn(py, ['app.py'], {
    cwd: ROOT,
    env: { ...process.env, PORT: String(FLASK_PORT) },
  });
  proc.stdout.on('data', d => {
    const msg = d.toString().trim();
    console.log('[Flask]', msg);
    if (msg.includes(`${FLASK_PORT}`)) flaskReady = true;
  });
  proc.stderr.on('data', d => {
    const msg = d.toString().trim();
    if (msg.includes('Running on')) { flaskReady = true; console.log('[Flask]', msg); }
    else if (msg.includes('Error') || msg.includes('error')) console.warn('[Flask err]', msg);
  });
  proc.on('error', () => startFlask(pythonList));
  proc.on('exit', code => {
    if (code !== 0 && code !== null) {
      console.warn(`[Flask] exited ${code} — retry with next python`);
      startFlask(pythonList);
    }
  });
  flaskProc = proc;
}
startFlask([...pythons]);

// Donner 3 s à Flask pour démarrer
setTimeout(() => { if (!flaskReady) flaskReady = true; }, 3000);

// ── Proxy vers Flask ────────────────────────────────────────────────────
function proxyToFlask(req, res) {
  const body = [];
  req.on('data', c => body.push(c));
  req.on('end', () => {
    const payload = Buffer.concat(body);
    const options = {
      hostname: '127.0.0.1',
      port: FLASK_PORT,
      path: req.url,
      method: req.method,
      headers: { ...req.headers, host: `localhost:${FLASK_PORT}`, 'content-length': payload.length },
    };
    const proxy = http.request(options, pr => {
      res.writeHead(pr.statusCode, pr.headers);
      pr.pipe(res);
    });
    proxy.on('error', err => {
      res.writeHead(503, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        response: `**Panel d'experts IA temporairement indisponible**\n\nLe serveur d'analyse démarre… Réessayez dans quelques secondes.\n\n_Erreur: ${err.message}_`,
        mode: 'unavailable'
      }));
    });
    proxy.write(payload);
    proxy.end();
  });
}

// ── Serveur principal ───────────────────────────────────────────────────
const server = http.createServer((req, res) => {
  const url = req.url.split('?')[0];

  // API → Flask
  if (url.startsWith('/api/')) return proxyToFlask(req, res);

  // Fichiers statiques
  let filePath = path.join(ROOT, url === '/' ? 'index.html' : url);

  fs.stat(filePath, (err, stat) => {
    // Si c'est un dossier, chercher index.html dedans
    if (!err && stat.isDirectory()) filePath = path.join(filePath, 'index.html');

    fs.readFile(filePath, (err2, data) => {
      if (err2) {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end(`404 — ${url}`);
        return;
      }
      const ext  = path.extname(filePath);
      const mime = MIME[ext] || 'application/octet-stream';
      res.writeHead(200, {
        'Content-Type': mime,
        'Cache-Control': ext === '.json' ? 'no-cache' : 'max-age=60',
      });
      res.end(data);
    });
  });
});

server.listen(PORT, () => {
  console.log(`\n🚔 SPVM INSIGHT — http://localhost:${PORT}`);
  console.log(`   Static : Node.js (port ${PORT})`);
  console.log(`   API IA : Flask  (port ${FLASK_PORT}) — démarrage en cours…\n`);
});

process.on('exit',    () => flaskProc?.kill());
process.on('SIGINT',  () => { flaskProc?.kill(); process.exit(); });
process.on('SIGTERM', () => { flaskProc?.kill(); process.exit(); });
