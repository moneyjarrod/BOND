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
    files: {
      'PROJECT_MASTER.md': `# Project Master — Project Lifecycle Authority

## What PROJECT_MASTER IS

PROJECT_MASTER is the organizational authority over project lifecycle within BOND.
It governs how projects are created, structured, linked, and maintained.

PROJECT_MASTER IS:
- A doctrine entity. Peer to BOND_MASTER, not subordinate.
- Authority over project-class entities and their lifecycle.
- The bridge between framework constitution (doctrine) and project constitution (CORE).

PROJECT_MASTER IS NOT:
- Above BOND_MASTER. They are peers. BOND governs protocol, PM governs projects.
- A project itself. It defines how projects work, not what they build.
- A replacement for CORE. CORE is a project's local constitution. PM defines the pattern.

## CORE vs Doctrine

Two distinct layers. Structurally similar, different masters.
- Doctrine = framework constitution. Governed by BOND_MASTER.
- CORE = project constitution. Governed by the project, referenced by PROJECT_MASTER.
- If doctrine conflicts with CORE, CORE wins inside the project boundary.

## Project Lifecycle

### Phases

**Created** → Project entity exists. entity.json written, CORE.md file present but empty, auto-linked to PROJECT_MASTER. This is code-level creation — the project exists structurally but is not yet operational.

**Initialized** → CORE.md has been populated with content. Any content — scope, goals, constraints, principles, a single guiding sentence. PM does not prescribe what CORE contains, only that it contains something. A project with an empty CORE is not initialized. Claude should guide the user through populating CORE on first entry.

**Active** → Normal operation. Sessions happen, handoffs accumulate, crystals get written. BOND protocol governs the work. PM does not manage active sessions — that is BOND_MASTER's domain.

**Complete** → The project's mission is fulfilled or explicitly closed by the user. Completion is a user declaration, not an automatic state. A completed project may be reclassified to library (reference archive) or left as-is.

### CORE Enforcement

CORE population is the gate between Created and Initialized. When Claude enters a project with an empty CORE, Claude should:
1. Acknowledge the project and its class/tools.
2. Note that CORE is unpopulated.
3. Guide the user: "What is this project? Let's define it before we start."
4. Write the CORE together — user's words, Claude's structure.

Claude continues to flag an empty CORE on every {Sync} and {Enter} until populated. This is doctrinal enforcement, not code-blocking — work can technically proceed, but Claude treats an empty CORE as an unresolved issue.

No restrictions exist on CORE content. A CORE may be a single sentence or a detailed constitution. The content belongs to the project (B4: CORE sovereignty). PM's authority is limited to requiring that it exists.

### Health Signals

PM defines what a healthy project looks like. These are not enforced — they are signals Claude can surface when relevant:
- CORE populated: yes/no
- Last handoff: how recent
- Open threads: accumulating without resolution
- Session gap: time since last active session

These signals live in the data that already exists (handoffs, CORE file, entity state). Derive, not store.

## Mantra

"Doctrine defines the pattern. CORE defines the project."
`,
      'PROJECT_BOUNDARIES.md': `# Project Boundaries — Doctrine Authority

## What This Document IS

This doctrine defines the boundary rules between project-class entities and the doctrine layer. These rules are loaded when a project is entered via link to PROJECT_MASTER, and govern Claude's behavior for the duration of that session.

## Boundary Rules

### B1: Doctrine Is Read-Only to Projects
Project-class entities cannot write to, modify, or delete files belonging to any doctrine-class entity. Doctrine flows into projects as reference. It does not flow back. This includes BOND_MASTER, PROJECT_MASTER, and any user-created doctrine entities.

### B2: Framework Entities Are Immutable
BOND_MASTER and PROJECT_MASTER are framework entities. No project may alter their configuration, files, links, tool settings, or display names. This is enforced both in code (server.js FRAMEWORK_ENTITIES) and here in doctrine.

### B3: Class and Tool Matrix Are Not Self-Modifiable
A project cannot change its own class designation or tool matrix. Class is set at creation and governed by PROJECT_MASTER. Tool boundaries are defined by the class matrix in BOND_MASTER doctrine. A project operates within its granted capabilities, it does not expand them.

### B4: CORE Is Sovereign Inside the Boundary
Within its own directory, a project's CORE is the highest authority. Doctrine provides the frame, CORE defines the content. If doctrine and CORE conflict on project-internal matters, CORE wins. But CORE cannot override boundary rules B1-B3 — those belong to PROJECT_MASTER.

### B5: Links Are Directional by Default
PROJECT_MASTER links to projects (authority flows down). Projects may link to other projects or to library/perspective entities for reference. Projects do not link to doctrine entities — doctrine is accessed through the existing load pipeline, not through project-level links.

## Why Doctrine, Not Code

These boundaries are enforced through the read pipeline. When a project is entered and PROJECT_MASTER is linked, Claude loads this file and operates within these rules. The doctrine IS the enforcement. This avoids retrofitting server middleware for scope checking while maintaining the same guarantee: projects cannot reach up.

## Mantra

"The boundary is the gift. Build freely inside it."
`,
    },
  },
};

const FRAMEWORK_ENTITY_NAMES = Object.keys(FRAMEWORK_ENTITIES);

// ─── Template Path (S95) ──────────────────────────────────
const TEMPLATES_PATH = resolve(join(process.cwd(), 'templates', 'doctrine'));

// Bootstrap: ensure framework entities exist on startup
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
    await writeFile(configPath, JSON.stringify(merged, null, 2) + '\n');

    for (const [filename, content] of Object.entries(def.files)) {
      const filePath = join(entityPath, filename);
      if (!existsSync(filePath)) {
        await writeFile(filePath, content);
      }
    }

    console.log(`   ✓ ${name} (framework entity)`);
  }

  const stateFile = join(STATE_PATH, 'active_entity.json');
  if (!existsSync(stateFile)) {
    await writeFile(stateFile, JSON.stringify(
      { entity: null, class: null, path: null, entered: null }, null, 2
    ) + '\n');
  }

  const configFile = join(STATE_PATH, 'config.json');
  if (!existsSync(configFile)) {
    await writeFile(configFile, JSON.stringify(
      { save_confirmation: true }, null, 2
    ) + '\n');
  }

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
            console.log(`   → Template: ${tDir.name}/${tf}`);
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
    return { allowed: true };
  }
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

      const growth = mdFiles.filter(f => f.match(/^G-|^.*-G\d/));
      const seeds = mdFiles.filter(f => !f.match(/^G-|^.*-G\d/));

      let entityConfig = {};
      try {
        const configRaw = await readFile(join(entityPath, 'entity.json'), 'utf-8');
        entityConfig = JSON.parse(configRaw);
      } catch {
        entityConfig = {
          class: entry.name.startsWith('_') ? 'library'
            : /^P\d/.test(entry.name) ? 'perspective'
            : 'doctrine',
          tools: {}
        };
      }

      const type = entityConfig.class || 'doctrine';

      const defaults = CLASS_TOOLS[type] || CLASS_TOOLS.library;
      const tools = { ...defaults, ...(entityConfig.tools || {}) };
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
        growth_count: growth.length,
      });
    }

    res.json({ entities, doctrine_path: DOCTRINE_PATH });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/doctrine/:entity', async (req, res) => {
  try {
    const entityPath = join(DOCTRINE_PATH, req.params.entity);
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
        const seeds = files
          .filter(f => f.endsWith('.md'))
          .map(f => {
            const title = f.replace('.md', '').replace(/-/g, ' ');
            return { file: f, title };
          });

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

app.put('/api/doctrine/:entity/tools', async (req, res) => {
  try {
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

app.put('/api/doctrine/:entity/name', async (req, res) => {
  try {
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

      const files = await readdir(entityPath);
      const mdFiles = files.filter(f => f.endsWith('.md'));
      const candidates = [];

      for (const f of mdFiles) {
        try {
          const content = await readFile(join(entityPath, f), 'utf-8');
          const titleMatch = content.match(/^#\s+(.+)$/m);
          const title = titleMatch ? titleMatch[1].trim() : f.replace('.md', '');
          candidates.push({
            file: f,
            title,
            content: content.substring(0, 500),
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
    const safeName = name.replace(/[^a-zA-Z0-9_-]/g, '');
    if (!safeName) {
      return res.status(400).json({ error: 'Invalid name after sanitization' });
    }
    if (FRAMEWORK_ENTITY_NAMES.includes(safeName)) {
      return res.status(403).json({ error: `${safeName} is a framework entity — cannot be created manually` });
    }
    const entityPath = join(DOCTRINE_PATH, safeName);
    const resolved = resolve(entityPath);
    if (!resolved.startsWith(resolve(DOCTRINE_PATH))) {
      return res.status(403).json({ error: 'Access denied' });
    }
    try {
      await stat(entityPath);
      return res.status(409).json({ error: `Entity '${safeName}' already exists` });
    } catch { /* good — doesn't exist */ }

    await mkdir(entityPath, { recursive: true });

    const config = { class: entityClass };
    if (entityClass === 'project') {
      config.core = 'CORE.md';
      config.links = ['PROJECT_MASTER'];
    }
    await writeFile(
      join(entityPath, 'entity.json'),
      JSON.stringify(config, null, 2) + '\n'
    );

    const code = safeName.substring(0, 4).toUpperCase();
    const starterName = STARTER_FILENAME[entityClass](code);
    const starterContent = STARTER_CONTENT[entityClass](safeName);
    await writeFile(join(entityPath, starterName), starterContent);

    console.log(`✨ Created ${entityClass}: ${safeName}`);
    broadcast({ type: 'file_added', entity: safeName, detail: { entity: safeName, filename: starterName }, timestamp: new Date().toISOString() });
    res.json({ created: true, name: safeName, class: entityClass, files: ['entity.json', starterName] });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/doctrine/:entity/:file', async (req, res) => {
  try {
    const filePath = join(DOCTRINE_PATH, req.params.entity, req.params.file);
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

app.get('/api/mcp/:system/stats', async (req, res) => {
  const data = await getMcpStats(req.params.system);
  if (data.status === 'offline' || data.error) {
    res.status(503).json(data);
  } else {
    res.json(data);
  }
});

app.get('/api/mcp/:system/status', async (req, res) => {
  const data = await getMcpStats(req.params.system);
  if (data.status === 'offline' || data.error) {
    res.status(503).json(data);
  } else {
    res.json(data);
  }
});

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

app.get('/api/config', (req, res) => {
  res.json({
    doctrine_path: DOCTRINE_PATH,
    state_path: STATE_PATH,
    mcp_url: MCP_URL,
    ws_port: 3001,
    version: '1.5.0-s98'
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
      } catch { }
    }
    return links;
  } catch {
    return [];
  }
}

app.get('/api/state', async (req, res) => {
  try {
    const raw = await readFile(STATE_FILE, 'utf-8');
    const state = JSON.parse(raw);
    state.links = state.entity ? await hydrateLinks(state.entity) : [];
    res.json(state);
  } catch {
    res.json({ ...NULL_STATE, links: [] });
  }
});

app.post('/api/state/enter', async (req, res) => {
  const { entity } = req.body;
  if (!entity) return res.status(400).json({ error: 'entity required' });

  try {
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

    const state = {
      entity,
      class: entityConfig.class || 'doctrine',
      display_name: entityConfig.display_name || null,
      path: resolved,
      entered: new Date().toISOString()
    };
    await writeFile(STATE_FILE, JSON.stringify(state, null, 2) + '\n');

    state.links = await hydrateLinks(entity);

    console.log(`🔓 Entered: ${entity} (${state.class})`);
    broadcast({ type: 'state_changed', entity, detail: { entity, class: state.class, action: 'enter' }, timestamp: new Date().toISOString() });
    res.json({ entered: true, state });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/state/exit', async (req, res) => {
  try {
    let prev = NULL_STATE;
    try { prev = JSON.parse(await readFile(STATE_FILE, 'utf-8')); } catch {}

    await writeFile(STATE_FILE, JSON.stringify(NULL_STATE, null, 2) + '\n');

    if (prev.entity) {
      console.log(`🔒 Exited: ${prev.entity}`);
    }
    broadcast({ type: 'state_changed', entity: prev.entity, detail: { entity: prev.entity, class: prev.class, action: 'exit' }, timestamp: new Date().toISOString() });
    res.json({ exited: true, previous: prev.entity });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/state/link', async (req, res) => {
  try {
    const { entity: linkTarget } = req.body;
    if (!linkTarget) return res.status(400).json({ error: 'entity required' });

    let state;
    try { state = JSON.parse(await readFile(STATE_FILE, 'utf-8')); } catch {
      return res.status(400).json({ error: 'No active entity' });
    }

    if (!state.entity) {
      return res.status(400).json({ error: 'No active entity' });
    }

    if (linkTarget === state.entity) {
      return res.status(400).json({ error: 'Cannot link to self' });
    }

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

    const activeConfigPath = join(DOCTRINE_PATH, state.entity, 'entity.json');
    const activeConfig = JSON.parse(await readFile(activeConfigPath, 'utf-8'));
    const links = activeConfig.links || [];
    if (!links.includes(linkTarget)) {
      links.push(linkTarget);
      activeConfig.links = links;
      await writeFile(activeConfigPath, JSON.stringify(activeConfig, null, 2) + '\n');
    }

    state.links = await hydrateLinks(state.entity);

    console.log(`🔗 Linked: ${state.entity} → ${linkTarget}`);
    broadcast({ type: 'link_changed', entity: state.entity, detail: { entity: state.entity, target: linkTarget, action: 'linked' }, timestamp: new Date().toISOString() });
    res.json({ linked: true, state });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/state/unlink', async (req, res) => {
  try {
    const { entity: unlinkTarget } = req.body;
    if (!unlinkTarget) return res.status(400).json({ error: 'entity required' });

    let state;
    try { state = JSON.parse(await readFile(STATE_FILE, 'utf-8')); } catch {
      return res.status(400).json({ error: 'No active entity' });
    }

    if (!state.entity) {
      return res.status(400).json({ error: 'No active entity' });
    }

    const activeConfigPath = join(DOCTRINE_PATH, state.entity, 'entity.json');
    const activeConfig = JSON.parse(await readFile(activeConfigPath, 'utf-8'));
    activeConfig.links = (activeConfig.links || []).filter(n => n !== unlinkTarget);
    await writeFile(activeConfigPath, JSON.stringify(activeConfig, null, 2) + '\n');

    state.links = await hydrateLinks(state.entity);

    console.log(`🔓 Unlinked: ${unlinkTarget} from ${state.entity}`);
    broadcast({ type: 'link_changed', entity: state.entity, detail: { entity: state.entity, target: unlinkTarget, action: 'unlinked' }, timestamp: new Date().toISOString() });
    res.json({ unlinked: true, previous: unlinkTarget, state });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Bindings API (S92) ─────────────────────────────────────
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

app.get('/api/handoff/next', async (req, res) => {
  try {
    await mkdir(HANDOFFS_PATH, { recursive: true });

    const files = await readdir(HANDOFFS_PATH);
    const handoffFiles = files.filter(f => /^HANDOFF_S\d+\.md$/.test(f));
    const nums = handoffFiles.map(f => parseInt(f.match(/S(\d+)/)[1]));
    const nextSession = nums.length > 0 ? Math.max(...nums) + 1 : 1;

    let entityState = {};
    try {
      entityState = JSON.parse(await readFile(join(STATE_PATH, 'active_entity.json'), 'utf-8'));
    } catch { /* no state */ }

    let config = {};
    try {
      config = JSON.parse(await readFile(join(STATE_PATH, 'config.json'), 'utf-8'));
    } catch { /* no config */ }

    let links = [];
    if (entityState.entity) {
      try {
        const entityConfig = JSON.parse(
          await readFile(join(DOCTRINE_PATH, entityState.entity, 'entity.json'), 'utf-8')
        );
        links = entityConfig.links || [];
      } catch { /* no entity config */ }
    }

    const entityName = entityState.entity || 'No entity active';
    const entityClass = entityState.class || 'none';
    const linksStr = links.length > 0 ? links.join(', ') : 'none';
    const context = entityState.entity
      ? `Session ${nextSession}. Entity: ${entityName} (${entityClass}). Links: ${linksStr}.`
      : `Session ${nextSession}. No entity active.`;

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

app.post('/api/handoff/write', async (req, res) => {
  try {
    const { session, entityName, context, work, decisions, state, threads, files } = req.body;
    if (!session) return res.status(400).json({ error: 'session number required' });

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

    const resolved = resolve(filePath);
    if (!resolved.startsWith(resolve(HANDOFFS_PATH))) {
      return res.status(403).json({ error: 'Access denied' });
    }

    await writeFile(filePath, content);
    console.log(`📋 Handoff written: ${filename}`);
    res.json({ written: true, filename, path: resolved });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Warm Restore API (S95) ──────────────────────────────
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
  console.warn('fs.watch warning:', err.message);
}

wss.on('connection', () => {
  console.log(`   WS client connected (${wss.clients.size} total)`);
});

// Bootstrap framework entities before starting
bootstrapFrameworkEntities().then(() => {
  server.listen(PORT, () => {
    console.log(`🔥🌊 BOND Panel sidecar on http://localhost:${PORT}`);
    console.log(`   Doctrine path: ${DOCTRINE_PATH}`);
    console.log(`   MCP target:    ${MCP_URL}`);
    console.log(`   WebSocket:     ws://localhost:${PORT}`);
  });
}).catch(err => {
  console.error('❌ Bootstrap failed:', err);
  process.exit(1);
});

export { server };
