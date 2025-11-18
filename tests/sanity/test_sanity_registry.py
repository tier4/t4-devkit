from __future__ import annotations

from t4_devkit.sanity.checker import RuleID
from t4_devkit.sanity.registry import RuleGroup


def test_rule_group_to_group() -> None:
    """Test the RuleGroup.to_group method."""
    # valid rule IDs
    assert RuleGroup.to_group(RuleID("STR000")) == RuleGroup.STRUCTURE
    assert RuleGroup.to_group(RuleID("REC000")) == RuleGroup.RECORD
    assert RuleGroup.to_group(RuleID("REF000")) == RuleGroup.REFERENCE
    assert RuleGroup.to_group(RuleID("FMT000")) == RuleGroup.FORMAT
    assert RuleGroup.to_group(RuleID("TIV000")) == RuleGroup.TIERIV
    # invalid rule IDs
    assert RuleGroup.to_group(RuleID("FOO000")) is None
    assert RuleGroup.to_group(RuleID("")) is None
