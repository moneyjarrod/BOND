// BOND Control Panel — Express Sidecar
// Serves: React app (production) + Doctrine filesystem API + Clipboard bridge
// Port: 3000

import express from 'express';
import cors from 'cors';
import { readdir, readFile, writeFile, stat, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import { join, resolve } from 'path';
import { createServer } from 'http';
import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);

const app = express();
app.use(cors());
app.use(express.json());

// ─── Config ───────────────────────────────────────────────
const BOND_ROOT = resolve(process.env.BOND_ROOT
  || join(process.cwd(), '..'));
const DOCTRINE_PATH = resolve(process.env.DOCTRINE_PATH
  || join(BOND_ROOT, 'doctrine'));
const STATE_PATH = resolve(process.env.STATE_PATH
  || join(BOND_ROOT, 'state'));
const PORT = process.env.PORT || 3000;
const MCP_URL = process.env.MCP_URL || 'http://localhost:3002';

// ─── Doctrine Filesystem API ──────────────────────────────

// List all entity folders
app.get('/api/doctrine', async (req, res) => {
  try {
    const entries = await readdir(DOCTRINE_PATH, { withFileTypes: true });
    const entities = [];

    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const entityPath = join(DOCTRINE_PATH, entry.name);
      const files = await readdir(entityPath);
      const mdFiles = files.filter(f => f.endsWith('.md'));

      // Classify files: bare name = doctrine/seed, G-prefix = growth
      const growth = mdFiles.filter(f => f.match(/^G-|^.*-G\d/));
      const seeds = mdFiles.filter(f => !f.match(/^G-|^.*-G\d/));

      // Read entity.json for classification (B69: Four-Class Architecture)
      let entityConfig = {};
      try {
        const configRaw = await readFile(join(entityPath, 'entity.json'), 'utf-8');
        entityConfig = JSON.parse(configRaw);
      } catch {
        // Fallback: folder name heuristic
        entityConfig = {
          class: entry.name.startsWith('_') ? 'library'
            : /^P\d/.test(entry.name) ? 'perspective'
            : 'doctrine',
          tools: {}
        };
      }

      const type = entityConfig.class || 'doctrine';

      // Class tool defaults (B69)
      const CLASS_TOOLS = {
        doctrine:    { filesystem: true, iss: true, qais: false, heatmap: false, crystal: false },
        project:     { filesystem: true, iss: true, qais: true, heatmap: true, crystal: true },
        perspective: { filesystem: true, iss: false, qais: true, heatmap: true, crystal: true },
        library:     { filesystem: true, iss: false, qais: false, heatmap: false, crystal: false },
      };

      const defaults = CLASS_TOOLS[type] || CLASS_TOOLS.library;
      const tools = { ...defaults, ...(entityConfig.tools || {}) };
      // Enforce class boundaries — can only toggle what the class allows
      const allowed = CLASS_TOOLS[type] || {};
      for (const key of Object.keys(tools)) {
        if (allowed[key] === false) tools[key] = false;
      }

      entities.push({
        name: entry.name,
        display_name: entityConfig.display_name || null,
        files: mdFiles,
        type,
        tools,
        core: entityConfig.core || null,
        doctrine_count: (type === 'doctrine' || type === 'project') ? seeds.length : 0,
        seed_count: type === 'perspective' ? seeds.length : 0,
        growth_count: growth.length,
      });
    }

    res.json({ entities, doctrine_path: DOCTRINE_PATH });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// List files in entity folder
app.get('/api/doctrine/:entity', async (req, res) => {
  try {
    const entityPath = join(DOCTRINE_PATH, req.params.entity);
    // Guard against path traversal
    const resolved = resolve(entityPath);
    if (!resolved.startsWith(resolve(DOCTRINE_PATH))) {
      return res.status(403).json({ error: 'Access denied' });
    }

    const files = await readdir(entityPath);
    const mdFiles = files.filter(f => f.endsWith('.md'));

    const fileDetails = await Promise.all(mdFiles.map(async (f) => {
      const filePath = join(entityPath, f);
      const info = await stat(filePath);
      const isGrowth = !!f.match(/^G-|^.*-G\d/);
      return {
        name: f,
        size: info.size,
        modified: info.mtime,
        type: isGrowth ? 'growth' : 'doctrine'
      };
    }));

    res.json({ entity: req.params.entity, files: fileDetails });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Update entity tool toggles (B69)
app.put('/api/doctrine/:entity/tools', async (req, res) => {
  try {
    const entityPath = join(DOCTRINE_PATH, req.params.entity);
    const resolved = resolve(entityPath);
    if (!resolved.startsWith(resolve(DOCTRINE_PATH))) {
      return res.status(403).json({ error: 'Access denied' });
    }
    const configPath = join(entityPath, 'entity.json');
    let config = {};
    try {
      config = JSON.parse(await readFile(configPath, 'utf-8'));
    } catch { /* new config */ }

    // Merge only allowed tools for this class
    const CLASS_TOOLS = {
      doctrine:    { filesystem: true, iss: true, qais: false, heatmap: false, crystal: false },
      project:     { filesystem: true, iss: true, qais: true, heatmap: true, crystal: true },
      perspective: { filesystem: true, iss: false, qais: true, heatmap: true, crystal: true },
      library:     { filesystem: true, iss: false, qais: false, heatmap: false, crystal: false },
    };
    const type = config.class || 'doctrine';
    const allowed = CLASS_TOOLS[type] || {};
    const incoming = req.body.tools || {};
    const tools = { ...(config.tools || {}) };
    for (const [key, val] of Object.entries(incoming)) {
      if (allowed[key] !== false) tools[key] = val;
    }
    config.tools = tools;

    await writeFile(configPath, JSON.stringify(config, null, 2) + '\n');
    res.json({ saved: true, tools });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Update entity display name
app.put('/api/doctrine/:entity/name', async (req, res) => {
  try {
    const entityPath = join(DOCTRINE_PATH, req.params.entity);
    const resolved = resolve(entityPath);
    if (!resolved.startsWith(resolve(DOCTRINE_PATH))) {
      return res.status(403).json({ error: 'Access denied' });
    }
    const configPath = join(entityPath, 'entity.json');
    let config = {};
    try {
      config = JSON.parse(await readFile(configPath, 'utf-8'));
    } catch { /* new config */ }

    const { display_name } = req.body;
    if (display_name === null || display_name === '') {
      delete config.display_name;
    } else {
      config.display_name = display_name;
    }

    await writeFile(configPath, JSON.stringify(config, null, 2) + '\n');
    res.json({ saved: true, display_name: config.display_name || null });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Create new entity (B69 Four-Class)
const STARTER_CONTENT = {
  doctrine: (name) => `# ${name}\n\n<!-- Doctrine: IS statements. Static truth. -->\n`,
  project: (name) => `# ${name} — CORE\n\n<!-- Project CORE: immutable boundary. Define scope and constraints. -->\n`,
  perspective: (name) => `# ${name}\n\n<!-- Perspective seed. This file will grow through resonance. -->\n`,
  library: (name) => `# ${name}\n\n<!-- Library reference. Read-only knowledge. -->\n`,
};

const STARTER_FILENAME = {
  doctrine: (code) => `${code}-root.md`,
  project: () => 'CORE.md',
  perspective: () => 'seed.md',
  library: () => 'index.md',
};

app.post('/api/doctrine', async (req, res) => {
  try {
    const { name, class: entityClass } = req.body;
    if (!name || !entityClass) {
      return res.status(400).json({ error: 'name and class required' });
    }
    const validClasses = ['doctrine', 'project', 'perspective', 'library'];
    if (!validClasses.includes(entityClass)) {
      return res.status(400).json({ error: `class must be one of: ${validClasses.join(', ')}` });
    }
    // Sanitize folder name
    const safeName = name.replace(/[^a-zA-Z0-9_-]/g, '');
    if (!safeName) {
      return res.status(400).json({ error: 'Invalid name after sanitization' });
    }
    const entityPath = join(DOCTRINE_PATH, safeName);
    const resolved = resolve(entityPath);
    if (!resolved.startsWith(resolve(DOCTRINE_PATH))) {
      return res.status(403).json({ error: 'Access denied' });
    }
    // Check if already exists
    try {
      await stat(entityPath);
      return res.status(409).json({ error: `Entity '${safeName}' already exists` });
    } catch { /* good — doesn't exist */ }

    // Create folder
    await mkdir(entityPath, { recursive: true });

    // Write entity.json
    const config = { class: entityClass };
    if (entityClass === 'project') config.core = 'CORE.md';
    await writeFile(
      join(entityPath, 'entity.json'),
      JSON.stringify(config, null, 2) + '\n'
    );

    // Write starter file
    const code = safeName.substring(0, 4).toUpperCase();
    const starterName = STARTER_FILENAME[entityClass](code);
    const starterContent = STARTER_CONTENT[entityClass](safeName);
    await writeFile(join(entityPath, starterName), starterContent);

    console.log(`\u2728 Created ${entityClass}: ${safeName}`);
    res.json({ created: true, name: safeName, class: entityClass, files: ['entity.json', starterName] });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Return file content
app.get('/api/doctrine/:entity/:file', async (req, res) => {
  try {
    const filePath = join(DOCTRINE_PATH, req.params.entity, req.params.file);
    // Guard against path traversal
    const resolved = resolve(filePath);
    if (!resolved.startsWith(resolve(DOCTRINE_PATH))) {
      return res.status(403).json({ error: 'Access denied' });
    }

    const content = await readFile(filePath, 'utf-8');
    const isGrowth = !!req.params.file.match(/^G-|^.*-G\d/);

    res.json({
      file: req.params.file,
      entity: req.params.entity,
      type: isGrowth ? 'growth' : 'doctrine',
      content
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─── MCP Stats Proxy ─────────────────────────────────────
const MCP_STATS_SCRIPT = join(process.cwd(), 'mcp_stats.py');

async function getMcpStats(system) {
  try {
    const { stdout } = await execFileAsync('python', [MCP_STATS_SCRIPT, system], {
      timeout: 5000,
      cwd: process.cwd(),
    });
    return JSON.parse(stdout);
  } catch (err) {
    return { status: 'offline', error: err.message };
  }
}

// Individual system endpoints (what module cards poll)
app.get('/api/mcp/:system/stats', async (req, res) => {
  const data = await getMcpStats(req.params.system);
  if (data.status === 'offline' || data.error) {
    res.status(503).json(data);
  } else {
    res.json(data);
  }
});

// Also serve as /status for modules that use that
app.get('/api/mcp/:system/status', async (req, res) => {
  const data = await getMcpStats(req.params.system);
  if (data.status === 'offline' || data.error) {
    res.status(503).json(data);
  } else {
    res.json(data);
  }
});

// All systems at once
app.get('/api/mcp/all', async (req, res) => {
  const data = await getMcpStats('all');
  res.json(data);
});

// ─── MCP Tool Invocation (S4) ─────────────────────────────
const MCP_INVOKE_SCRIPT = join(process.cwd(), 'mcp_invoke.py');

app.post('/api/mcp/:system/invoke', async (req, res) => {
  const { system } = req.params;
  const { tool, input } = req.body;
  if (!tool) return res.status(400).json({ error: 'tool required' });

  try {
    const { stdout, stderr } = await execFileAsync('python', [
      MCP_INVOKE_SCRIPT, system, tool, input || ''
    ], { timeout: 15000, cwd: process.cwd() });

    try {
      res.json(JSON.parse(stdout));
    } catch {
      res.json({ raw: stdout, stderr: stderr || null });
    }
  } catch (err) {
    res.status(503).json({ error: err.message, stderr: err.stderr || null });
  }
});

// ─── Module Configs API ────────────────────────────────
const MODULES_PATH = join(process.cwd(), 'modules');

app.get('/api/modules', async (req, res) => {
  try {
    const files = await readdir(MODULES_PATH);
    const modules = [];
    for (const f of files) {
      if (!f.endsWith('.json')) continue;
      const content = await readFile(join(MODULES_PATH, f), 'utf-8');
      try { modules.push(JSON.parse(content)); } catch { /* skip bad json */ }
    }
    res.json({ modules });
  } catch (err) {
    res.json({ modules: [] });
  }
});

// Panel config
app.get('/api/config', (req, res) => {
  res.json({
    doctrine_path: DOCTRINE_PATH,
    state_path: STATE_PATH,
    mcp_url: MCP_URL,
    ws_port: 3001,
    version: '1.2.0-s85'
  });
});

// ─── Entity State API (Enter-Mode) ────────────────────────
const STATE_FILE = join(STATE_PATH, 'active_entity.json');
const NULL_STATE = { entity: null, class: null, path: null, entered: null };

// Read current state
app.get('/api/state', async (req, res) => {
  try {
    const raw = await readFile(STATE_FILE, 'utf-8');
    res.json(JSON.parse(raw));
  } catch {
    res.json(NULL_STATE);
  }
});

// Enter entity — write state file
app.post('/api/state/enter', async (req, res) => {
  const { entity } = req.body;
  if (!entity) return res.status(400).json({ error: 'entity required' });

  try {
    // Look up entity config
    const entityPath = join(DOCTRINE_PATH, entity);
    const resolved = resolve(entityPath);
    if (!resolved.startsWith(resolve(DOCTRINE_PATH))) {
      return res.status(403).json({ error: 'Access denied' });
    }

    let entityConfig = {};
    try {
      entityConfig = JSON.parse(await readFile(join(entityPath, 'entity.json'), 'utf-8'));
    } catch {
      return res.status(404).json({ error: `Entity '${entity}' not found or missing entity.json` });
    }

    // Write state file FIRST (Claude reads this on {Sync})
    const state = {
      entity,
      class: entityConfig.class || 'doctrine',
      display_name: entityConfig.display_name || null,
      path: resolved,
      entered: new Date().toISOString()
    };
    await writeFile(STATE_FILE, JSON.stringify(state, null, 2) + '\n');

    // Bridge: panel clipboard handles {Enter} command (App.jsx)
    console.log(`🔓 Entered: ${entity} (${state.class})`);
    res.json({ entered: true, state });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Exit entity — clear state file
app.post('/api/state/exit', async (req, res) => {
  try {
    // Read current before clearing (for logging)
    let prev = NULL_STATE;
    try { prev = JSON.parse(await readFile(STATE_FILE, 'utf-8')); } catch {}

    // Clear state file
    await writeFile(STATE_FILE, JSON.stringify(NULL_STATE, null, 2) + '\n');

    // Bridge: panel clipboard handles {Exit} command (App.jsx)
    if (prev.entity) {
      console.log(`🔒 Exited: ${prev.entity}`);
    }
    res.json({ exited: true, previous: prev.entity });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Link entity — BOND_MASTER exclusive. Attaches a secondary entity.
app.post('/api/state/link', async (req, res) => {
  try {
    const { entity: linkTarget } = req.body;
    if (!linkTarget) return res.status(400).json({ error: 'entity required' });

    // Read current state
    let state;
    try { state = JSON.parse(await readFile(STATE_FILE, 'utf-8')); } catch {
      return res.status(400).json({ error: 'No active entity' });
    }

    // Only BOND_MASTER can link
    if (state.entity !== 'BOND_MASTER') {
      return res.status(403).json({ error: 'Only BOND_MASTER can link entities' });
    }

    // Cannot link to self
    if (linkTarget === 'BOND_MASTER') {
      return res.status(400).json({ error: 'Cannot link to self' });
    }

    // Look up target entity
    const targetPath = join(DOCTRINE_PATH, linkTarget);
    const resolved = resolve(targetPath);
    if (!resolved.startsWith(resolve(DOCTRINE_PATH))) {
      return res.status(403).json({ error: 'Access denied' });
    }

    let targetConfig = {};
    try {
      targetConfig = JSON.parse(await readFile(join(targetPath, 'entity.json'), 'utf-8'));
    } catch {
      return res.status(404).json({ error: `Entity '${linkTarget}' not found` });
    }

    // Write linked state
    state.linked = {
      entity: linkTarget,
      class: targetConfig.class || 'library',
      display_name: targetConfig.display_name || null,
      path: resolved,
      linked_at: new Date().toISOString()
    };
    await writeFile(STATE_FILE, JSON.stringify(state, null, 2) + '\n');

    console.log(`🔗 Linked: BOND_MASTER ↔ ${linkTarget} (${state.linked.class})`);
    res.json({ linked: true, state });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Unlink entity — remove secondary entity link
app.post('/api/state/unlink', async (req, res) => {
  try {
    let state;
    try { state = JSON.parse(await readFile(STATE_FILE, 'utf-8')); } catch {
      return res.status(400).json({ error: 'No active entity' });
    }

    const prev = state.linked?.entity || null;
    delete state.linked;
    await writeFile(STATE_FILE, JSON.stringify(state, null, 2) + '\n');

    if (prev) console.log(`🔓 Unlinked: ${prev}`);
    res.json({ unlinked: true, previous: prev });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Bridge ───────────────────────────────────────────────
// Clipboard-only. Panel writes "BOND:{cmd}" → AHK OnClipboardChange.
// HTTP bridge removed S85 (Dead Code Audit).

// ─── Production static serving ────────────────────────────
const DIST_PATH = join(process.cwd(), 'dist');
if (existsSync(DIST_PATH)) {
  app.use(express.static(DIST_PATH));
  app.get('*', (req, res) => {
    if (!req.path.startsWith('/api/')) {
      res.sendFile(join(DIST_PATH, 'index.html'));
    }
  });
  console.log('   Serving built panel from dist/');
}

// ─── Start ────────────────────────────────────────────────
const server = createServer(app);

server.listen(PORT, () => {
  console.log(`🔥🌊 BOND Panel sidecar on http://localhost:${PORT}`);
  console.log(`   Doctrine path: ${DOCTRINE_PATH}`);
  console.log(`   MCP target:    ${MCP_URL}`);
});

export { server };
