"""Pure metric calculation functions for triage evaluation."""

from dataclasses import dataclass, field
from typing import Optional

from smart_dispatch.data.schemas import Severity
from smart_dispatch.data.golden_dataset import GoldenCase
from smart_dispatch.agents.triage.schemas import TriageResult


SEVERITY_ORDER = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]


def severity_distance(a: Severity, b: Severity) -> int:
    return abs(SEVERITY_ORDER.index(a) - SEVERITY_ORDER.index(b))


@dataclass
class TriageMetrics:
    total: int = 0
    type_correct: int = 0
    severity_correct: int = 0
    severity_within_one: int = 0
    location_correct: int = 0
    resources_exact_match: int = 0
    resources_superset: int = 0
    avg_confidence: float = 0.0

    type_confusion: dict = field(default_factory=dict)
    severity_confusion: dict = field(default_factory=dict)

    @property
    def type_accuracy(self) -> float:
        return self.type_correct / self.total if self.total else 0.0

    @property
    def severity_accuracy(self) -> float:
        return self.severity_correct / self.total if self.total else 0.0

    @property
    def severity_tolerance_accuracy(self) -> float:
        return self.severity_within_one / self.total if self.total else 0.0

    @property
    def location_accuracy(self) -> float:
        return self.location_correct / self.total if self.total else 0.0

    @property
    def resources_exact_rate(self) -> float:
        return self.resources_exact_match / self.total if self.total else 0.0


@dataclass
class DedupMetrics:
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    true_negatives: int = 0

    @property
    def precision(self) -> float:
        tp, fp = self.true_positives, self.false_positives
        return tp / (tp + fp) if (tp + fp) else 0.0

    @property
    def recall(self) -> float:
        tp, fn = self.true_positives, self.false_negatives
        return tp / (tp + fn) if (tp + fn) else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0


def evaluate_triage_case(case: GoldenCase, result: TriageResult) -> dict:
    exp = case.expected
    type_ok = result.incident_type == exp.incident_type
    sev_ok = result.severity == exp.severity
    sev_dist = severity_distance(result.severity, exp.severity)

    loc_lower = (result.location_raw or "").lower()
    loc_ok = any(kw.lower() in loc_lower for kw in exp.location_keywords)

    expected_set = set(exp.resources_needed)
    actual_set = set(result.resources_needed)
    resources_exact = expected_set == actual_set
    resources_superset = expected_set.issubset(actual_set)

    return {
        "call_id": case.call.call_id,
        "type_ok": type_ok,
        "severity_ok": sev_ok,
        "severity_distance": sev_dist,
        "location_ok": loc_ok,
        "resources_exact": resources_exact,
        "resources_superset": resources_superset,
        "expected_type": exp.incident_type.value,
        "actual_type": result.incident_type.value,
        "expected_severity": exp.severity.value,
        "actual_severity": result.severity.value,
        "confidence": result.llm_confidence,
    }


def aggregate_triage(cases_and_results: list[tuple[GoldenCase, TriageResult]]) -> TriageMetrics:
    m = TriageMetrics()
    conf_sum = 0.0
    for case, result in cases_and_results:
        r = evaluate_triage_case(case, result)
        m.total += 1
        if r["type_ok"]:
            m.type_correct += 1
        if r["severity_ok"]:
            m.severity_correct += 1
        if r["severity_distance"] <= 1:
            m.severity_within_one += 1
        if r["location_ok"]:
            m.location_correct += 1
        if r["resources_exact"]:
            m.resources_exact_match += 1
        if r["resources_superset"]:
            m.resources_superset += 1
        conf_sum += r["confidence"]

        tc_key = (r["expected_type"], r["actual_type"])
        m.type_confusion[tc_key] = m.type_confusion.get(tc_key, 0) + 1
        sc_key = (r["expected_severity"], r["actual_severity"])
        m.severity_confusion[sc_key] = m.severity_confusion.get(sc_key, 0) + 1

    m.avg_confidence = conf_sum / m.total if m.total else 0.0
    return m


def evaluate_dedup(
    cases_and_results: list[tuple[GoldenCase, TriageResult]],
) -> DedupMetrics:
    """Compare agent dedup decisions against golden ground truth."""
    m = DedupMetrics()
    for case, result in cases_and_results:
        expected_dup = case.expected.is_duplicate_of is not None
        actual_dup = result.is_duplicate
        if expected_dup and actual_dup:
            m.true_positives += 1
        elif not expected_dup and actual_dup:
            m.false_positives += 1
        elif expected_dup and not actual_dup:
            m.false_negatives += 1
        else:
            m.true_negatives += 1
    return m
