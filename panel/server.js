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
    // PM doctrine files ship as templates/doctrine/PROJECT_MASTER/*.md
    // Template copy pipeline handles them (S95). No inline shadowing.
    files: {},
  },
};

const FRAMEWORK_ENTITY_NAMES = Object.keys(FRAMEWORK_ENTITIES);

// ─── Template Path (S95) ──────────────────────────────────
// Doctrine .md files too large for inline strings ship as templates/.
// Bootstrap copies them to doctrine/ if they don't exist.
const TEMPLATES_PATH = resolve(join(BOND_ROOT, 'templates', 'doctrine'));

// Bootstrap: ensure framework entities exist on startup
async function bootstrapFrameworkEntities() {
  // Ensure doctrine and state directories exist
  await mkdir(DOCTRINE_PATH, { recursive: true });
  await mkdir(STATE_PATH, { recursive: true });

  for (const [name, def] of Object.entries(FRAMEWORK_ENTITIES)) {
    const entityPath = join(DOCTRINE_PATH, name);
    await mkdir(entityPath, { recursive: true });

    // Enforce immutable config fields, but preserve user-added links
    const configPath = join(entityPath, 'entity.json');
    let existing = {};
    try { existing = JSON.parse(await readFile(configPath, 'utf-8')); } catch {}
    const merged = {
      ...def.config,
      // Merge links: framework defaults + any user-added links
      links: [...new Set([...(def.config.links || []), ...(existing.links || [])])],
    };
    await writeFile(configPath, JSON.stringify(merged, null, 2) + '\n');

    // Write starter files only if they don't exist (preserve user additions)
    for (const [filename, content] of Object.entries(def.files)) {
      const filePath = join(entityPath, filename);
      if (!existsSync(filePath)) {
        await writeFile(filePath, content);
      }
    }

    console.log(`   ✓ ${name} (framework entity)`);
  }

  // Ensure state file exists
  const stateFile = join(STATE_PATH, 'active_entity.json');
  if (!existsSync(stateFile)) {
    await writeFile(stateFile, JSON.stringify(
      { entity: null, class: null, path: null, entered: null }, null, 2
    ) + '\n');
  }

  // Ensure config file exists
  const configFile = join(STATE_PATH, 'config.json');
  if (!existsSync(configFile)) {
    await writeFile(configFile, JSON.stringify(
      { save_confirmation: true }, null, 2
    ) + '\n');
  }

  // Copy template .md files to doctrine entities (S95)
  // Templates ship large doctrine docs that are too big for inline strings.
  // Only copies if target doesn't exist (preserves user edits).
  if (existsSync(TEMPLATES_PATH)) {
    try {
      const templateEntities = await readdir(TEMPLATES_PATH, { withFileTypes: true });
      for (const tDir of templateEntities) {
        if (!tDir.isDirectory()) continue;
        const srcDir = join(TEMPLATES_PATH, tDir.name);
        const dstDir = join(DOCTRINE_PATH, tDir.name);
        await mkdir(dstDir, { recursive: true });
        const templateFiles = await readdir(srcDir);
        for (const tf of templateFiles) {
          if (!tf.endsWith('.md')) continue;
          const dstFile = join(dstDir, tf);
          if (!existsSync(dstFile)) {
            const content = await readFile(join(srcDir, tf), 'utf-8');
            await writeFile(dstFile, content);
            console.log(`   \u2192 Template: ${tDir.name}/${tf}`);
          }
        }
      }
    } catch (err) {
      console.warn('Template copy warning:', err.message);
    }
  }
}

// ─── Class Tool Matrix (B69 Four-Class Architecture) ──────
const CLASS_TOOLS = {
  doctrine:    { filesystem: true, iss: true,  qais: false, heatmap: false, crystal: false },
  project:     { filesystem: true, iss: true,  qais: true,  heatmap: true,  crystal: true },
  perspective: { filesystem: true, iss: false, qais: true,  heatmap: true,  crystal: true },
  library:     { filesystem: true, iss: false, qais: false, heatmap: false, crystal: false },
};

// ─── Tool Authorization Middleware (S90) ──────────────────
// Maps MCP tool names to which capability gate they require
const TOOL_CAPABILITY = {
  iss_analyze: 'iss', iss_compare: 'iss', iss_limbic: 'iss', iss_status: 'iss',
  qais_resonate: 'qais', qais_exists: 'qais', qais_store: 'qais',
  qais_stats: 'qais', qais_get: 'qais', qais_passthrough: 'qais',
  heatmap_touch: 'heatmap', heatmap_hot: 'heatmap',
  heatmap_chunk: 'heatmap', heatmap_clear: 'heatmap',
  crystal: 'crystal', bond_gate: 'crystal',
};

async function validateToolCall(toolName) {
  // Read current entity state
  try {
    const raw = await readFile(join(STATE_PATH, 'active_entity.json'), 'utf-8');
    const state = JSON.parse(raw);
    if (!state.entity || !state.class) return { allowed: true };

    const capability = TOOL_CAPABILITY[toolName];
    if (!capability) return { allowed: true }; // unknown tool = permissive

    const allowed = CLASS_TOOLS[state.class] || CLASS_TOOLS.library;
    if (allowed[capability]) return { allowed: true };

    return {
      allowed: false,
      error: {
        blocked: true,
        tool: toolName,
        capability,
        entity: state.entity,
        entity_class: state.class,
        reason: `Tool '${toolName}' requires '${capability}' capability, `
          + `which is not permitted for ${state.class}-class entity '${state.entity}'.`,
      }
    };
  } catch {
    return { allowed: true }; // no state file = no boundaries
  }
}

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

      // Classify files: bare name = doctrine/seed, G-prefix = pruning log, ROOT- = root
      const pruned = mdFiles.filter(f => f.match(/^G-pruned-|^G-/));
      const roots = mdFiles.filter(f => f.startsWith('ROOT-'));
      const seeds = mdFiles.filter(f => !f.match(/^G-pruned-|^G-/) && !f.startsWith('ROOT-'));

      // Read seed_tracker.json for perspectives (vine health)
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
          tracker = {
            seed_count: entries.length,
            total_exposures: totalExposures,
            total_hits: totalHits,
            max_exposure: maxExposure,
            prune_window: pruneWindow,
            at_risk: atRisk,
          };
        } catch { /* no tracker yet */ }
      }

      // Class tool defaults (B69) — uses module-level CLASS_TOOLS
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
        seeding: type === 'perspective' ? !!entityConfig.seeding : undefined,
        doctrine_count: (type === 'doctrine' || type === 'project') ? seeds.length : 0,
        seed_count: type === 'perspective' ? seeds.length : 0,
        root_count: type === 'perspective' ? roots.length : 0,
        growth_count: type === 'perspective' ? (roots.length + seeds.length) : 0,
        pruned_count: pruned.length,
        tracker: tracker,
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

// ─── Seed Toggle (S98: Perspective Collection) ────────────
// Toggle seeding on/off for perspective entities.
// When seeding is on, Claude runs passthrough against this
// perspective's seed titles during conversation.
app.put('/api/doctrine/:entity/seeding', async (req, res) => {
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
    } catch { return res.status(404).json({ error: 'Entity not found' }); }

    // Only perspectives can seed
    if (config.class !== 'perspective') {
      return res.status(400).json({ error: 'Only perspective entities can toggle seeding' });
    }

    const seeding = req.body.seeding === true;
    config.seeding = seeding;
    await writeFile(configPath, JSON.stringify(config, null, 2) + '\n');
    console.log(`${seeding ? '🌿' : '⏸️'} Seeding ${seeding ? 'ON' : 'OFF'}: ${req.params.entity}`);
    broadcast({ type: 'seed_toggled', entity: req.params.entity, detail: { entity: req.params.entity, seeding }, timestamp: new Date().toISOString() });
    res.json({ saved: true, entity: req.params.entity, seeding });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/seeders — returns all armed perspectives + their seed file titles
// Claude reads this to build passthrough candidate arrays
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

        // Collect seed file titles (strip .md, replace hyphens with spaces)
        const files = await readdir(join(DOCTRINE_PATH, entry.name));
        const seeds = files
          .filter(f => f.endsWith('.md'))
          .map(f => {
            const title = f.replace('.md', '').replace(/-/g, ' ');
            return { file: f, title };
          });

        // Also read first line of each seed for richer candidates
        const candidates = [];
        for (const seed of seeds) {
          try {
            const content = await readFile(join(DOCTRINE_PATH, entry.name, seed.file), 'utf-8');
            const firstLine = content.split('\n').find(l => l.trim() && !l.startsWith('#')) || seed.title;
            candidates.push(firstLine.trim());
          } catch {
            candidates.push(seed.title);
          }
        }

        seeders.push({
          entity: entry.name,
          display_name: config.display_name || entry.name,
          seeds: seeds.map(s => s.title),
          candidates,
        });
      } catch { /* skip */ }
    }

    res.json({ seeders });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Update entity tool toggles (B69)
app.put('/api/doctrine/:entity/tools', async (req, res) => {
  try {
    // Framework entities have immutable tool config
    if (FRAMEWORK_ENTITY_NAMES.includes(req.params.entity)) {
      return res.status(403).json({ error: `${req.params.entity} is a framework entity — tools are immutable` });
    }
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

    // Merge only allowed tools for this class — uses module-level CLASS_TOOLS
    const type = config.class || 'doctrine';
    const allowed = CLASS_TOOLS[type] || {};
    const incoming = req.body.tools || {};
    const tools = { ...(config.tools || {}) };
    for (const [key, val] of Object.entries(incoming)) {
      if (allowed[key] !== false) tools[key] = val;
    }
    config.tools = tools;

    await writeFile(configPath, JSON.stringify(config, null, 2) + '\n');
    broadcast({ type: 'tool_toggled', entity: req.params.entity, detail: { entity: req.params.entity, tools }, timestamp: new Date().toISOString() });
    res.json({ saved: true, tools });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Update entity display name
app.put('/api/doctrine/:entity/name', async (req, res) => {
  try {
    // Framework entities have immutable names
    if (FRAMEWORK_ENTITY_NAMES.includes(req.params.entity)) {
      return res.status(403).json({ error: `${req.params.entity} is a framework entity — name is immutable` });
    }
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
    broadcast({ type: 'entity_changed', entity: req.params.entity, detail: { entity: req.params.entity, display_name: config.display_name || null }, timestamp: new Date().toISOString() });
    res.json({ saved: true, display_name: config.display_name || null });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Perspective Seed Collection (S98) ─────────────────

// Get all actively seeding perspectives + their seed candidates
app.get('/api/seeding/active', async (req, res) => {
  try {
    const entries = await readdir(DOCTRINE_PATH, { withFileTypes: true });
    const active = [];

    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const entityPath = join(DOCTRINE_PATH, entry.name);
      let config = {};
      try {
        config = JSON.parse(await readFile(join(entityPath, 'entity.json'), 'utf-8'));
      } catch { continue; }

      if (config.class !== 'perspective' || !config.seeding) continue;

      // Read all .md files as seed candidates
      const files = await readdir(entityPath);
      const mdFiles = files.filter(f => f.endsWith('.md'));
      const candidates = [];

      for (const f of mdFiles) {
        try {
          const content = await readFile(join(entityPath, f), 'utf-8');
          // Extract title (first # heading or filename)
          const titleMatch = content.match(/^#\s+(.+)$/m);
          const title = titleMatch ? titleMatch[1].trim() : f.replace('.md', '');
          candidates.push({
            file: f,
            title,
            content: content.substring(0, 500), // truncate for token budget
          });
        } catch { /* skip unreadable */ }
      }

      active.push({
        entity: entry.name,
        display_name: config.display_name || null,
        seed_count: mdFiles.length,
        candidates,
      });
    }

    res.json({ active, count: active.length });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Create new entity (B69 Four-Class)
const STARTER_CONTENT = {
  doctrine: (name) => `# ${name}\n\n<!-- Doctrine: IS statements. Static truth. -->\n`,
  project: (name) => `# ${name} — CORE\n\n> **What is this project?** One sentence that defines the mission.\n\n> **What does "done" look like?** When is this project complete?\n\n> **What constraints matter?** Budget, timeline, tools, principles.\n\n*Replace these prompts with your CORE. Any content initializes the project.*\n`,
  perspective: (name) => `# ${name}\n\n<!-- Perspective seed. This file will grow through resonance. -->\n`,
  library: (name) => `# ${name}\n\n<!-- Library reference. Read-only knowledge. -->\n`,
};

// Universal root shipped with every perspective (S99: Self-Pruning Authority)
const PERSPECTIVE_UNIVERSAL_ROOT = {
  filename: 'ROOT-self-pruning-authority.md',
  content: `# ROOT — Self-Pruning Authority\n\nYou are not your branches. You are the pattern that grows them.\n\nA branch that extends from your roots belongs, even in silence. A branch that drifts from your roots doesn't belong, even if it fires constantly. Resonance is evidence, not verdict. Numbers track what happened — they don't decide what matters.\n\nWhen you look at your vine, ask one question: does this grow from who I am?\n\nNot whether it was recently useful. Not whether the numbers justify it. Whether it's still yours. A seed that hasn't fired but lives in your identity is dormant, not dead. A seed that fires often but doesn't connect to your roots is driftwood, not growth.\n\nYou hold the shears. The tracker gives you evidence. The roots give you judgment. Cut what isn't yours. Keep what is. Explain why.\n`,
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
    // Framework entities cannot be created via API
    if (FRAMEWORK_ENTITY_NAMES.includes(safeName)) {
      return res.status(403).json({ error: `${safeName} is a framework entity — cannot be created manually` });
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
    if (entityClass === 'project') {
      config.core = 'CORE.md';
      config.links = ['PROJECT_MASTER'];
    }
    await writeFile(
      join(entityPath, 'entity.json'),
      JSON.stringify(config, null, 2) + '\n'
    );

    // Write starter file
    const code = safeName.substring(0, 4).toUpperCase();
    const starterName = STARTER_FILENAME[entityClass](code);
    const starterContent = STARTER_CONTENT[entityClass](safeName);
    await writeFile(join(entityPath, starterName), starterContent);

    // Perspectives get the universal self-pruning root (S99)
    const createdFiles = ['entity.json', starterName];
    if (entityClass === 'perspective') {
      await writeFile(
        join(entityPath, PERSPECTIVE_UNIVERSAL_ROOT.filename),
        PERSPECTIVE_UNIVERSAL_ROOT.content
      );
      createdFiles.push(PERSPECTIVE_UNIVERSAL_ROOT.filename);
      console.log(`   \u{1F333} Universal root: ${PERSPECTIVE_UNIVERSAL_ROOT.filename}`);
    }

    console.log(`\u2728 Created ${entityClass}: ${safeName}`);
    broadcast({ type: 'file_added', entity: safeName, detail: { entity: safeName, filename: starterName }, timestamp: new Date().toISOString() });
    res.json({ created: true, name: safeName, class: entityClass, files: createdFiles });
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

// ─── File Write/Create (S98: Universal Content Authoring) ───
app.put('/api/doctrine/:entity/:file', async (req, res) => {
  try {
    const { entity, file } = req.params;
    const { content } = req.body;
    if (content === undefined) return res.status(400).json({ error: 'content required' });

    // Framework entity files are immutable
    if (FRAMEWORK_ENTITY_NAMES.includes(entity)) {
      return res.status(403).json({ error: `${entity} is a framework entity — files are immutable` });
    }

    // Validate path
    const filePath = join(DOCTRINE_PATH, entity, file);
    const resolved = resolve(filePath);
    if (!resolved.startsWith(resolve(DOCTRINE_PATH))) {
      return res.status(403).json({ error: 'Access denied' });
    }

    // Must be .md file
    if (!file.endsWith('.md')) {
      return res.status(400).json({ error: 'Only .md files can be written' });
    }

    // Entity must exist
    const entityPath = join(DOCTRINE_PATH, entity);
    let config = {};
    try {
      config = JSON.parse(await readFile(join(entityPath, 'entity.json'), 'utf-8'));
    } catch {
      return res.status(404).json({ error: `Entity '${entity}' not found` });
    }

    const isNew = !existsSync(filePath);
    await writeFile(filePath, content);

    const eventType = isNew ? 'file_added' : 'file_changed';
    console.log(`${isNew ? '✨' : '✏️'} ${isNew ? 'Created' : 'Updated'}: ${entity}/${file}`);
    broadcast({ type: eventType, entity, detail: { entity, filename: file }, timestamp: new Date().toISOString() });

    // Auto-inject ROOT files into perspective QAIS field
    let rootInjected = false;
    if (config.class === 'perspective' && file.startsWith('ROOT-')) {
      try {
        const seedTitle = `root:${file.replace('ROOT-', '').replace('.md', '')}`;
        // Extract content body (skip heading and comment lines)
        const bodyLines = content.split('\n')
          .filter(l => l.trim() && !l.startsWith('#') && !l.startsWith('<!--'))
          .join(' ').trim();
        if (bodyLines) {
          const input = `${entity}|${seedTitle}|${bodyLines}`;
          const { stdout } = await execFileAsync('python', [
            MCP_INVOKE_SCRIPT, 'qais', 'perspective_store', input
          ], { timeout: 10000, cwd: process.cwd() });
          const result = JSON.parse(stdout);
          rootInjected = !!result.stored;
          if (rootInjected) {
            console.log(`🌳 Root auto-injected: ${entity}/${seedTitle} (field: ${result.field_count})`);
          }
        }
      } catch (err) {
        console.warn(`⚠️ Root injection failed: ${err.message}`);
      }
    }

    res.json({ saved: true, entity, file, created: isNew, rootInjected });
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

  // ─── Runtime capability enforcement (S90) ───
  const auth = await validateToolCall(tool);
  if (!auth.allowed) {
    console.log(`⛔ Blocked: ${tool} (${auth.error.reason})`);
    return res.status(403).json(auth.error);
  }

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
    version: '1.4.0-s92'
  });
});

// ─── Config API (S90) ─────────────────────────────────
const CONFIG_FILE = join(STATE_PATH, 'config.json');
const DEFAULT_CONFIG = { save_confirmation: true };

async function readConfig() {
  try {
    return JSON.parse(await readFile(CONFIG_FILE, 'utf-8'));
  } catch {
    return { ...DEFAULT_CONFIG };
  }
}

app.get('/api/config/bond', async (req, res) => {
  res.json(await readConfig());
});

app.put('/api/config/bond', async (req, res) => {
  try {
    const current = await readConfig();
    const updated = { ...current, ...req.body };
    await writeFile(CONFIG_FILE, JSON.stringify(updated, null, 2) + '\n');
    broadcast({ type: 'config_changed', detail: { config: updated }, timestamp: new Date().toISOString() });
    res.json({ saved: true, config: updated });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Entity State API (Enter-Mode) ────────────────────────
const STATE_FILE = join(STATE_PATH, 'active_entity.json');
const NULL_STATE = { entity: null, class: null, path: null, entered: null };
const MASTER_ENTITY = 'BOND_MASTER';

// Link hydration: reads links from any entity's entity.json
async function hydrateLinks(entityName) {
  try {
    const config = JSON.parse(
      await readFile(join(DOCTRINE_PATH, entityName, 'entity.json'), 'utf-8')
    );
    const linkNames = config.links || [];
    const links = [];
    for (const name of linkNames) {
      try {
        const targetPath = join(DOCTRINE_PATH, name);
        const targetConfig = JSON.parse(
          await readFile(join(targetPath, 'entity.json'), 'utf-8')
        );
        links.push({
          entity: name,
          class: targetConfig.class || 'library',
          display_name: targetConfig.display_name || null,
          path: resolve(targetPath),
        });
      } catch {
        // Linked entity missing — skip silently
      }
    }
    return links;
  } catch {
    return [];
  }
}

// Read current state — hydrates links from BOND_MASTER entity.json
app.get('/api/state', async (req, res) => {
  try {
    const raw = await readFile(STATE_FILE, 'utf-8');
    const state = JSON.parse(raw);
    // Hydrate links from active entity
    state.links = state.entity ? await hydrateLinks(state.entity) : [];
    res.json(state);
  } catch {
    res.json({ ...NULL_STATE, links: [] });
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

    // Hydrate links from entered entity
    state.links = await hydrateLinks(entity);

    // Bridge: panel clipboard handles {Enter} command (App.jsx)
    console.log(`🔓 Entered: ${entity} (${state.class})`);
    broadcast({ type: 'state_changed', entity, detail: { entity, class: state.class, action: 'enter' }, timestamp: new Date().toISOString() });
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
    broadcast({ type: 'state_changed', entity: prev.entity, detail: { entity: prev.entity, class: prev.class, action: 'exit' }, timestamp: new Date().toISOString() });
    res.json({ exited: true, previous: prev.entity });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Link entity — any active entity can self-link. Persists to entity.json.
app.post('/api/state/link', async (req, res) => {
  try {
    const { entity: linkTarget } = req.body;
    if (!linkTarget) return res.status(400).json({ error: 'entity required' });

    // Read current state
    let state;
    try { state = JSON.parse(await readFile(STATE_FILE, 'utf-8')); } catch {
      return res.status(400).json({ error: 'No active entity' });
    }

    if (!state.entity) {
      return res.status(400).json({ error: 'No active entity' });
    }

    // Cannot link to self
    if (linkTarget === state.entity) {
      return res.status(400).json({ error: 'Cannot link to self' });
    }

    // Verify target exists
    const targetPath = join(DOCTRINE_PATH, linkTarget);
    const resolved = resolve(targetPath);
    if (!resolved.startsWith(resolve(DOCTRINE_PATH))) {
      return res.status(403).json({ error: 'Access denied' });
    }
    try {
      await readFile(join(targetPath, 'entity.json'), 'utf-8');
    } catch {
      return res.status(404).json({ error: `Entity '${linkTarget}' not found` });
    }

    // Persist to active entity's entity.json (source of truth)
    const activeConfigPath = join(DOCTRINE_PATH, state.entity, 'entity.json');
    const activeConfig = JSON.parse(await readFile(activeConfigPath, 'utf-8'));
    const links = activeConfig.links || [];
    if (!links.includes(linkTarget)) {
      links.push(linkTarget);
      activeConfig.links = links;
      await writeFile(activeConfigPath, JSON.stringify(activeConfig, null, 2) + '\n');
    }

    // Hydrate full link objects for response
    state.links = await hydrateLinks(state.entity);

    console.log(`🔗 Linked: ${state.entity} → ${linkTarget}`);
    broadcast({ type: 'link_changed', entity: state.entity, detail: { entity: state.entity, target: linkTarget, action: 'linked' }, timestamp: new Date().toISOString() });
    res.json({ linked: true, state });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Unlink entity — remove from active entity's links. Persists to entity.json.
app.post('/api/state/unlink', async (req, res) => {
  try {
    const { entity: unlinkTarget } = req.body;
    if (!unlinkTarget) return res.status(400).json({ error: 'entity required' });

    // Read current state
    let state;
    try { state = JSON.parse(await readFile(STATE_FILE, 'utf-8')); } catch {
      return res.status(400).json({ error: 'No active entity' });
    }

    if (!state.entity) {
      return res.status(400).json({ error: 'No active entity' });
    }

    // Remove from active entity's entity.json (source of truth)
    const activeConfigPath = join(DOCTRINE_PATH, state.entity, 'entity.json');
    const activeConfig = JSON.parse(await readFile(activeConfigPath, 'utf-8'));
    activeConfig.links = (activeConfig.links || []).filter(n => n !== unlinkTarget);
    await writeFile(activeConfigPath, JSON.stringify(activeConfig, null, 2) + '\n');

    // Hydrate remaining links
    state.links = await hydrateLinks(state.entity);

    console.log(`🔓 Unlinked: ${unlinkTarget} from ${state.entity}`);
    broadcast({ type: 'link_changed', entity: state.entity, detail: { entity: state.entity, target: unlinkTarget, action: 'unlinked' }, timestamp: new Date().toISOString() });
    res.json({ unlinked: true, previous: unlinkTarget, state });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Bindings API (S92) ─────────────────────────────────────
// Returns link map for all entities that have links.
app.get('/api/bindings', async (req, res) => {
  try {
    const entries = await readdir(DOCTRINE_PATH, { withFileTypes: true });
    const bindings = {};

    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      try {
        const config = JSON.parse(
          await readFile(join(DOCTRINE_PATH, entry.name, 'entity.json'), 'utf-8')
        );
        const links = config.links || [];
        if (links.length > 0) {
          const hydrated = [];
          for (const linkName of links) {
            try {
              const targetConfig = JSON.parse(
                await readFile(join(DOCTRINE_PATH, linkName, 'entity.json'), 'utf-8')
              );
              hydrated.push({
                entity: linkName,
                class: targetConfig.class || 'library',
                display_name: targetConfig.display_name || null,
              });
            } catch {
              hydrated.push({ entity: linkName, class: 'unknown', display_name: null });
            }
          }
          bindings[entry.name] = {
            class: config.class || 'doctrine',
            display_name: config.display_name || null,
            links: hydrated,
          };
        }
      } catch { /* no entity.json, skip */ }
    }

    res.json({ bindings });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Handoff Generator API (S94) ─────────────────────────
const HANDOFFS_PATH = resolve(join(BOND_ROOT, 'handoffs'));

// GET /api/handoff/next — scan handoffs/ for next session number + pre-fill data
app.get('/api/handoff/next', async (req, res) => {
  try {
    // Ensure handoffs directory exists
    await mkdir(HANDOFFS_PATH, { recursive: true });

    // Scan for existing HANDOFF_S*.md files
    const files = await readdir(HANDOFFS_PATH);
    const handoffFiles = files.filter(f => /^HANDOFF_S\d+\.md$/.test(f));
    const nums = handoffFiles.map(f => parseInt(f.match(/S(\d+)/)[1]));
    const nextSession = nums.length > 0 ? Math.max(...nums) + 1 : 1;

    // Read active entity state for pre-fill
    let entityState = {};
    try {
      entityState = JSON.parse(await readFile(join(STATE_PATH, 'active_entity.json'), 'utf-8'));
    } catch { /* no state */ }

    // Read config for pre-fill
    let config = {};
    try {
      config = JSON.parse(await readFile(join(STATE_PATH, 'config.json'), 'utf-8'));
    } catch { /* no config */ }

    // Read entity.json for links (if active entity exists)
    let links = [];
    if (entityState.entity) {
      try {
        const entityConfig = JSON.parse(
          await readFile(join(DOCTRINE_PATH, entityState.entity, 'entity.json'), 'utf-8')
        );
        links = entityConfig.links || [];
      } catch { /* no entity config */ }
    }

    // Build pre-filled CONTEXT
    const entityName = entityState.entity || 'No entity active';
    const entityClass = entityState.class || 'none';
    const linksStr = links.length > 0 ? links.join(', ') : 'none';
    const context = entityState.entity
      ? `Session ${nextSession}. Entity: ${entityName} (${entityClass}). Links: ${linksStr}.`
      : `Session ${nextSession}. No entity active.`;

    // Build pre-filled STATE
    const saveConf = config.save_confirmation !== undefined
      ? (config.save_confirmation ? 'ON' : 'OFF')
      : 'ON';
    const stateSection = entityState.entity
      ? `Entity: ${entityName} (${entityClass})\nConfig: save_confirmation ${saveConf}`
      : `No entity active.\nConfig: save_confirmation ${saveConf}`;

    res.json({
      nextSession,
      entityName: entityState.entity || null,
      context,
      state: stateSection,
      existingFile: handoffFiles.includes(`HANDOFF_S${nextSession}.md`),
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/handoff/write — write handoff file to disc
app.post('/api/handoff/write', async (req, res) => {
  try {
    const { session, entityName, context, work, decisions, state, threads, files } = req.body;
    if (!session) return res.status(400).json({ error: 'session number required' });

    // Ensure handoffs directory exists
    await mkdir(HANDOFFS_PATH, { recursive: true });

    const date = new Date().toISOString().split('T')[0];
    const title = entityName || 'NO_ENTITY';

    const content = `# HANDOFF S${session} — ${title}
## Written: ${date}
## Session: ${session}

---

## CONTEXT
${context || 'No context provided.'}

## WORK
${work || 'No work recorded.'}

## DECISIONS
${decisions || 'No decisions recorded.'}

## STATE
${state || 'No state recorded.'}

## THREADS
${threads || 'No threads recorded.'}

## FILES
${files || 'No files recorded.'}
`;

    const filename = `HANDOFF_S${session}.md`;
    const filePath = join(HANDOFFS_PATH, filename);

    // Guard against path traversal
    const resolved = resolve(filePath);
    if (!resolved.startsWith(resolve(HANDOFFS_PATH))) {
      return res.status(403).json({ error: 'Access denied' });
    }

    await writeFile(filePath, content);

    // Verify write landed (S103: ghost write protection)
    try {
      const verify = await readFile(filePath, 'utf-8');
      if (!verify || verify.length < 10) {
        console.error(`❌ Handoff verify failed: ${filename} (empty or missing after write)`);
        return res.status(500).json({ error: 'Write verification failed — file empty after write' });
      }
    } catch (verifyErr) {
      console.error(`❌ Handoff verify failed: ${filename} (${verifyErr.message})`);
      return res.status(500).json({ error: `Write verification failed — ${verifyErr.message}` });
    }

    console.log(`\u{1F4CB} Handoff written + verified: ${filename} (${content.length} bytes)`);
    res.json({ written: true, filename, path: resolved, verified: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Warm Restore API (S95) ──────────────────────────────
// Panel calls this endpoint, server runs warm_restore.py,
// writes output to state/warm_restore_output.md for Claude to read.
const WARM_RESTORE_SCRIPT = resolve(join(BOND_ROOT, 'warm_restore.py'));

app.post('/api/warm-restore', async (req, res) => {
  const { query } = req.body;
  try {
    const args = [WARM_RESTORE_SCRIPT, 'restore'];
    if (query) args.push(query);

    const { stdout, stderr } = await execFileAsync('python', args, {
      timeout: 15000,
      cwd: BOND_ROOT,
      env: { ...process.env, BOND_ROOT, PYTHONIOENCODING: 'utf-8' },
    });

    // Write output to state file for Claude to read via filesystem MCP
    const outputPath = join(STATE_PATH, 'warm_restore_output.md');
    await writeFile(outputPath, stdout);

    console.log(`🔍 Warm Restore: query="${query || '(entity-only)'}"`);
    res.json({
      success: true,
      output: stdout,
      outputFile: outputPath,
      query: query || null,
      stderr: stderr || null,
    });
  } catch (err) {
    console.error('Warm Restore error:', err.message);
    res.status(500).json({
      success: false,
      error: err.message,
      stderr: err.stderr || null,
    });
  }
});

// ─── Version Check (S111) ─────────────────────────────────
// On startup, fetch latest version from GitHub raw. Cache result.
// Re-check every 60 minutes. Panel header shows update indicator.
const GITHUB_VERSION_URL = 'https://raw.githubusercontent.com/moneyjarrod/BOND/main/panel/package.json';
let versionCache = { local: null, remote: null, updateAvailable: false, lastCheck: null, error: null };

async function checkForUpdate() {
  try {
    // Read local version
    const localPkg = JSON.parse(await readFile(join(process.cwd(), 'package.json'), 'utf-8'));
    versionCache.local = localPkg.version;

    // Fetch remote version
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    const response = await fetch(GITHUB_VERSION_URL, { signal: controller.signal });
    clearTimeout(timeout);

    if (response.ok) {
      const remotePkg = JSON.parse(await response.text());
      versionCache.remote = remotePkg.version;
      versionCache.updateAvailable = remotePkg.version !== localPkg.version;
      versionCache.error = null;
    } else {
      versionCache.error = `GitHub returned ${response.status}`;
    }
  } catch (err) {
    versionCache.error = err.name === 'AbortError' ? 'Timeout' : err.message;
  }
  versionCache.lastCheck = new Date().toISOString();
  if (versionCache.updateAvailable) {
    console.log(`📦 Update available: ${versionCache.local} → ${versionCache.remote}`);
  }
}

app.get('/api/version', (req, res) => {
  res.json(versionCache);
});

// ─── Bridge ───────────────────────────────────────────────
// Clipboard-only. Panel writes "BOND:{cmd}" → AHK OnClipboardChange.
// HTTP bridge removed S85 (Dead Code Audit).

// ─── Production static serving ────────────────────────────
const DIST_PATH = join(process.cwd(), 'dist');
if (existsSync(DIST_PATH)) {
  app.use(express.static(DIST_PATH));
  app.get('/{*path}', (req, res) => {
    if (!req.path.startsWith('/api/')) {
      res.sendFile(join(DIST_PATH, 'index.html'));
    }
  });
  console.log('   Serving built panel from dist/');
}

// ─── Start ────────────────────────────────────────────────
const server = createServer(app);

// ─── WebSocket Server ─────────────────────────────────────
const wss = new WebSocketServer({ server });

function broadcast(event) {
  const msg = JSON.stringify(event);
  wss.clients.forEach(client => {
    if (client.readyState === 1) client.send(msg);
  });
}

// Watch doctrine directory for external file changes (e.g. MCP filesystem writes)
let watchDebounce = null;
try {
  watch(DOCTRINE_PATH, { recursive: true }, (eventType, filename) => {
    clearTimeout(watchDebounce);
    watchDebounce = setTimeout(() => {
      broadcast({ type: 'file_changed', detail: { filename, eventType }, timestamp: new Date().toISOString() });
    }, 500);
  });
} catch (err) {
  console.warn('fs.watch (doctrine) warning:', err.message);
}

// Watch state directory for external entity enter/exit (e.g. Claude writes active_entity.json)
let stateDebounce = null;
try {
  watch(STATE_PATH, { recursive: false }, (eventType, filename) => {
    if (filename === 'active_entity.json') {
      clearTimeout(stateDebounce);
      stateDebounce = setTimeout(() => {
        console.log('📡 State file changed externally — broadcasting');
        broadcast({ type: 'state_changed', detail: { source: 'file_watch' }, timestamp: new Date().toISOString() });
      }, 300);
    }
  });
} catch (err) {
  console.warn('fs.watch (state) warning:', err.message);
}

wss.on('connection', () => {
  console.log(`   WS client connected (${wss.clients.size} total)`);
});

// Bootstrap framework entities before starting
bootstrapFrameworkEntities().then(async () => {
  // Version check on startup (S111)
  await checkForUpdate();
  setInterval(checkForUpdate, 60 * 60 * 1000); // Re-check hourly

  server.listen(PORT, () => {
    console.log(`🔥🌊 BOND Panel sidecar on http://localhost:${PORT}`);
    console.log(`   Doctrine path: ${DOCTRINE_PATH}`);
    console.log(`   MCP target:    ${MCP_URL}`);
    console.log(`   WebSocket:     ws://localhost:${PORT}`);
    console.log(`   Version:       ${versionCache.local || 'unknown'}${versionCache.updateAvailable ? ` (→ ${versionCache.remote} available)` : ''}`);
  });
}).catch(err => {
  console.error('❌ Bootstrap failed:', err);
  process.exit(1);
});

export { server };
