# Cursor Model Catalog

**Last updated:** 2026-01-07  
**Source of truth:** Kevin’s authoritative list (keep in sync with Cursor’s model picker)

This catalog lists available models in Cursor as of 2026-01-07. When writing or following agent prompts, **always specify** which model was used.

## Policy: 85% performance / 15% cost

When choosing a model for agent work, default to:
- **~85% performance/quality**
- **~15% cost**

Meaning: if you’re unsure, prefer the stronger model for correctness, then only downgrade for cost once the task risk is clearly low.

---

## Current models (2026-01-07)

The following models are available in Cursor's model picker:

### Claude models (Anthropic)
- **claude-4-sonnet-20250514** (Sonnet 4.5) — recommended for most tasks
- **claude-opus-4-20250514** (Opus 4)
- **claude-3.7-sonnet** (Sonnet 3.7)
- **claude-3.5-sonnet** (Sonnet 3.5)
- **claude-opus** (Opus 3)

### OpenAI models
- **gpt-5.2**
- **gpt-5-mini**
- **gpt-5-nano**
- **gpt-4o**
- **gpt-4o-mini**
- **o1**
- **o1-mini**

### DeepSeek models
- **deepseek-chat**
- **deepseek-reasoner**

### Google models
- **gemini-exp-1206**
- **gemini-2.0-flash-exp**

---

## Model selection guidance

### By task type

| Task type | Recommended model |
|-----------|-------------------|
| General coding / refactoring | claude-4-sonnet-20250514 (Sonnet 4.5) |
| Documentation / writing | claude-4-sonnet-20250514 (Sonnet 4.5) |
| Complex reasoning / architecture | claude-opus-4-20250514 (Opus 4) |
| Quick edits / simple tasks | gpt-5-mini (or gpt-4o-mini) |

### Family mapping (if exact model unavailable)

If you cannot find the exact model name in your Cursor instance, pick the closest family:

- **Sonnet family** → use latest `claude-X-sonnet` or `claude-X.X-sonnet`
- **Opus family** → use latest `claude-opus` or `claude-opus-X`
- **GPT family** → use `gpt-5-mini` / `gpt-5-nano` / `gpt-5.2` (or `gpt-4o` / `gpt-4o-mini`)
- **o1 family** → use `o1` or `o1-mini`
- **DeepSeek family** → use `deepseek-chat` or `deepseek-reasoner`
- **Gemini family** → use latest `gemini-X.X-flash-exp` or `gemini-exp-XXXX`

---

## MAX mode

**MAX mode** is a Cursor feature that enables:
- Extended context window
- More comprehensive analysis
- Higher token budget per response

### When to use MAX mode
- ✅ Large refactoring across multiple files
- ✅ Complex architectural decisions
- ✅ First pass of a new feature or module
- ✅ Debugging obscure issues requiring deep context

### When NOT to use MAX mode
- ❌ Simple edits or typo fixes
- ❌ Documentation updates (unless large-scale)
- ❌ Following a well-defined step-by-step plan
- ❌ Routine CI fixes

---

## Cycle count (1×–4×)

**Cycle count** refers to how many deliberate review/refinement passes the agent should make.

### 1× cycle (default)
- Make the changes once
- Run tests
- Deliver

### 2× cycle
- Make the changes
- Review your own work (self-critique)
- Refine / fix issues
- Run tests
- Deliver

### 3× cycle
- Make the changes
- Self-review (pass 1)
- Refactor for maintainability / edge-cases (pass 2)
- Run tests
- Deliver

### 4× cycle
- Everything in 3×, plus:
  - stronger “what could go wrong?” review (safety/rollback)
  - additional evidence (extra test coverage / repro notes)
  - tighten docs/process updates for future runs

**Use 2×–4× cycles for:**
- Critical path / high-risk changes
- New features with unclear requirements
- Refactoring that touches many files

---

## Required headers in prompts

Every agent prompt MUST include:

```markdown
## Model + MAX mode + Cycle
- **Model used:** claude-4-sonnet-20250514 (or specify exact model)
- **MAX mode:** ON | OFF
- **Cycle:** 1× | 2× | 3× | 4×
```

**Enforcement:**
- CI checks will warn if prompts are missing this section
- Archive prompts must preserve the model/mode/cycle metadata

---

## Notes

- This catalog will be updated as Cursor adds or deprecates models
- If you see a model not listed here, add it and update the date stamp
- Always check Cursor's model picker UI for the current list
- Model availability may vary by Cursor plan (Free / Pro / Business)

---

## References

- Cursor documentation: `https://docs.cursor.com/`
- OpenAI runtime model policy (non-Cursor): `docs/11_Governance_Continuous_Improvement/Model_Update_Policy.md`

