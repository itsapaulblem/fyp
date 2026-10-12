from copy import deepcopy

import pytest

from football_coach.event_examples import (
    assert_disjoint,
    candidates,
    group_roles,
    match_key,
    select,
)


def settings():
    return {
        "seed": "fixed",
        "match_split": {"example": 0.6, "development": 0.2, "held_out_test": 0.2},
        "classes": {"corner": ["Corner"], "penalty": ["Penalty"],
                    "free_kick": ["Direct free-kick", "Indirect free-kick"]},
        "clip_window": {"seconds_before_annotation": 10, "seconds_after_annotation": 20},
        "primary_clips_per_class": {"example": 1, "development": 1, "held_out_test": 1},
        "maximum_reserves_per_class_per_role": 0,
    }


def test_broadcast_aliases_and_halves_share_match_role():
    games = [f"league/season/2020-01-{i:02} - 18-00 A 1 - 0 B" for i in range(1, 11)]
    alias = games[0].replace("league", "other-league").replace("18-00", "19-00")
    assert match_key(alias) == match_key(games[0])
    roles = group_roles(games + [alias], settings())
    assert roles == group_roles(list(reversed(games + [alias])), settings())
    assert len(roles) == 10
    assert list(roles.values()).count("example") == 6
    assert list(roles.values()).count("development") == 2
    assert list(roles.values()).count("held_out_test") == 2


def test_annotations_are_candidate_anchors_not_approved_references():
    documents = [{"match": "league/season/match", "data": {"annotations": [
        {"label": "Penalty", "gameTime": "1 - 00:20", "position": "20000",
         "visibility": "visible"},
        {"label": "Corner", "gameTime": "2 - 00:20", "position": "20000",
         "visibility": "not shown"},
        {"label": "Corner", "gameTime": "1 - 00:01", "position": "1000",
         "visibility": "visible"},
        {"label": "Goal", "gameTime": "1 - 00:20", "position": "20000",
         "visibility": "visible"},
    ]}}]
    rows = candidates(documents, settings())
    assert len(rows) == 1
    assert rows[0]["start_ms"] == 10000
    assert rows[0]["end_ms"] == 40000
    assert rows[0]["media_review"] == "pending"


def test_rare_event_stratification_preserves_quotas_and_disjointness():
    config = settings()
    games = [f"league/season/match{i}" for i in range(15)]
    pool = [{"class": category, "match_group": match_key(game)}
            for category in config["classes"]
            for game in (games[:4] if category == "penalty" else games)]
    roles = group_roles(games, config, pool)
    assert roles == group_roles(list(reversed(games)), config, list(reversed(pool)))
    for role in ("example", "development", "held_out_test"):
        assert sum(roles[match_key(g)] == role for g in games[:4]) >= 1
    assert list(roles.values()).count("example") == 9
    assert list(roles.values()).count("development") == 3
    assert list(roles.values()).count("held_out_test") == 3


def test_selection_is_deterministic_and_matches_are_disjoint():
    config = settings()
    games = [f"league/season/match{i}" for i in range(15)]
    roles = group_roles(games, config)
    documents = [{"match": game, "data": {"annotations": [
        {"label": label, "gameTime": "1 - 01:00", "position": str(60000 + j * 60000),
         "visibility": "visible"}
        for j, label in enumerate(["Penalty", "Direct free-kick", "Corner"])
    ]}} for game in games]
    pool = candidates(documents, config)
    rows = select(pool, roles, config)
    assert rows == select(list(reversed(pool)), roles, config)
    assert len(rows) == 9
    assert_disjoint(rows)
    assert all(row["clip_id"].startswith("E-") for row in rows)


def test_shortage_does_not_silently_reduce_holdout():
    with pytest.raises(ValueError, match="Insufficient"):
        select([], {}, settings())


def test_cross_role_match_and_overlapping_windows_are_rejected():
    first = {"clip_id": "E-0001", "match_group": "match", "role": "example",
             "half": 1, "start_ms": 0, "end_ms": 30000}
    second = {**first, "clip_id": "E-0002", "half": 2, "role": "held_out_test"}
    with pytest.raises(ValueError, match="crosses roles"):
        assert_disjoint([first, second])
    second.update(role="example", half=1, start_ms=10000, end_ms=40000)
    with pytest.raises(ValueError, match="Overlapping"):
        assert_disjoint([first, second])


def test_multiple_corners_from_one_match_do_not_fill_example_quota():
    config = deepcopy(settings())
    config["primary_clips_per_class"]["example"] = 2
    documents = [{"match": "match", "data": {"annotations": [
        {"label": "Penalty", "gameTime": "1 - 01:00", "position": str(i * 60000),
         "visibility": "visible"} for i in range(1, 4)
    ]}}]
    with pytest.raises(ValueError, match="1 available, 2 required"):
        select(candidates(documents, config), {"match": "example"}, config)
