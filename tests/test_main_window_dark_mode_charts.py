"""Covers a real dark-mode bug found during the Kintsugi-redesign audit:
matplotlib charts and the server-health indicator used to read the light
PALETTE unconditionally, so they looked wrong (light figure background,
dark-on-dark text) whenever the app was in dark mode."""

import types

import shared.theme as theme
from matplotlib.figure import Figure

import views.main_window as mw
from shared.palette import DARK_PALETTE, PALETTE


class FakeClassManager:
    def __init__(self, healthy=True):
        self._healthy = healthy

    def check_server_health(self, *args, **kwargs):
        return self._healthy

    def flush_offline_queue(self, *args, **kwargs):
        return 0

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return []

    def get_student_table(self, class_id):
        return {
            "columns": ["Student Number", "Student Name Surname", "Not Attended Hours", "Attended Hours",
                        "01-09-2025 - 09:00-10:50"],
            "rows": [["1", "Grace Hopper", 0, 1, "1 Present"]],
        }


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def build_window(qtbot, monkeypatch, healthy=True):
    monkeypatch.setattr(mw, "ClassManager", lambda: FakeClassManager(healthy))
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)

    user = types.SimpleNamespace(user_id="u1", name="Ada", surname="Lovelace")
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    window._health_check_timer.stop()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    return window


def test_attendance_trend_follows_active_theme_by_default(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    cls = types.SimpleNamespace(class_id="c1")
    monkeypatch.setattr(theme, "load_theme_preference", lambda: "dark")

    figure = Figure()
    axes = figure.add_subplot(111)
    window._render_attendance_trend(axes, cls)

    assert axes.lines[0].get_color() == DARK_PALETTE["accent"]


def test_attendance_trend_uses_light_palette_when_explicitly_overridden(qtbot, monkeypatch):
    """export_statistics_pdf forces the light palette so exported reports
    stay print-friendly regardless of the app's active theme."""
    window = build_window(qtbot, monkeypatch)
    cls = types.SimpleNamespace(class_id="c1")
    monkeypatch.setattr(theme, "load_theme_preference", lambda: "dark")

    figure = Figure()
    axes = figure.add_subplot(111)
    window._render_attendance_trend(axes, cls, palette=PALETTE)

    assert axes.lines[0].get_color() == PALETTE["accent"]


def test_server_health_indicator_uses_dark_palette_in_dark_mode(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, healthy=True)
    monkeypatch.setattr(theme, "load_theme_preference", lambda: "dark")

    window.update_server_health_indicator()

    assert DARK_PALETTE["success"] in window.server_health_lbl.styleSheet()


def test_toggle_dark_mode_rebuilds_the_active_chart(qtbot, monkeypatch, tmp_path):
    window = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(mw, "stylesheet_path", lambda theme_name: str(tmp_path / "noop.qss"))
    (tmp_path / "noop.qss").write_text("")
    monkeypatch.setattr(mw, "save_theme_preference", lambda theme_name: None)

    calls = []
    window._last_chart_builder = lambda: calls.append(1)

    window.toggle_dark_mode(True)

    assert calls == [1]


def test_toggle_dark_mode_is_a_noop_when_no_chart_has_been_built(qtbot, monkeypatch, tmp_path):
    window = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(mw, "stylesheet_path", lambda theme_name: str(tmp_path / "noop.qss"))
    (tmp_path / "noop.qss").write_text("")
    monkeypatch.setattr(mw, "save_theme_preference", lambda theme_name: None)

    window.toggle_dark_mode(True)  # must not raise
