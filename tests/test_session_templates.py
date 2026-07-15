"""Covers #22: persisted attendance session templates."""

import shared.session_templates as stpl


def test_defaults_to_empty_template_when_no_file(monkeypatch, tmp_path):
    monkeypatch.setattr(stpl, "SESSION_TEMPLATES_PATH", tmp_path / "missing")
    assert stpl.load_session_template("c1") == {"time_slot": None, "late_threshold_override": None}


def test_save_then_load_round_trips(monkeypatch, tmp_path):
    path = tmp_path / ".session_templates.json"
    monkeypatch.setattr(stpl, "SESSION_TEMPLATES_PATH", path)

    stpl.save_session_template("c1", "09:00-10:50", 20)

    assert stpl.load_session_template("c1") == {
        "time_slot": "09:00-10:50", "late_threshold_override": 20,
    }


def test_templates_for_different_classes_are_independent(monkeypatch, tmp_path):
    path = tmp_path / ".session_templates.json"
    monkeypatch.setattr(stpl, "SESSION_TEMPLATES_PATH", path)

    stpl.save_session_template("c1", "09:00-10:50", 20)
    stpl.save_session_template("c2", "13:00-14:50", None)

    assert stpl.load_session_template("c1")["time_slot"] == "09:00-10:50"
    assert stpl.load_session_template("c2")["time_slot"] == "13:00-14:50"
    assert stpl.load_session_template("c2")["late_threshold_override"] is None


def test_invalid_json_falls_back_to_empty(tmp_path, monkeypatch):
    path = tmp_path / ".session_templates.json"
    path.write_text("not json")
    monkeypatch.setattr(stpl, "SESSION_TEMPLATES_PATH", path)

    assert stpl.load_session_template("c1") == {"time_slot": None, "late_threshold_override": None}
