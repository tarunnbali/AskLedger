"""
SQL accuracy gate.

Asks every benchmark question through the real SQL pipeline (versioned prompt ->
Gemini -> validator -> one self-correction attempt -> query as the tenant, under
RLS) and compares the result with the gold query's result.

  python evals/run_eval.py --check-gold          # gold queries only, no Gemini
  python evals/run_eval.py --sample               # the smoke subset (pull requests)
  python evals/run_eval.py                        # full benchmark (main)
  python evals/run_eval.py --prompt-version v2    # score a candidate prompt

Exit codes: 0 pass, 1 accuracy below the gate, 2 inconclusive (too many Gemini
failures to judge), 3 broken benchmark (a gold query failed).
"""
import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import yaml

import harness

EVALS = Path(__file__).resolve().parent
MAX_LLM_ERROR_SHARE = 0.2


def load_questions(sample: bool) -> list[dict]:
    qs = yaml.safe_load((EVALS / "questions.yaml").read_text())["questions"]
    ids = [q["id"] for q in qs]
    assert len(ids) == len(set(ids)), "duplicate question ids"
    return [q for q in qs if q.get("smoke")] if sample else qs


def check_gold(questions: list[dict]) -> int:
    failures = 0
    for q in questions:
        try:
            rows = harness.run_as_tenant(q["gold"])
            status = "ok" if rows else "EMPTY (a benchmark answer must not be empty)"
            failures += not rows
        except Exception as e:  # noqa: BLE001
            status, failures = f"ERROR {type(e).__name__}: {e}", failures + 1
        print(f"  {q['id']:<24} {status}")
    print(f"\n{len(questions) - failures}/{len(questions)} gold queries valid")
    return 0 if failures == 0 else 3


class PredictionCache:
    """Predictions keyed by prompt content, model list and question."""

    def __init__(self, path: Path):
        self.path = path
        self.data = json.loads(path.read_text()) if path.exists() else {}

    @staticmethod
    def key(*parts: str) -> str:
        return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=1, sort_keys=True))


def evaluate(questions, prompt, models: str, cache: PredictionCache, delay: float) -> list[dict]:
    import openai

    from app.services.nl_to_sql_service import fix_sql, generate_sql

    results = []
    for q in questions:
        key = PredictionCache.key(prompt.sha256, models, q["question"])
        entry = cache.data.get(key, {})
        outcome = {"id": q["id"], "question": q["question"], "cached": bool(entry)}
        try:
            if "sql" not in entry:
                entry["sql"] = generate_sql(q["question"], [], prompt)
                time.sleep(delay)
            sql = entry["sql"]
            outcome["sql"] = sql
            if sql.upper().startswith("CLARIFICATION_NEEDED:"):
                outcome.update(status="wrong", reason="asked for clarification")
            else:
                try:
                    pred = harness.run_as_tenant(sql)
                except Exception as e:  # noqa: BLE001 — mirror the app: one self-correction attempt
                    if "fixed_sql" not in entry:
                        entry["fixed_sql"] = fix_sql(q["question"], sql, str(e), prompt)
                        time.sleep(delay)
                    outcome["fixed_sql"] = entry["fixed_sql"]
                    pred = harness.run_as_tenant(entry["fixed_sql"])
                gold = harness.run_as_tenant(q["gold"])
                ok = harness.results_match(gold, pred, ordered=q.get("ordered", False))
                outcome.update(status="correct" if ok else "wrong", reason="" if ok else "result differs from gold")
        except openai.APIError as e:
            outcome.update(status="llm_error", reason=f"{type(e).__name__}")
        except Exception as e:  # noqa: BLE001 — bad SQL even after the fix attempt
            outcome.update(status="wrong", reason=f"{type(e).__name__}: {str(e).splitlines()[0][:120]}")
        cache.data[key] = entry
        results.append(outcome)
        mark = {"correct": "PASS", "wrong": "FAIL", "llm_error": "SKIP"}[outcome["status"]]
        print(f"  {mark}  {q['id']:<24} {outcome.get('reason', '')}", flush=True)
    return results


def write_summary(report: dict, results: list[dict]):
    lines = [
        f"### SQL accuracy: {report['score']:.0%} ({report['correct']}/{report['judged']})",
        f"Prompt `{report['prompt_version']}` · gate {report['required']:.0%} · {report['verdict']}",
        "",
        "| Question | Result | Reason |",
        "|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r['id']} | {r['status']} | {r.get('reason', '')} |")
    text = "\n".join(lines) + "\n"
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt-version", help="prompt to score (default: the app's SQL_PROMPT_VERSION)")
    ap.add_argument("--sample", action="store_true", help="only the smoke questions")
    ap.add_argument("--check-gold", action="store_true", help="validate gold queries only (no Gemini)")
    ap.add_argument("--min-score", type=float, default=0.75, help="absolute floor (default 0.75)")
    ap.add_argument("--tolerance", type=float, default=0.05, help="allowed drop below the baseline (default 0.05)")
    ap.add_argument("--baseline", type=Path, default=EVALS / "baseline.json")
    ap.add_argument("--cache", type=Path, default=EVALS / ".cache" / "predictions.json")
    ap.add_argument("--report", type=Path, default=EVALS / "reports" / "latest.json")
    ap.add_argument("--delay", type=float, default=3.0, help="seconds between Gemini calls (free-tier rate limits)")
    args = ap.parse_args()

    questions = load_questions(args.sample)
    print(f"Preparing benchmark database ({len(questions)} questions)...", flush=True)
    harness.prepare_database()

    if args.check_gold:
        return check_gold(questions)

    from app.core.config import settings
    from app.prompts.registry import load_prompt

    version = args.prompt_version or settings.SQL_PROMPT_VERSION
    prompt = load_prompt("sql_generation", version)
    cache = PredictionCache(args.cache)
    print(f"Scoring prompt {version} with models {settings.GEMINI_SQL_MODELS}\n", flush=True)
    try:
        results = evaluate(questions, prompt, settings.GEMINI_SQL_MODELS, cache, args.delay)
    finally:
        cache.save()

    correct = sum(r["status"] == "correct" for r in results)
    llm_errors = sum(r["status"] == "llm_error" for r in results)
    judged = len(results) - llm_errors
    score = correct / judged if judged else 0.0

    baseline = json.loads(args.baseline.read_text()) if args.baseline.exists() else {}
    key = "sample" if args.sample else "full"
    required = max(args.min_score, baseline.get(key, 0.0) - args.tolerance)

    if llm_errors > MAX_LLM_ERROR_SHARE * len(results):
        verdict, code = f"INCONCLUSIVE: {llm_errors} Gemini failures", 2
    elif score < required:
        verdict, code = "FAILED", 1
    else:
        verdict, code = "PASSED", 0

    report = {
        "prompt_version": version, "prompt_sha256": prompt.sha256, "models": settings.GEMINI_SQL_MODELS,
        "mode": key, "questions": len(results), "judged": judged, "correct": correct, "llm_errors": llm_errors,
        "score": round(score, 4), "required": round(required, 4), "baseline": baseline.get(key),
        "verdict": verdict, "results": results,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2))
    write_summary(report, results)
    print(f"\nScore {score:.1%} ({correct}/{judged}), required {required:.1%} -> {verdict}")
    return code


if __name__ == "__main__":
    sys.exit(main())
