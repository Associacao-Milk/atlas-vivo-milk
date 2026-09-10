"""Pytest configuration — exclude standalone certification scripts from collection.

test_neural_certification.py is a standalone certification SCRIPT (module-level
execution + sys.exit), not a unit-test module; collecting it raises SystemExit
(INTERNALERROR). It has no `def test_*` functions, so ignoring it from
collection is correct. It still runs as `python tests/test_neural_certification.py`.
"""
collect_ignore = ["test_neural_certification.py", "test_sovereign_core_gate.py"]
