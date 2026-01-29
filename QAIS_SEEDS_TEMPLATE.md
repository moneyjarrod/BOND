# QAIS Seeds Template
### Quick-Reference Format for SKILL.md

*Compact identity encoding for instant recall*

---

## Format

```
Entity:role=fact,role=fact,role=fact
```

**Rules:**
- One entity per line
- Multiple roles separated by commas
- Multiple values for same role: use `|` (pipe)
- Keep facts short (2-5 words)

---

## Example Seeds Section

Add to your SKILL.md:

```markdown
## QAIS Seeds

Query: entity:role → fact. Multi-value: `|` separated.

ProjectName:type=web app,stack=React|Node,stage=beta
Alice:role=lead dev,loc=Seattle,expertise=backend|APIs
Bob:role=designer,loc=remote,tools=Figma|Sketch
CoreDB:def=main database,tech=PostgreSQL,size=50GB
AuthSystem:def=login flow,method=OAuth|JWT,status=stable
Sprint1:goal=MVP launch,deadline=March,blockers=none
```

---

## Common Roles

| Role | Use For | Examples |
|------|---------|----------|
| `def` | Definitions | "main database", "core algorithm" |
| `role` | Person's role | "lead dev", "consultant" |
| `loc` | Location | "Seattle", "remote", "building-3" |
| `type` | Category | "web app", "service", "library" |
| `tech` | Technology | "React", "PostgreSQL", "AWS" |
| `status` | Current state | "stable", "beta", "deprecated" |
| `bf` | Bonfire reference | "B12", "B45" |
| `prin` | Principle | "separation of concerns" |
| `form` | Formula/format | "y = mx + b" |
| `rel` | Relationship | "cousin", "partner", "depends-on" |

---

## Storing in QAIS Field

To populate QAIS MCP with your seeds, tell Claude:

```
Store these in QAIS:
- ProjectName, type, web app
- ProjectName, stack, React
- ProjectName, stack, Node
- Alice, role, lead dev
- Alice, expertise, backend
```

Or ask Claude to parse your seeds section and store them automatically.

---

## Seeds vs QAIS Field

| SKILL Seeds | QAIS Field |
|-------------|------------|
| Always in context | Queried on demand |
| Pattern matching | True resonance |
| ~5 tokens per fact | ~0 tokens until queried |
| Instant but approximate | Precise with confidence |

**Recommendation:** Use both.
- Seeds for core identities Claude should always know
- QAIS field for extended knowledge Claude can query

---

## Migration

If you have existing seeds, you can bulk-load them to QAIS:

```
Parse my SKILL seeds and store each identity-role-fact in QAIS.
```

Claude will call `qais_store` for each binding.

---

🔥 Part of BOND Protocol | J-Dub & Claude | 2026
