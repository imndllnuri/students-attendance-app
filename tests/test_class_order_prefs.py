"""Covers #7: persisted drag-and-drop custom class ordering."""

import shared.class_order as co


def test_defaults_to_empty_list_when_no_preference_file(monkeypatch, tmp_path):
    monkeypatch.setattr(co, "CLASS_ORDER_PREFERENCE_PATH", tmp_path / "missing")
    assert co.load_class_order() == []


def test_save_then_load_round_trips(monkeypatch, tmp_path):
    pref_path = tmp_path / ".class_order_preference"
    monkeypatch.setattr(co, "CLASS_ORDER_PREFERENCE_PATH", pref_path)

    co.save_class_order(["c3", "c1", "c2"])

    assert co.load_class_order() == ["c3", "c1", "c2"]


def test_invalid_json_falls_back_to_empty_list(tmp_path, monkeypatch):
    pref_path = tmp_path / ".class_order_preference"
    pref_path.write_text("not json")
    monkeypatch.setattr(co, "CLASS_ORDER_PREFERENCE_PATH", pref_path)

    assert co.load_class_order() == []


def test_non_list_json_falls_back_to_empty_list(tmp_path, monkeypatch):
    pref_path = tmp_path / ".class_order_preference"
    pref_path.write_text('{"not": "a list"}')
    monkeypatch.setattr(co, "CLASS_ORDER_PREFERENCE_PATH", pref_path)

    assert co.load_class_order() == []
