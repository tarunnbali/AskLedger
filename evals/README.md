# SQL accuracy evals

A benchmark of 40 billing questions with known correct answers. Each question
goes through the real pipeline: the versioned prompt, Gemini, the SQL validator,
one self-correction attempt, then execution as a tenant under Row-Level Security.
The model's result is compared with a hand-written gold query's result
(*execution accuracy*: row order and extra columns don't matter).

```bash
python evals/run_eval.py --check-gold        # validate the benchmark itself, no Gemini
python evals/run_eval.py --sample            # 10 smoke questions (pull requests)
python evals/run_eval.py                     # all 40 (merges to main)
python evals/run_eval.py --prompt-version v2 # score a candidate prompt
```

Uses `TEST_ADMIN_DATABASE_URL` if set (CI), otherwise starts an embedded Postgres.
Needs `GEMINI_API_KEY` unless every prediction is already cached.

## The gate

The eval scores **one pinned model** (`baseline.json`'s, currently
`gemini-3.5-flash-lite`) with no fallback. The app falls back across models, but a
gate that scores whichever model is available that day can't tell a worse prompt
from a busy Gemini: the first run on `main` failed for exactly that reason, when
39 of 40 questions fell through to a smaller model.

The run fails if the score is below `max(--min-score, baseline - --tolerance)`,
with the baseline in [`baseline.json`](baseline.json). Reports break accuracy down
by the model that answered, and failures are posted as GitHub annotations. Gemini outages don't count as
wrong answers; if more than 20% of calls fail, the run is *inconclusive* (exit 2)
rather than pass or fail on noise.

Predictions are cached by prompt content + model list + question, so a pull
request that doesn't touch the prompt re-checks answers against a fresh database
without spending Gemini quota.

## Baseline: prompt v1

| Model | Score |
|---|---|
| `gemini-3.5-flash-lite` (pinned for the gate) | **90% (36/40)**, sample 10/10 |
| `gemini-3.6-flash` | 95% (38/40) |

Two misses come from one prompt rule: v1 tells the model to always filter
`sc.is_active = TRUE` on revenue questions, which is wrong for questions about
cancelled subscriptions. The lite model also asks for clarification on two
questions it should answer. Both are targets for prompt v2.
