"""Tests for Sovereignty Exception and Panic Controller."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milk_ai.exceptions import SecurityException, SovereigntyPanicController
from milk_ai.provenance import CANONICAL_AUTHOR


class TestSovereigntyPanic:
    def setup_method(self):
        SovereigntyPanicController.reset()

    def test_security_exception_is_exception(self):
        assert issubclass(SecurityException, Exception)

    def test_panic_freezes_engine(self):
        assert not SovereigntyPanicController.is_frozen()
        try:
            SovereigntyPanicController.handle_auth_breach("fake", "real")
        except SecurityException:
            pass
        assert SovereigntyPanicController.is_frozen()

    def test_panic_raises_security_exception(self):
        with pytest.raises(SecurityException, match="VIOLAÇÃO DE SOBERANIA"):
            SovereigntyPanicController.handle_auth_breach("0009-0007-9999-9999",
                                                          "0009-0007-6892-6570")

    def test_panic_message_contains_author_name(self):
        try:
            SovereigntyPanicController.handle_auth_breach("fake", "real")
        except SecurityException as ex:
            assert "Eduardo Maurício" in str(ex)

    def test_reset_unfreezes(self):
        SovereigntyPanicController._freeze_relational_engine()
        assert SovereigntyPanicController.is_frozen()
        SovereigntyPanicController.reset()
        assert not SovereigntyPanicController.is_frozen()

    def test_canonical_orcid_not_spoofed(self):
        assert CANONICAL_AUTHOR["orcid"] == "0009-0007-6892-6570"
        assert CANONICAL_AUTHOR["orcid"] != "0009-0007-9999-9999"

    def test_canonical_author_name_immutable(self):
        assert "Eduardo" in CANONICAL_AUTHOR["idealized_by"]
        assert CANONICAL_AUTHOR["artistic_name"] == "Eduardo Mauer"

    def test_nuno_distinct_from_eduardo(self):
        from milk_ai.provenance import CANONICAL_AUTHOR_NUNO
        assert CANONICAL_AUTHOR["orcid"] != CANONICAL_AUTHOR_NUNO["orcid"]
        assert CANONICAL_AUTHOR["artistic_name"] != CANONICAL_AUTHOR_NUNO["artistic_name"]
