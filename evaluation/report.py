"""Render EvalReport as markdown and JSON."""

import json
from pathlib import Path

from .evaluator import EvalReport


def render_markdown(report: EvalReport) -> str:
    t = report.triage
    d = report.dedup
    lines = [
        "# Triage Agent Evaluation Report",
        "",
        f"- **LLM:** {report.llm_provider} / {report.llm_model}",
        f"- **Cases evaluated:** {t.total}",
        f"- **Total time:** {report.total_time_sec:.1f}s",
        "",
        "## Triage Accuracy",
        "",
        "| Metric | Score |",
        "|--------|-------|",
        f"| Incident type accuracy | **{t.type_accuracy:.1%}** ({t.type_correct}/{t.total}) |",
        f"| Severity exact match | **{t.severity_accuracy:.1%}** ({t.severity_correct}/{t.total}) |",
        f"| Severity within 1 level | **{t.severity_tolerance_accuracy:.1%}** ({t.severity_within_one}/{t.total}) |",
        f"| Location match (any keyword) | **{t.location_accuracy:.1%}** ({t.location_correct}/{t.total}) |",
        f"| Resources exact match | **{t.resources_exact_rate:.1%}** ({t.resources_exact_match}/{t.total}) |",
        f"| Avg LLM confidence | {t.avg_confidence:.2f} |",
        "",
        "## Deduplication",
        "",
        "| Metric | Score |",
        "|--------|-------|",
        f"| Precision | **{d.precision:.1%}** |",
        f"| Recall | **{d.recall:.1%}** |",
        f"| F1 | **{d.f1:.1%}** |",
        f"| True positives | {d.true_positives} |",
        f"| False positives | {d.false_positives} |",
        f"| False negatives | {d.false_negatives} |",
        f"| True negatives | {d.true_negatives} |",
        "",
        "## Type Confusion Matrix",
        "",
        "| Expected → Actual | Count |",
        "|-------------------|-------|",
    ]
    for (exp, act), count in sorted(t.type_confusion.items(), key=lambda x: -x[1]):
        marker = " ✅" if exp == act else " ❌"
        lines.append(f"| {exp} → {act}{marker} | {count} |")

    lines.extend([
        "",
        "## Per-Case Details",
        "",
        "| Call ID | Expected Type | Actual | Sev Expected | Sev Actual | Dup? | Latency |",
        "|---------|---------------|--------|--------------|------------|------|---------|",
    ])
    for c in report.per_case:
        if "error" in c:
            lines.append(f"| {c['call_id']} | ERROR | {c['error'][:40]} | - | - | - | - |")
        else:
            type_ok = "✅" if c["expected_type"] == c["actual_type"] else "❌"
            sev_ok = "✅" if c["expected_severity"] == c["actual_severity"] else "~"
            dup = "DUP" if c["is_duplicate_actual"] else ""
            lat = f"{c.get('latency_ms', 0):.0f}ms"
            lines.append(
                f"| {c['call_id'][:12]} "
                f"| {c['expected_type']} "
                f"| {c['actual_type']}{type_ok} "
                f"| {c['expected_severity']} "
                f"| {c['actual_severity']}{sev_ok} "
                f"| {dup} "
                f"| {lat} |"
            )

    return "\n".join(lines)


def save_report(report: EvalReport, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "eval_report.md"
    json_path = out_dir / "eval_report.json"
    md_path.write_text(render_markdown(report))
    json_path.write_text(json.dumps({
        "triage": {
            "total": report.triage.total,
            "type_accuracy": report.triage.type_accuracy,
            "severity_accuracy": report.triage.severity_accuracy,
            "severity_within_one": report.triage.severity_tolerance_accuracy,
            "location_accuracy": report.triage.location_accuracy,
            "resources_exact_rate": report.triage.resources_exact_rate,
            "avg_confidence": report.triage.avg_confidence,
            "type_confusion": {
                f"{k[0]}->{k[1]}": v for k, v in report.triage.type_confusion.items()
            },
            "severity_confusion": {
                f"{k[0]}->{k[1]}": v for k, v in report.triage.severity_confusion.items()
            },
        },
        "dedup": {
            "precision": report.dedup.precision,
            "recall": report.dedup.recall,
            "f1": report.dedup.f1,
            "true_positives": report.dedup.true_positives,
            "false_positives": report.dedup.false_positives,
            "false_negatives": report.dedup.false_negatives,
            "true_negatives": report.dedup.true_negatives,
        },
        "per_case": report.per_case,
        "total_time_sec": report.total_time_sec,
        "llm_provider": report.llm_provider,
        "llm_model": report.llm_model,
    }, indent=2, default=str))
    return md_path, json_path
