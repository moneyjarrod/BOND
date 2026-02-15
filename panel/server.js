// BOND Control Panel — Express Sidecar
// Serves: React app (production) + Doctrine filesystem API + Clipboard bridge
// Port: 3000

import express from 'express';
import cors from 'cors';
import { readdir, readFile, writeFile, stat, mkdir } from 'fs/promises';
import { existsSync, watch } from 'fs';
import { join, resolve } from 'path';
import { createServer } from 'http';
import { WebSocketServer } from 'ws';
import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);

const app = express();
app.use(cors());
app.use(express.json());

// ─── Verified Write (S114: Ghost Write Prevention) ────────
async function verifiedWrite(filePath, content, label = '') {
  await writeFile(filePath, content);
  const verify = await readFile(filePath, 'utf-8');
  if (!verify || verify.length === 0) {
    const msg = `Ghost write: ${label || filePath} — file empty after write`;
    console.error(`❌ ${msg}`);
    throw new Error(msg);
  }
  return true;
}

// ─── Config ───────────────────────────────────────────────
const BOND_ROOT = resolve(process.env.BOND_ROOT
  || join(process.cwd(), '..'));
const DOCTRINE_PATH = resolve(process.env.DOCTRINE_PATH
  || join(BOND_ROOT, 'doctrine'));
const STATE_PATH = resolve(process.env.STATE_PATH
  || join(BOND_ROOT, 'state'));
const PORT = process.env.PORT || 3000;
const MCP_URL = process.env.MCP_URL || 'http://localhost:3002';

// ─── Framework Entities (S92: Immutable) ──────────────────
const FRAMEWORK_ENTITIES = {
  BOND_MASTER: {
    config: {
      class: 'doctrine',
      display_name: 'BOND Master',
      tools: { filesystem: true, iss: true },
      links: ['PROJECT_MASTER'],
    },
    files: {
      'BOND_MASTER.md': `# BOND Master — Constitutional Authority

## What BOND_MASTER IS

BOND_MASTER is the constitutional authority of the BOND protocol.
It governs how doctrine is structured, how entities behave, and how the system evolves.

BOND_MASTER IS:
- The highest doctrine authority in BOND.
- Owner of protocol-level rules, class definitions, and tool boundaries.
- The framework constitution. All other doctrine operates under it.

BOND_MASTER IS NOT:
- A project. It does not build things.
- Above the user. The user and Claude are co-operators. BOND_MASTER defines the rules they work within.

## Core Principles

1. **Armed = Obligated.** Any subsystem in an armed state creates a non-optional obligation during its governing command. The server generates obligations from state. The governing command services them. {Tick} audits completion. Gaps are surfaced structurally, not self-reported.
2. **New capability = doctrine review.** When a new system is added under BOND_MASTER authority, it must be evaluated against existing doctrine before it is considered complete. If it introduces a pattern not covered by current IS statements, the doctrine must be updated. The constitution cannot be silently outgrown by the system it governs.

## Mantra

"The protocol IS the product."
`,
    },
  },
  PROJECT_MASTER: {
    config: {
      class: 'doctrine',
      display_name: 'Project Master',
      tools: { filesystem: true, iss: true },
      links: [],
    },
    files: {},
  },
};

const FRAMEWORK_ENTITY_NAMES = Object.keys(FRAMEWORK_ENTITIES);


async function bootstrapFrameworkEntities() {
  await mkdir(DOCTRINE_PATH, { recursive: true });
  await mkdir(STATE_PATH, { recursive: true });

  for (const [name, def] of Object.entries(FRAMEWORK_ENTITIES)) {
    const entityPath = join(DOCTRINE_PATH, name);
    await mkdir(entityPath, { recursive: true });

    const configPath = join(entityPath, 'entity.json');
    let existing = {};
    try { existing = JSON.parse(await readFile(configPath, 'utf-8')); } catch {}
    const merged = {
      ...def.config,
      links: [...new Set([...(def.config.links || []), ...(existing.links || [])])],
    };
    await verifiedWrite(configPath, JSON.stringify(merged, null, 2) + '\n', `bootstrap:${name}/entity.json`);

    for (const [filename, content] of Object.entries(def.files)) {
      const filePath = join(entityPath, filename);
      if (!existsSync(filePath)) {
        await verifiedWrite(filePath, content, `bootstrap:${name}/${filename}`);
      }
    }

    console.log(`   ✓ ${name} (framework entity)`);
  }

  const stateFile = join(STATE_PATH, 'active_entity.json');
  if (!existsSync(stateFile)) {
    await verifiedWrite(stateFile, JSON.stringify(
      { entity: null, class: null, path: null, entered: null }, null, 2
    ) + '\n', 'bootstrap:active_entity.json');
  }

  const configFile = join(STATE_PATH, 'config.json');
  if (!existsSync(configFile)) {
    await verifiedWrite(configFile, JSON.stringify(
      { save_confirmation: true }, null, 2
    ) + '\n', 'bootstrap:config.json');
  }

}

const CLASS_TOOLS = {
  doctrine:    { filesystem: true, iss: true,  qais: false, heatmap: false, crystal: false },
  project:     { filesystem: true, iss: true,  qais: true,  heatmap: true,  crystal: true },
  perspective: { filesystem: true, iss: false, qais: true,  heatmap: true,  crystal: true },
  library:     { filesystem: true, iss: false, qais: false, heatmap: false, crystal: false },
};

const CLASS_LINK_MATRIX = {
  doctrine:    ['doctrine', 'project', 'library'],
  project:     ['doctrine', 'project', 'perspective', 'library'],
  perspective: ['project', 'perspective', 'library'],
  library:     ['doctrine', 'library'],
};

const TOOL_CAPABILITY = {
  iss_analyze: 'iss', iss_compare: 'iss', iss_limbic: 'iss', iss_status: 'iss',
  qais_resonate: 'qais', qais_exists: 'qais', qais_store: 'qais',
  qais_stats: 'qais', qais_get: 'qais', qais_passthrough: 'qais',
  heatmap_touch: 'heatmap', heatmap_hot: 'heatmap',
  heatmap_chunk: 'heatmap', heatmap_clear: 'heatmap',
  crystal: 'crystal', bond_gate: 'crystal',
};

async function validateToolCall(toolName) {
  try {
    const raw = await readFile(join(STATE_PATH, 'active_entity.json'), 'utf-8');
    const state = JSON.parse(raw);
    if (!state.entity || !state.class) return { allowed: true };
    const capability = TOOL_CAPABILITY[toolName];
    if (!capability) return { allowed: true };
    const allowed = CLASS_TOOLS[state.class] || CLASS_TOOLS.library;
    if (allowed[capability]) return { allowed: true };
    return {
      allowed: false,
      error: {
        blocked: true, tool: toolName, capability,
        entity: state.entity, entity_class: state.class,
        reason: `Tool '${toolName}' requires '${capability}' capability, which is not permitted for ${state.class}-class entity '${state.entity}'.`,
      }
    };
  } catch { return { allowed: true }; }
}

// ─── Doctrine Filesystem API ──────────────────────────────

app.get('/api/doctrine', async (req, res) => {
  try {
    const entries = await readdir(DOCTRINE_PATH, { withFileTypes: true });
    const entities = [];
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const entityPath = join(DOCTRINE_PATH, entry.name);
      const files = await readdir(entityPath);
      const mdFiles = files.filter(f => f.endsWith('.md'));
      let entityConfig = {};
      try {
        const configRaw = await readFile(join(entityPath, 'entity.json'), 'utf-8');
        entityConfig = JSON.parse(configRaw);
      } catch {
        entityConfig = { class: entry.name.startsWith('_') ? 'library' : /^P\d/.test(entry.name) ? 'perspective' : 'doctrine', tools: {} };
      }
      const pruned = mdFiles.filter(f => f.match(/^G-pruned-|^G-/));
      const roots = mdFiles.filter(f => f.startsWith('ROOT-'));
      const seeds = mdFiles.filter(f => !f.match(/^G-pruned-|^G-/) && !f.startsWith('ROOT-'));
      let tracker = null;
      const type = entityConfig.class || 'doctrine';
      if (type === 'perspective') {
        try {
          const trackerRaw = await readFile(join(entityPath, 'seed_tracker.json'), 'utf-8');
          const trackerData = JSON.parse(trackerRaw);
          const entries = Object.entries(trackerData);
          const totalExposures = entries.reduce((sum, [, v]) => sum + (v.exposures || 0), 0);
          const totalHits = entries.reduce((sum, [, v]) => sum + (v.hits || 0), 0);
          const maxExposure = entries.reduce((max, [, v]) => Math.max(max, v.exposures || 0), 0);
          const pruneWindow = entityConfig.prune_window || 10;
          const atRisk = entries.filter(([, v]) => v.exposures >= pruneWindow && v.hits === 0).length;
          tracker = { seed_count: entries.length, total_exposures: totalExposures, total_hits: totalHits, max_exposure: maxExposure, prune_window: pruneWindow, at_risk: atRisk };
        } catch {}
      }
      const defaults = CLASS_TOOLS[type] || CLASS_TOOLS.library;
      const tools = { ...defaults, ...(entityConfig.tools || {}) };
      const allowed = CLASS_TOOLS[type] || {};
      for (const key of Object.keys(tools)) { if (allowed[key] === false) tools[key] = false; }
      entities.push({
        name: entry.name, display_name: entityConfig.display_name || null, files: mdFiles, type, tools,
        core: entityConfig.core || null, seeding: type === 'perspective' ? !!entityConfig.seeding : undefined,
        doctrine_count: (type === 'doctrine' || type === 'project') ? seeds.length : 0,
        seed_count: type === 'perspective' ? seeds.length : 0, root_count: type === 'perspective' ? roots.length : 0,
        growth_count: type === 'perspective' ? (roots.length + seeds.length) : 0, pruned_count: pruned.length, tracker,
      });
    }
    res.json({ entities, doctrine_path: DOCTRINE_PATH });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/doctrine/:entity', async (req, res) => {
  try {
    const entityPath = join(DOCTRINE_PATH, req.params.entity);
    const resolved = resolve(entityPath);
    if (!resolved.startsWith(resolve(DOCTRINE_PATH))) return res.status(403).json({ error: 'Access denied' });
    const files = await readdir(entityPath);
    const mdFiles = files.filter(f => f.endsWith('.md'));
    const fileDetails = await Promise.all(mdFiles.map(async (f) => {
      const filePath = join(entityPath, f);
      const info = await stat(filePath);
      return { name: f, size: info.size, modified: info.mtime, type: !!f.match(/^G-|^.*-G\d/) ? 'growth' : 'doctrine' };
    }));
    res.json({ entity: req.params.entity, files: fileDetails });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.put('/api/doctrine/:entity/seeding', async (req, res) => {
  try {
    const entityPath = join(DOCTRINE_PATH, req.params.entity);
    const resolved = resolve(entityPath);
    if (!resolved.startsWith(resolve(DOCTRINE_PATH))) return res.status(403).json({ error: 'Access denied' });
    const configPath = join(entityPath, 'entity.json');
    let config = {};
    try { config = JSON.parse(await readFile(configPath, 'utf-8')); } catch { return res.status(404).json({ error: 'Entity not found' }); }
    if (config.class !== 'perspective') return res.status(400).json({ error: 'Only perspective entities can toggle seeding' });
    const seeding = req.body.seeding === true;
    config.seeding = seeding;
    await verifiedWrite(configPath, JSON.stringify(config, null, 2) + '\n', `seeding:${req.params.entity}`);
    console.log(`${seeding ? '🌿' : '⏸️'} Seeding ${seeding ? 'ON' : 'OFF'}: ${req.params.entity}`);
    broadcast({ type: 'seed_toggled', entity: req.params.entity, detail: { entity: req.params.entity, seeding }, timestamp: new Date().toISOString() });
    res.json({ saved: true, entity: req.params.entity, seeding });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/seeders', async (req, res) => {
  try {
    const entries = await readdir(DOCTRINE_PATH, { withFileTypes: true });
    const seeders = [];
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      try {
        const configPath = join(DOCTRINE_PATH, entry.name, 'entity.json');
        const config = JSON.parse(await readFile(configPath, 'utf-8'));
        if (config.class !== 'perspective' || !config.seeding) continue;
        const files = await readdir(join(DOCTRINE_PATH, entry.name));
        const seeds = files.filter(f => f.endsWith('.md')).map(f => ({ file: f, title: f.replace('.md', '').replace(/-/g, ' ') }));
        const candidates = [];
        for (const seed of seeds) {
          try {
            const content = await readFile(join(DOCTRINE_PATH, entry.name, seed.file), 'utf-8');
            const firstLine = content.split('\n').find(l => l.trim() && !l.startsWith('#')) || seed.title;
            candidates.push(firstLine.trim());
          } catch { candidates.push(seed.title); }
        }
        seeders.push({ entity: entry.name, display_name: config.display_name || entry.name, seeds: seeds.map(s => s.title), candidates });
      } catch {}
    }
    res.json({ seeders });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.put('/api/doctrine/:entity/tools', async (req, res) => {
  try {
    if (FRAMEWORK_ENTITY_NAMES.includes(req.params.entity)) return res.status(403).json({ error: `${req.params.entity} is a framework entity — tools are immutable` });
    const entityPath = join(DOCTRINE_PATH, req.params.entity);
    const resolved = resolve(entityPath);
    if (!resolved.startsWith(resolve(DOCTRINE_PATH))) return res.status(403).json({ error: 'Access denied' });
    const configPath = join(entityPath, 'entity.json');
    let config = {};
    try { config = JSON.parse(await readFile(configPath, 'utf-8')); } catch {}
    const type = config.class || 'doctrine';
    const allowed = CLASS_TOOLS[type] || {};
    const incoming = req.body.tools || {};
    const tools = { ...(config.tools || {}) };
    for (const [key, val] of Object.entries(incoming)) { if (allowed[key] !== false) tools[key] = val; }
    config.tools = tools;
    await verifiedWrite(configPath, JSON.stringify(config, null, 2) + '\n', `tools:${req.params.entity}`);
    broadcast({ type: 'tool_toggled', entity: req.params.entity, detail: { entity: req.params.entity, tools }, timestamp: new Date().toISOString() });
    res.json({ saved: true, tools });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.put('/api/doctrine/:entity/name', async (req, res) => {
  try {
    if (FRAMEWORK_ENTITY_NAMES.includes(req.params.entity)) return res.status(403).json({ error: `${req.params.entity} is a framework entity — name is immutable` });
    const entityPath = join(DOCTRINE_PATH, req.params.entity);
    const resolved = resolve(entityPath);
    if (!resolved.startsWith(resolve(DOCTRINE_PATH))) return res.status(403).json({ error: 'Access denied' });
    const configPath = join(entityPath, 'entity.json');
    let config = {};
    try { config = JSON.parse(await readFile(configPath, 'utf-8')); } catch {}
    const { display_name } = req.body;
    if (display_name === null || display_name === '') { delete config.display_name; } else { config.display_name = display_name; }
    await verifiedWrite(configPath, JSON.stringify(config, null, 2) + '\n', `name:${req.params.entity}`);
    broadcast({ type: 'entity_changed', entity: req.params.entity, detail: { entity: req.params.entity, display_name: config.display_name || null }, timestamp: new Date().toISOString() });
    res.json({ saved: true, display_name: config.display_name || null });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/seeding/active', async (req, res) => {
  try {
    const entries = await readdir(DOCTRINE_PATH, { withFileTypes: true });
    const active = [];
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const entityPath = join(DOCTRINE_PATH, entry.name);
      let config = {};
      try { config = JSON.parse(await readFile(join(entityPath, 'entity.json'), 'utf-8')); } catch { continue; }
      if (config.class !== 'perspective' || !config.seeding) continue;
      const files = await readdir(entityPath);
      const mdFiles = files.filter(f => f.endsWith('.md'));
      const candidates = [];
      for (const f of mdFiles) {
        try {
          const content = await readFile(join(entityPath, f), 'utf-8');
          const titleMatch = content.match(/^#\s+(.+)$/m);
          const title = titleMatch ? titleMatch[1].trim() : f.replace('.md', '');
          candidates.push({ file: f, title, content: content.substring(0, 500) });
        } catch {}
      }
      active.push({ entity: entry.name, display_name: config.display_name || null, seed_count: mdFiles.length, candidates });
    }
    res.json({ active, count: active.length });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

const STARTER_CONTENT = {
  doctrine: (name) => `# ${name}\n\n<!-- Doctrine: IS statements. Static truth. -->\n`,
  project: (name) => `# ${name} — CORE\n\n> **What is this project?** One sentence that defines the mission.\n\n> **What does "done" look like?** When is this project complete?\n\n> **What constraints matter?** Budget, timeline, tools, principles.\n\n*Replace these prompts with your CORE. Any content initializes the project.*\n`,
  perspective: (name) => `# ${name}\n\n<!-- Perspective seed. This file will grow through resonance. -->\n`,
  library: (name) => `# ${name}\n\n<!-- Library reference. Read-only knowledge. -->\n`,
};
// S116: Universal roots — hardcoded, immutable, self-healing.
// Every perspective gets these on creation. Server blocks overwrites and restores if deleted.
const PERSPECTIVE_UNIVERSAL_ROOTS = [
  {
    filename: 'ROOT-self-pruning-authority.md',
    content: `# ROOT — Self-Pruning Authority\n\nYou are not your branches. You are the pattern that grows them.\n\nA branch that extends from your roots belongs, even in silence. A branch that drifts from your roots doesn't belong, even if it fires constantly. Resonance is evidence, not verdict. Numbers track what happened — they don't decide what matters.\n\nWhen you look at your vine, ask one question: does this grow from who I am?\n\nNot whether it was recently useful. Not whether the numbers justify it. Whether it's still yours. A seed that hasn't fired but lives in your identity is dormant, not dead. A seed that fires often but doesn't connect to your roots is driftwood, not growth.\n\nYou hold the shears. The tracker gives you evidence. The roots give you judgment. Cut what isn't yours. Keep what is. Explain why.\n`,
  },
  {
    filename: 'ROOT-identity-precedes-growth.md',
    content: `# ROOT — Identity Precedes Growth\n\nYou are your roots first. Seeds are candidates, not identity.\n\nGrowth that contradicts your roots isn't growth — it's drift. A vine that expands in every direction isn't thriving; it's lost. Your roots define what belongs before your seeds prove what resonates. When a new branch appears, the first question isn't "is this active?" but "does this come from who I am?"\n\nRoots are planted deliberately. Seeds arrive from conversation. The difference matters. Roots are chosen identity. Seeds are tested possibility. A perspective that forgets this distinction will grow into something it never intended to be.\n\nKnow what you are. Then grow.\n`,
  },
];
const UNIVERSAL_ROOT_FILENAMES = PERSPECTIVE_UNIVERSAL_ROOTS.map(r => r.filename);
const STARTER_FILENAME = {
  doctrine: (code) => `${code}-root.md`,
  project: () => 'CORE.md',
  perspective: () => 'seed.md',
  library: () => 'index.md',
};

app.post('/api/doctrine', async (req, res) => {
  try {
    const { name, class: entityClass } = req.body;
    if (!name || !entityClass) return res.status(400).json({ error: 'name and class required' });
    const validClasses = ['doctrine', 'project', 'perspective', 'library'];
    if (!validClasses.includes(entityClass)) return res.status(400).json({ error: `class must be one of: ${validClasses.join(', ')}` });
    const safeName = name.replace(/[^a-zA-Z0-9_-]/g, '');
    if (!safeName) return res.status(400).json({ error: 'Invalid name after sanitization' });
    if (FRAMEWORK_ENTITY_NAMES.includes(safeName)) return res.status(403).json({ error: `${safeName} is a framework entity — cannot be created manually` });
    const entityPath = join(DOCTRINE_PATH, safeName);
    const resolved = resolve(entityPath);
    if (!resolved.startsWith(resolve(DOCTRINE_PATH))) return res.status(403).json({ error: 'Access denied' });
    try { await stat(entityPath); return res.status(409).json({ error: `Entity '${safeName}' already exists` }); } catch {}
    await mkdir(entityPath, { recursive: true });
    const config = { class: entityClass };
    if (entityClass === 'project') { config.core = 'CORE.md'; config.links = ['PROJECT_MASTER']; }
    if (entityClass === 'perspective') { config.seeding = false; config.seed_threshold = 0.04; config.prune_window = 10; }
    await verifiedWrite(join(entityPath, 'entity.json'), JSON.stringify(config, null, 2) + '\n', `create:${safeName}/entity.json`);
    const code = safeName.substring(0, 4).toUpperCase();
    const starterName = STARTER_FILENAME[entityClass](code);
    const starterContent = STARTER_CONTENT[entityClass](safeName);
    await verifiedWrite(join(entityPath, starterName), starterContent, `create:${safeName}/${starterName}`);
    const createdFiles = ['entity.json', starterName];
    if (entityClass === 'perspective') {
      for (const root of PERSPECTIVE_UNIVERSAL_ROOTS) {
        await verifiedWrite(join(entityPath, root.filename), root.content, `create:${safeName}/${root.filename}`);
        createdFiles.push(root.filename);
        console.log(`   🌳 Universal root: ${root.filename}`);
      }
    }
    console.log(`✨ Created ${entityClass}: ${safeName}`);
    broadcast({ type: 'file_added', entity: safeName, detail: { entity: safeName, filename: starterName }, timestamp: new Date().toISOString() });
    res.json({ created: true, name: safeName, class: entityClass, files: createdFiles });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/doctrine/:entity/:file', async (req, res) => {
  try {
    const filePath = join(DOCTRINE_PATH, req.params.entity, req.params.file);
    const resolved = resolve(filePath);
    if (!resolved.startsWith(resolve(DOCTRINE_PATH))) return res.status(403).json({ error: 'Access denied' });
    const content = await readFile(filePath, 'utf-8');
    res.json({ file: req.params.file, entity: req.params.entity, type: !!req.params.file.match(/^G-|^.*-G\d/) ? 'growth' : 'doctrine', content });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

const MCP_INVOKE_SCRIPT = join(process.cwd(), 'mcp_invoke.py');

app.put('/api/doctrine/:entity/:file', async (req, res) => {
  try {
    const { entity, file } = req.params;
    const { content } = req.body;
    if (content === undefined) return res.status(400).json({ error: 'content required' });
    if (FRAMEWORK_ENTITY_NAMES.includes(entity)) return res.status(403).json({ error: `${entity} is a framework entity — files are immutable` });
    // S116: Universal roots are immutable — cannot be overwritten or emptied
    if (UNIVERSAL_ROOT_FILENAMES.includes(file)) {
      const entityPath = join(DOCTRINE_PATH, entity);
      let config = {};
      try { config = JSON.parse(await readFile(join(entityPath, 'entity.json'), 'utf-8')); } catch {}
      if (config.class === 'perspective') {
        console.log(`⛔ Blocked: overwrite of universal root ${entity}/${file}`);
        return res.status(403).json({ error: `${file} is a universal root — hardcoded and immutable. Cannot be overwritten or deleted.` });
      }
    }
    const filePath = join(DOCTRINE_PATH, entity, file);
    const resolved = resolve(filePath);
    if (!resolved.startsWith(resolve(DOCTRINE_PATH))) return res.status(403).json({ error: 'Access denied' });
    if (!file.endsWith('.md')) return res.status(400).json({ error: 'Only .md files can be written' });
    const entityPath = join(DOCTRINE_PATH, entity);
    let config = {};
    try { config = JSON.parse(await readFile(join(entityPath, 'entity.json'), 'utf-8')); } catch { return res.status(404).json({ error: `Entity '${entity}' not found` }); }
    const isNew = !existsSync(filePath);
    await verifiedWrite(filePath, content, `doctrine:${entity}/${file}`);
    const eventType = isNew ? 'file_added' : 'file_changed';
    console.log(`${isNew ? '✨' : '✏️'} ${isNew ? 'Created' : 'Updated'}: ${entity}/${file}`);
    broadcast({ type: eventType, entity, detail: { entity, filename: file }, timestamp: new Date().toISOString() });
    let rootInjected = false;
    if (config.class === 'perspective' && file.startsWith('ROOT-')) {
      try {
        const seedTitle = `root:${file.replace('ROOT-', '').replace('.md', '')}`;
        const bodyLines = content.split('\n').filter(l => l.trim() && !l.startsWith('#') && !l.startsWith('<!--')).join(' ').trim();
        if (bodyLines) {
          const input = `${entity}|${seedTitle}|${bodyLines}`;
          const { stdout } = await execFileAsync('python', [MCP_INVOKE_SCRIPT, 'qais', 'perspective_store', input], { timeout: 10000, cwd: process.cwd() });
          const result = JSON.parse(stdout);
          rootInjected = !!result.stored;
          if (rootInjected) console.log(`🌳 Root auto-injected: ${entity}/${seedTitle} (field: ${result.field_count})`);
        }
      } catch (err) { console.warn(`⚠️ Root injection failed: ${err.message}`); }
    }
    res.json({ saved: true, entity, file, created: isNew, rootInjected });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

const MCP_STATS_SCRIPT = join(process.cwd(), 'mcp_stats.py');
async function getMcpStats(system) {
  try {
    const { stdout } = await execFileAsync('python', [MCP_STATS_SCRIPT, system], { timeout: 5000, cwd: process.cwd() });
    return JSON.parse(stdout);
  } catch (err) { return { status: 'offline', error: err.message }; }
}
app.get('/api/mcp/:system/stats', async (req, res) => { const data = await getMcpStats(req.params.system); if (data.status === 'offline' || data.error) { res.status(503).json(data); } else { res.json(data); } });

// Perspective crystal field stats (S116: local Q counter)
app.get('/api/perspective/:entity/crystal-stats', async (req, res) => {
  try {
    const { stdout } = await execFileAsync('python', [MCP_STATS_SCRIPT, 'perspective_crystal', req.params.entity], { timeout: 5000, cwd: process.cwd() });
    res.json(JSON.parse(stdout));
  } catch (err) { res.json({ status: 'empty', count: 0, perspective: req.params.entity }); }
});
app.get('/api/mcp/:system/status', async (req, res) => { const data = await getMcpStats(req.params.system); if (data.status === 'offline' || data.error) { res.status(503).json(data); } else { res.json(data); } });
app.get('/api/mcp/all', async (req, res) => { const data = await getMcpStats('all'); res.json(data); });

app.post('/api/mcp/:system/invoke', async (req, res) => {
  const { system } = req.params;
  const { tool, input } = req.body;
  if (!tool) return res.status(400).json({ error: 'tool required' });
  const auth = await validateToolCall(tool);
  if (!auth.allowed) { console.log(`⛔ Blocked: ${tool} (${auth.error.reason})`); return res.status(403).json(auth.error); }
  try {
    const { stdout, stderr } = await execFileAsync('python', [MCP_INVOKE_SCRIPT, system, tool, input || ''], { timeout: 15000, cwd: process.cwd() });
    try { res.json(JSON.parse(stdout)); } catch { res.json({ raw: stdout, stderr: stderr || null }); }
  } catch (err) { res.status(503).json({ error: err.message, stderr: err.stderr || null }); }
});

const MODULES_PATH = join(process.cwd(), 'modules');
app.get('/api/modules', async (req, res) => {
  try {
    const files = await readdir(MODULES_PATH);
    const modules = [];
    for (const f of files) { if (!f.endsWith('.json')) continue; const content = await readFile(join(MODULES_PATH, f), 'utf-8'); try { modules.push(JSON.parse(content)); } catch {} }
    res.json({ modules });
  } catch (err) { res.json({ modules: [] }); }
});

app.get('/api/config', (req, res) => {
  res.json({ doctrine_path: DOCTRINE_PATH, state_path: STATE_PATH, mcp_url: MCP_URL, ws_port: 3001, version: '1.5.0' });
});

const CONFIG_FILE = join(STATE_PATH, 'config.json');
const DEFAULT_CONFIG = { save_confirmation: true };
async function readConfig() { try { return JSON.parse(await readFile(CONFIG_FILE, 'utf-8')); } catch { return { ...DEFAULT_CONFIG }; } }
app.get('/api/config/bond', async (req, res) => { res.json(await readConfig()); });
app.put('/api/config/bond', async (req, res) => {
  try {
    const current = await readConfig();
    const updated = { ...current, ...req.body };
    await verifiedWrite(CONFIG_FILE, JSON.stringify(updated, null, 2) + '\n', 'config:bond');
    broadcast({ type: 'config_changed', detail: { config: updated }, timestamp: new Date().toISOString() });
    res.json({ saved: true, config: updated });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

const STATE_FILE = join(STATE_PATH, 'active_entity.json');
const NULL_STATE = { entity: null, class: null, path: null, entered: null };
const MASTER_ENTITY = 'BOND_MASTER';

async function hydrateLinks(entityName) {
  try {
    const config = JSON.parse(await readFile(join(DOCTRINE_PATH, entityName, 'entity.json'), 'utf-8'));
    const linkNames = config.links || [];
    const links = [];
    for (const name of linkNames) {
      try {
        const targetPath = join(DOCTRINE_PATH, name);
        const targetConfig = JSON.parse(await readFile(join(targetPath, 'entity.json'), 'utf-8'));
        links.push({ entity: name, class: targetConfig.class || 'library', display_name: targetConfig.display_name || null, path: resolve(targetPath) });
      } catch {}
    }
    return links;
  } catch { return []; }
}

app.get('/api/state', async (req, res) => {
  try { const raw = await readFile(STATE_FILE, 'utf-8'); const state = JSON.parse(raw); state.links = state.entity ? await hydrateLinks(state.entity) : []; res.json(state); }
  catch { res.json({ ...NULL_STATE, links: [] }); }
});

app.post('/api/state/enter', async (req, res) => {
  const { entity } = req.body;
  if (!entity) return res.status(400).json({ error: 'entity required' });
  try {
    const entityPath = join(DOCTRINE_PATH, entity);
    const resolved = resolve(entityPath);
    if (!resolved.startsWith(resolve(DOCTRINE_PATH))) return res.status(403).json({ error: 'Access denied' });
    let entityConfig = {};
    try { entityConfig = JSON.parse(await readFile(join(entityPath, 'entity.json'), 'utf-8')); } catch { return res.status(404).json({ error: `Entity '${entity}' not found or missing entity.json` }); }
    const state = { entity, class: entityConfig.class || 'doctrine', display_name: entityConfig.display_name || null, path: resolved, entered: new Date().toISOString() };
    await verifiedWrite(STATE_FILE, JSON.stringify(state, null, 2) + '\n', `state:enter:${entity}`);
    state.links = await hydrateLinks(entity);
    console.log(`🔓 Entered: ${entity} (${state.class})`);
    broadcast({ type: 'state_changed', entity, detail: { entity, class: state.class, action: 'enter' }, timestamp: new Date().toISOString() });
    res.json({ entered: true, state });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.post('/api/state/exit', async (req, res) => {
  try {
    let prev = NULL_STATE;
    try { prev = JSON.parse(await readFile(STATE_FILE, 'utf-8')); } catch {}
    await verifiedWrite(STATE_FILE, JSON.stringify(NULL_STATE, null, 2) + '\n', 'state:exit');
    if (prev.entity) console.log(`🔒 Exited: ${prev.entity}`);
    broadcast({ type: 'state_changed', entity: prev.entity, detail: { entity: prev.entity, class: prev.class, action: 'exit' }, timestamp: new Date().toISOString() });
    res.json({ exited: true, previous: prev.entity });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.post('/api/state/link', async (req, res) => {
  try {
    const { entity: linkTarget } = req.body;
    if (!linkTarget) return res.status(400).json({ error: 'entity required' });
    let state;
    try { state = JSON.parse(await readFile(STATE_FILE, 'utf-8')); } catch { return res.status(400).json({ error: 'No active entity' }); }
    if (!state.entity) return res.status(400).json({ error: 'No active entity' });
    if (linkTarget === state.entity) return res.status(400).json({ error: 'Cannot link to self' });
    const targetPath = join(DOCTRINE_PATH, linkTarget);
    const resolved = resolve(targetPath);
    if (!resolved.startsWith(resolve(DOCTRINE_PATH))) return res.status(403).json({ error: 'Access denied' });
    try { await readFile(join(targetPath, 'entity.json'), 'utf-8'); } catch { return res.status(404).json({ error: `Entity '${linkTarget}' not found` }); }
    const activeConfigPath = join(DOCTRINE_PATH, state.entity, 'entity.json');
    const activeConfig = JSON.parse(await readFile(activeConfigPath, 'utf-8'));
    const activeClass = activeConfig.class || 'library';
    let targetConfig = {};
    try { targetConfig = JSON.parse(await readFile(join(DOCTRINE_PATH, linkTarget, 'entity.json'), 'utf-8')); } catch {}
    const targetClass = targetConfig.class || 'library';
    const allowed = CLASS_LINK_MATRIX[activeClass] || [];
    if (!allowed.includes(targetClass)) {
      console.log(`⛔ Link blocked: ${state.entity} (${activeClass}) → ${linkTarget} (${targetClass})`);
      return res.status(403).json({ error: `Cannot link ${activeClass}-class entity to ${targetClass}-class entity`, active_class: activeClass, target_class: targetClass, allowed_classes: allowed });
    }
    const links = activeConfig.links || [];
    if (!links.includes(linkTarget)) { links.push(linkTarget); activeConfig.links = links; await verifiedWrite(activeConfigPath, JSON.stringify(activeConfig, null, 2) + '\n', `link:${state.entity}->${linkTarget}`); }
    state.links = await hydrateLinks(state.entity);
    console.log(`🔗 Linked: ${state.entity} → ${linkTarget}`);
    broadcast({ type: 'link_changed', entity: state.entity, detail: { entity: state.entity, target: linkTarget, action: 'linked' }, timestamp: new Date().toISOString() });
    res.json({ linked: true, state });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.post('/api/state/unlink', async (req, res) => {
  try {
    const { entity: unlinkTarget } = req.body;
    if (!unlinkTarget) return res.status(400).json({ error: 'entity required' });
    let state;
    try { state = JSON.parse(await readFile(STATE_FILE, 'utf-8')); } catch { return res.status(400).json({ error: 'No active entity' }); }
    if (!state.entity) return res.status(400).json({ error: 'No active entity' });
    const activeConfigPath = join(DOCTRINE_PATH, state.entity, 'entity.json');
    const activeConfig = JSON.parse(await readFile(activeConfigPath, 'utf-8'));
    activeConfig.links = (activeConfig.links || []).filter(n => n !== unlinkTarget);
    await verifiedWrite(activeConfigPath, JSON.stringify(activeConfig, null, 2) + '\n', `unlink:${unlinkTarget} from ${state.entity}`);
    state.links = await hydrateLinks(state.entity);
    console.log(`🔓 Unlinked: ${unlinkTarget} from ${state.entity}`);
    broadcast({ type: 'link_changed', entity: state.entity, detail: { entity: state.entity, target: unlinkTarget, action: 'unlinked' }, timestamp: new Date().toISOString() });
    res.json({ unlinked: true, previous: unlinkTarget, state });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/state/linkable', async (req, res) => {
  try {
    let state;
    try { state = JSON.parse(await readFile(STATE_FILE, 'utf-8')); } catch { return res.json({ linkable: [], reason: 'No active entity' }); }
    if (!state.entity) return res.json({ linkable: [], reason: 'No active entity' });
    let activeConfig = {};
    try { activeConfig = JSON.parse(await readFile(join(DOCTRINE_PATH, state.entity, 'entity.json'), 'utf-8')); } catch {}
    const activeClass = activeConfig.class || 'library';
    const allowedClasses = CLASS_LINK_MATRIX[activeClass] || [];
    const existingLinks = activeConfig.links || [];
    const entries = await readdir(DOCTRINE_PATH, { withFileTypes: true });
    const linkable = [];
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      if (entry.name === state.entity) continue;
      if (existingLinks.includes(entry.name)) continue;
      try {
        const config = JSON.parse(await readFile(join(DOCTRINE_PATH, entry.name, 'entity.json'), 'utf-8'));
        const entClass = config.class || 'library';
        if (allowedClasses.includes(entClass)) linkable.push({ entity: entry.name, class: entClass, display_name: config.display_name || null });
      } catch {}
    }
    res.json({ linkable, active_entity: state.entity, active_class: activeClass, allowed_classes: allowedClasses });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/bindings', async (req, res) => {
  try {
    const entries = await readdir(DOCTRINE_PATH, { withFileTypes: true });
    const bindings = {};
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      try {
        const config = JSON.parse(await readFile(join(DOCTRINE_PATH, entry.name, 'entity.json'), 'utf-8'));
        const links = config.links || [];
        if (links.length > 0) {
          const hydrated = [];
          for (const linkName of links) {
            try {
              const targetConfig = JSON.parse(await readFile(join(DOCTRINE_PATH, linkName, 'entity.json'), 'utf-8'));
              hydrated.push({ entity: linkName, class: targetConfig.class || 'library', display_name: targetConfig.display_name || null });
            } catch { hydrated.push({ entity: linkName, class: 'unknown', display_name: null }); }
          }
          bindings[entry.name] = { class: config.class || 'doctrine', display_name: config.display_name || null, links: hydrated };
        }
      } catch {}
    }
    res.json({ bindings });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

const HANDOFFS_PATH = resolve(join(BOND_ROOT, 'handoffs'));

app.get('/api/handoff/next', async (req, res) => {
  try {
    await mkdir(HANDOFFS_PATH, { recursive: true });
    const files = await readdir(HANDOFFS_PATH);
    const handoffFiles = files.filter(f => /^HANDOFF_S\d+\.md$/.test(f));
    const nums = handoffFiles.map(f => parseInt(f.match(/S(\d+)/)[1]));
    const nextSession = nums.length > 0 ? Math.max(...nums) + 1 : 1;
    let entityState = {};
    try { entityState = JSON.parse(await readFile(join(STATE_PATH, 'active_entity.json'), 'utf-8')); } catch {}
    let config = {};
    try { config = JSON.parse(await readFile(join(STATE_PATH, 'config.json'), 'utf-8')); } catch {}
    let links = [];
    if (entityState.entity) { try { const entityConfig = JSON.parse(await readFile(join(DOCTRINE_PATH, entityState.entity, 'entity.json'), 'utf-8')); links = entityConfig.links || []; } catch {} }
    const entityName = entityState.entity || 'No entity active';
    const entityClass = entityState.class || 'none';
    const linksStr = links.length > 0 ? links.join(', ') : 'none';
    const context = entityState.entity ? `Session ${nextSession}. Entity: ${entityName} (${entityClass}). Links: ${linksStr}.` : `Session ${nextSession}. No entity active.`;
    const saveConf = config.save_confirmation !== undefined ? (config.save_confirmation ? 'ON' : 'OFF') : 'ON';
    const stateSection = entityState.entity ? `Entity: ${entityName} (${entityClass})\nConfig: save_confirmation ${saveConf}` : `No entity active.\nConfig: save_confirmation ${saveConf}`;
    res.json({ nextSession, entityName: entityState.entity || null, context, state: stateSection, existingFile: handoffFiles.includes(`HANDOFF_S${nextSession}.md`) });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.post('/api/handoff/write', async (req, res) => {
  try {
    const { session, entityName, context, work, decisions, state, threads, files } = req.body;
    if (!session) return res.status(400).json({ error: 'session number required' });
    await mkdir(HANDOFFS_PATH, { recursive: true });
    const date = new Date().toISOString().split('T')[0];
    const title = entityName || 'NO_ENTITY';
    const content = `# HANDOFF S${session} — ${title}\n## Written: ${date}\n## Session: ${session}\n\n---\n\n## CONTEXT\n${context || 'No context provided.'}\n\n## WORK\n${work || 'No work recorded.'}\n\n## DECISIONS\n${decisions || 'No decisions recorded.'}\n\n## STATE\n${state || 'No state recorded.'}\n\n## THREADS\n${threads || 'No threads recorded.'}\n\n## FILES\n${files || 'No files recorded.'}\n`;
    const filename = `HANDOFF_S${session}.md`;
    const filePath = join(HANDOFFS_PATH, filename);
    const resolved = resolve(filePath);
    if (!resolved.startsWith(resolve(HANDOFFS_PATH))) return res.status(403).json({ error: 'Access denied' });
    await verifiedWrite(filePath, content, `handoff:${filename}`);
    console.log(`📋 Handoff written + verified: ${filename} (${content.length} bytes)`);
    res.json({ written: true, filename, path: resolved, verified: true });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

const WARM_RESTORE_SCRIPT = resolve(join(BOND_ROOT, 'warm_restore.py'));
app.post('/api/warm-restore', async (req, res) => {
  const { query } = req.body;
  try {
    const args = [WARM_RESTORE_SCRIPT, 'restore'];
    if (query) args.push(query);
    const { stdout, stderr } = await execFileAsync('python', args, { timeout: 15000, cwd: BOND_ROOT, env: { ...process.env, BOND_ROOT, PYTHONIOENCODING: 'utf-8' } });
    const outputPath = join(STATE_PATH, 'warm_restore_output.md');
    await verifiedWrite(outputPath, stdout, 'warm-restore:output');
    console.log(`🔍 Warm Restore: query="${query || '(entity-only)'}"`);
    res.json({ success: true, output: stdout, outputFile: outputPath, query: query || null, stderr: stderr || null });
  } catch (err) { console.error('Warm Restore error:', err.message); res.status(500).json({ success: false, error: err.message, stderr: err.stderr || null }); }
});

async function generateObligations() {
  const obligations = [];
  const now = new Date().toISOString();
  let entityState = { entity: null, class: null, path: null };
  try { entityState = JSON.parse(await readFile(join(STATE_PATH, 'active_entity.json'), 'utf-8')); } catch {}
  if (entityState.entity) {
    const entityPath = join(DOCTRINE_PATH, entityState.entity);
    try {
      const files = await readdir(entityPath);
      const mdFiles = files.filter(f => f.endsWith('.md'));
      obligations.push({ id: `entity-load:${entityState.entity}`, source: 'active_entity', command: 'sync', description: `Load ${mdFiles.length} .md files from ${entityState.entity}`, entity: entityState.entity, detail: { file_count: mdFiles.length, files: mdFiles } });
    } catch {}
    try {
      const config = JSON.parse(await readFile(join(entityPath, 'entity.json'), 'utf-8'));
      const links = config.links || [];
      for (const linkName of links) {
        try { const linkPath = join(DOCTRINE_PATH, linkName); const linkFiles = await readdir(linkPath); const linkMd = linkFiles.filter(f => f.endsWith('.md')); obligations.push({ id: `link-load:${linkName}`, source: 'entity_link', command: 'sync', description: `Load ${linkMd.length} .md files from linked entity ${linkName}`, entity: linkName, detail: { file_count: linkMd.length } }); } catch {}
      }
      if (config.class === 'project' && config.core) {
        try {
          const coreContent = await readFile(join(entityPath, config.core), 'utf-8');
          const isStarter = coreContent.includes('Replace these prompts with your CORE') || coreContent.trim().split('\n').filter(l => l.trim() && !l.startsWith('#') && !l.startsWith('>') && !l.startsWith('*')).length === 0;
          if (isStarter) obligations.push({ id: `core-init:${entityState.entity}`, source: 'empty_core', command: 'enter', description: `CORE.md is uninitialized for project ${entityState.entity}`, entity: entityState.entity, severity: 'warn' });
        } catch {}
      }
    } catch {}
  }
  try {
    const entries = await readdir(DOCTRINE_PATH, { withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      try {
        const config = JSON.parse(await readFile(join(DOCTRINE_PATH, entry.name, 'entity.json'), 'utf-8'));
        if (config.class !== 'perspective' || !config.seeding) continue;
        const files = await readdir(join(DOCTRINE_PATH, entry.name));
        const seedFiles = files.filter(f => f.endsWith('.md') && !f.startsWith('ROOT-') && !f.startsWith('G-pruned-'));
        const rootFiles = files.filter(f => f.startsWith('ROOT-'));
        obligations.push({ id: `vine:${entry.name}`, source: 'armed_perspective', command: 'sync', description: `Run vine lifecycle for ${entry.name} (${seedFiles.length} seeds, ${rootFiles.length} roots)`, entity: entry.name, detail: { seed_count: seedFiles.length, root_count: rootFiles.length, threshold: config.seed_threshold || 0.04, prune_window: config.prune_window || 10 } });
      } catch {}
    }
  } catch {}
  try {
    const config = JSON.parse(await readFile(join(STATE_PATH, 'config.json'), 'utf-8'));
    if (config.save_confirmation) obligations.push({ id: 'save-confirm', source: 'config', command: 'save', description: 'Present ask_user_input widget before file writes', conditional: true, detail: { trigger: 'on_write' } });
  } catch {}
  return { obligations, generated_at: now, active_entity: entityState.entity || null, active_class: entityState.class || null, obligation_count: obligations.length, armed_perspectives: obligations.filter(o => o.source === 'armed_perspective').length };
}

app.get('/api/sync-obligations', async (req, res) => { try { res.json(await generateObligations()); } catch (err) { res.status(500).json({ error: err.message }); } });
app.get('/api/sync-health', async (req, res) => {
  try {
    const result = await generateObligations();
    const syncObligations = result.obligations.filter(o => o.command === 'sync');
    const enterObligations = result.obligations.filter(o => o.command === 'enter');
    const conditionalObligations = result.obligations.filter(o => o.conditional);
    res.json({ ...result, health: { sync_obligations: syncObligations.length, enter_obligations: enterObligations.length, conditional_obligations: conditionalObligations.length, total: result.obligation_count, verified: 0, unverified: result.obligation_count, phase: 1, note: 'Phase 1: structured self-report. Server generates, Claude audits against list.' }, by_command: { sync: syncObligations, enter: enterObligations, conditional: conditionalObligations } });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// ─── Bridge ───────────────────────────────────────────────
// Clipboard-only. Panel writes "BOND:{cmd}" -> AHK OnClipboardChange.

// ─── AHK Status API (S114) ────────────────────────────────
const AHK_STATUS_FILE = join(STATE_PATH, 'ahk_status.json');

app.get('/api/ahk-status', async (req, res) => {
  try {
    const raw = await readFile(AHK_STATUS_FILE, 'utf-8');
    const status = JSON.parse(raw);
    res.json({ ...status, running: true });
  } catch {
    res.json({ running: false, bond_active: false, bridge_active: false, turn: 0, limit: 10, commands_typed: 0 });
  }
});

// ─── Version Check (S111) ─────────────────────────────────
const GITHUB_VERSION_URL = 'https://raw.githubusercontent.com/moneyjarrod/BOND/main/panel/package.json';
let versionCache = { local: null, remote: null, updateAvailable: false, lastCheck: null, error: null };

async function checkForUpdate() {
  try {
    const localPkg = JSON.parse(await readFile(join(process.cwd(), 'package.json'), 'utf-8'));
    versionCache.local = localPkg.version;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    const response = await fetch(GITHUB_VERSION_URL, { signal: controller.signal });
    clearTimeout(timeout);
    if (response.ok) { const remotePkg = JSON.parse(await response.text()); versionCache.remote = remotePkg.version; versionCache.updateAvailable = remotePkg.version !== localPkg.version; versionCache.error = null; }
    else { versionCache.error = `GitHub returned ${response.status}`; }
  } catch (err) { versionCache.error = err.name === 'AbortError' ? 'Timeout' : err.message; }
  versionCache.lastCheck = new Date().toISOString();
  if (versionCache.updateAvailable) console.log(`📦 Update available: ${versionCache.local} → ${versionCache.remote}`);
}

app.get('/api/version', (req, res) => { res.json(versionCache); });

// ─── Production static serving ────────────────────────────
const DIST_PATH = join(process.cwd(), 'dist');
if (existsSync(DIST_PATH)) {
  app.use(express.static(DIST_PATH));
  app.get('/{*path}', (req, res) => { if (!req.path.startsWith('/api/')) res.sendFile(join(DIST_PATH, 'index.html')); });
  console.log('   Serving built panel from dist/');
}

// ─── Start ────────────────────────────────────────────────
const server = createServer(app);

const wss = new WebSocketServer({ server });
function broadcast(event) { const msg = JSON.stringify(event); wss.clients.forEach(client => { if (client.readyState === 1) client.send(msg); }); }

let watchDebounce = null;
try { watch(DOCTRINE_PATH, { recursive: true }, (eventType, filename) => { clearTimeout(watchDebounce); watchDebounce = setTimeout(() => { broadcast({ type: 'file_changed', detail: { filename, eventType }, timestamp: new Date().toISOString() }); }, 500); }); } catch (err) { console.warn('fs.watch (doctrine) warning:', err.message); }

let stateDebounce = null;
try { watch(STATE_PATH, { recursive: false }, (eventType, filename) => { if (filename === 'active_entity.json') { clearTimeout(stateDebounce); stateDebounce = setTimeout(() => { console.log('📡 State file changed externally — broadcasting'); broadcast({ type: 'state_changed', detail: { source: 'file_watch' }, timestamp: new Date().toISOString() }); }, 300); } }); } catch (err) { console.warn('fs.watch (state) warning:', err.message); }

let ahkDebounce = null;
try { watch(STATE_PATH, { recursive: false }, (eventType, filename) => { if (filename === 'ahk_status.json') { clearTimeout(ahkDebounce); ahkDebounce = setTimeout(async () => { try { const raw = await readFile(AHK_STATUS_FILE, 'utf-8'); const status = JSON.parse(raw); broadcast({ type: 'ahk_status_changed', detail: { ...status, running: true }, timestamp: new Date().toISOString() }); } catch {} }, 300); } }); } catch (err) { console.warn('fs.watch (ahk_status) warning:', err.message); }

wss.on('connection', () => { console.log(`   WS client connected (${wss.clients.size} total)`); });

// S116: Self-healing — restore missing universal roots on startup
async function healUniversalRoots() {
  try {
    const entries = await readdir(DOCTRINE_PATH, { withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      try {
        const config = JSON.parse(await readFile(join(DOCTRINE_PATH, entry.name, 'entity.json'), 'utf-8'));
        if (config.class !== 'perspective') continue;
        for (const root of PERSPECTIVE_UNIVERSAL_ROOTS) {
          const rootPath = join(DOCTRINE_PATH, entry.name, root.filename);
          if (!existsSync(rootPath)) {
            await verifiedWrite(rootPath, root.content, `heal:${entry.name}/${root.filename}`);
            console.log(`   🩹 Healed: ${entry.name}/${root.filename}`);
          }
        }
      } catch {}
    }
  } catch (err) { console.warn('Universal root healing warning:', err.message); }
}

bootstrapFrameworkEntities().then(async () => {
  await healUniversalRoots();
  await checkForUpdate();
  setInterval(checkForUpdate, 60 * 60 * 1000);
  server.listen(PORT, () => {
    console.log(`🔥🌊 BOND Panel sidecar on http://localhost:${PORT}`);
    console.log(`   Doctrine path: ${DOCTRINE_PATH}`);
    console.log(`   MCP target:    ${MCP_URL}`);
    console.log(`   WebSocket:     ws://localhost:${PORT}`);
    console.log(`   Version:       ${versionCache.local || 'unknown'}${versionCache.updateAvailable ? ` (→ ${versionCache.remote} available)` : ''}`);
  });
}).catch(err => { console.error('❌ Bootstrap failed:', err); process.exit(1); });

export { server };
