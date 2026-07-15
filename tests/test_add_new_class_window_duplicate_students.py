"""Covers #17: duplicate student-number detection at roster upload time."""

import pandas as pd

import views.add_new_class_window as acw
from models.classes import ClassManager


def build_window(qtbot, monkeypatch):
    monkeypatch.setattr(acw, "ClassManager", ClassManager)
    window = acw.AddNewClassWindow("instr-1")
    qtbot.addWidget(window)
    return window


def make_df(rows):
    # Columns: 0,1 unused; 2,3 -> student number; 4,5,6 -> name parts.
    return pd.DataFrame(rows, columns=[0, 1, 2, 3, 4, 5, 6])


def test_no_duplicates_loads_silently(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(acw.QFileDialog, "getOpenFileName", lambda *a, **k: ("roster.csv", ""))
    monkeypatch.setattr(acw.pd, "read_csv", lambda *a, **k: make_df([
        ["", "", "2023", "0001", "Grace", "Hopper", ""],
        ["", "", "2023", "0002", "Alan", "Turing", ""],
    ]))
    warned = []
    monkeypatch.setattr(acw.QMessageBox, "warning", lambda *a, **k: warned.append(True))
    monkeypatch.setattr(acw.QMessageBox, "information", lambda *a, **k: None)

    window.load_spreadsheet()

    assert warned == []
    assert len(window.students) == 2


def test_duplicate_student_numbers_prompt_before_loading(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(acw.QFileDialog, "getOpenFileName", lambda *a, **k: ("roster.csv", ""))
    monkeypatch.setattr(acw.pd, "read_csv", lambda *a, **k: make_df([
        ["", "", "2023", "0001", "Grace", "Hopper", ""],
        ["", "", "2023", "0001", "Grace", "H.", ""],  # duplicate number, different row
    ]))
    monkeypatch.setattr(acw.QMessageBox, "information", lambda *a, **k: None)

    warnings = []
    monkeypatch.setattr(acw.QMessageBox, "warning", lambda *a, **k: warnings.append(a) or acw.QMessageBox.No)

    window.load_spreadsheet()

    assert len(warnings) == 1
    assert window.students == []  # declined -> nothing loaded


def test_confirming_duplicate_warning_loads_anyway(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(acw.QFileDialog, "getOpenFileName", lambda *a, **k: ("roster.csv", ""))
    monkeypatch.setattr(acw.pd, "read_csv", lambda *a, **k: make_df([
        ["", "", "2023", "0001", "Grace", "Hopper", ""],
        ["", "", "2023", "0001", "Grace", "H.", ""],
    ]))
    monkeypatch.setattr(acw.QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(acw.QMessageBox, "warning", lambda *a, **k: acw.QMessageBox.Yes)

    window.load_spreadsheet()

    assert len(window.students) == 2
