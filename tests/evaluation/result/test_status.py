from __future__ import annotations

from t4_devkit.evaluation import MatchingStatus


def test_matching_status() -> None:
    # TP
    assert MatchingStatus.TP.is_true() and MatchingStatus.TP.is_positive()
    assert (not MatchingStatus.TP.is_false()) and (not MatchingStatus.TP.is_negative())

    # FP
    assert MatchingStatus.FP.is_false() and MatchingStatus.FP.is_positive()
    assert (not MatchingStatus.FP.is_true()) and (not MatchingStatus.FP.is_negative())

    # FN
    assert MatchingStatus.FN.is_false() and MatchingStatus.FN.is_negative()
    assert (not MatchingStatus.FN.is_true()) and (not MatchingStatus.FN.is_positive())

    # TN
    assert MatchingStatus.TN.is_true() and MatchingStatus.TN.is_negative()
    assert (not MatchingStatus.TN.is_false()) and (not MatchingStatus.TN.is_positive())
