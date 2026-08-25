from collections import Counter

from src.techniques import REGISTRY, consensus


def test_registry_has_exactly_100_unique_balanced_techniques():
    assert len(REGISTRY) == 100
    assert len({item.id for item in REGISTRY}) == 100
    assert set(Counter(item.family for item in REGISTRY).values()) == {10}
    assert len({item.family for item in REGISTRY}) == 10


def test_consensus_reports_techniques_and_equal_weight_families():
    closes = [100 + index * .25 for index in range(300)]
    result = consensus(closes)
    assert result["techniques_total"] == 100
    assert len(result["results"]) == 100
    assert len(result["family_scores"]) == 10
    assert 0 <= result["bullish_families"] <= 10
    assert all(0 <= score <= 1 for score in result["family_scores"].values())


def test_family_vote_cannot_exceed_one_regardless_of_correlated_variants():
    closes = [100 + index * .25 for index in range(300)]
    result = consensus(closes)
    assert result["family_scores"]["price_sma"] == 1.0
    assert result["family_scores"]["absolute_momentum"] == 1.0
    assert result["bullish_families"] <= 10
