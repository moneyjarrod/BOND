/**
 * S103 Fix: Remove inline PROJECT_MASTER .md files from FRAMEWORK_ENTITIES
 * 
 * Problem: server.js has full inline copies of PROJECT_MASTER.md and 
 * PROJECT_BOUNDARIES.md in FRAMEWORK_ENTITIES. These shorter versions 
 * shadow the richer template versions in templates/doctrine/PROJECT_MASTER/.
 * The inline writes first (bootstrap), template skips because file exists.
 *
 * Fix: Empty the files object for PROJECT_MASTER. Templates become canonical.
 * Bootstrap still creates entity dir + entity.json (config stays inline).
 * Template copy block then writes the .md files on first boot.
 *
 * Run once: node fix_pm_template.js
 * Delete after: this is a one-time migration script.
 */

import { readFile, writeFile } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SERVER_PATH = join(__dirname, 'panel', 'server.js');

async function fix() {
  const content = await readFile(SERVER_PATH, 'utf-8');
  
  // Find the PROJECT_MASTER files block
  const pmStart = content.indexOf("  PROJECT_MASTER: {");
  if (pmStart === -1) throw new Error("PROJECT_MASTER not found in FRAMEWORK_ENTITIES");
  
  // Find the `files: {` after PM config
  const pmFilesStart = content.indexOf("    files: {", pmStart);
  if (pmFilesStart === -1) throw new Error("PROJECT_MASTER files block not found");
  
  // Find the closing of FRAMEWORK_ENTITIES: `const FRAMEWORK_ENTITY_NAMES`
  const fwEnd = content.indexOf("const FRAMEWORK_ENTITY_NAMES");
  if (fwEnd === -1) throw new Error("FRAMEWORK_ENTITY_NAMES marker not found");
  
  // Walk backwards from fwEnd to find `};` that closes FRAMEWORK_ENTITIES
  const closingBrace = content.lastIndexOf("};", fwEnd);
  if (closingBrace === -1) throw new Error("FRAMEWORK_ENTITIES closing brace not found");
  
  // Replace: from pmFilesStart to closingBrace + 2 (include `};`)
  const before = content.substring(0, pmFilesStart);
  const after = content.substring(closingBrace + 2);
  
  const replacement = `    // .md files sourced from templates/doctrine/PROJECT_MASTER/ (S103)
    // Richer versions with Authority Chain + IS Statements sections.
    // Bootstrap creates dir + entity.json, template copy writes .md files.
    files: {},
  },
};`;

  const result = before + replacement + after;
  
  // Sanity checks
  if (!result.includes('BOND_MASTER')) throw new Error("Lost BOND_MASTER!");
  if (!result.includes('PROJECT_MASTER')) throw new Error("Lost PROJECT_MASTER!");
  if (!result.includes('const FRAMEWORK_ENTITY_NAMES')) throw new Error("Lost FRAMEWORK_ENTITY_NAMES!");
  if (result.includes("'PROJECT_MASTER.md':")) throw new Error("Inline PM content still present!");
  if (result.includes("'PROJECT_BOUNDARIES.md':")) throw new Error("Inline PB content still present!");
  if (!result.includes("'BOND_MASTER.md':")) throw new Error("Lost BOND_MASTER inline file!");
  
  await writeFile(SERVER_PATH, result);
  
  const linesBefore = content.split('\n').length;
  const linesAfter = result.split('\n').length;
  console.log(`✅ Fixed: ${linesBefore} → ${linesAfter} lines (removed ${linesBefore - linesAfter} inline lines)`);
  console.log(`   PROJECT_MASTER .md files now sourced from templates/`);
  console.log(`   BOND_MASTER inline file preserved`);
  console.log(`\n   Verify: open server.js and check PROJECT_MASTER has files: {}`);
}

fix().catch(err => {
  console.error(`❌ ${err.message}`);
  process.exit(1);
});
