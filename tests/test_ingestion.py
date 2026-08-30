from rag.ingestion import extract_section, infer_category
from rag.workflow import heuristic_category
from pathlib import Path


def test_category_from_path():
    assert infer_category(Path("docs/hr/policy.txt")) == "hr"
    assert infer_category(Path("docs/technical/api.txt")) == "technical"


def test_heading_extraction():
    assert extract_section("1. INCIDENT RESPONSE POLICY\n-----\nDetails") == "Incident Response Policy"


def test_heuristic_routing():
    assert heuristic_category("What happens after an HTTP 429 rate limit?") == "technical"
    assert heuristic_category("How many annual leave days do employees receive?") == "hr"
    assert heuristic_category("What is the GDPR breach deadline?") == "compliance"

