# Prompts

Prompts live here as versioned YAML files: `<name>/<version>.yaml`.

- **A merged version never changes.** To change a prompt, add the next version
  (`v2.yaml`) and set `SQL_PROMPT_VERSION=v2`. Old versions stay for comparison
  and rollback.
- **The SQL accuracy gate scores every change** before it merges. Score a
  candidate locally with `python evals/run_eval.py --prompt-version v2`.
- Templates use `{{ placeholder }}` tokens. A missing value raises an error
  instead of shipping a half-rendered prompt, and tests render every version.
- Each answer's API response includes `prompt_version`, and the metrics are
  labelled with it, so a rollout can be watched per version.

| Prompt | Versions | Notes |
|---|---|---|
| `sql_generation` | v1 | Baseline. 95% on the benchmark; misses revenue questions about cancelled subscriptions (rule 7 forces `is_active = TRUE`). |
