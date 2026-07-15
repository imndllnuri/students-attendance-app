from dataclasses import dataclass
from typing import Dict, List, Optional

from PyQt5.QtCore import QTime

from services.api_client import ApiClient, ApiError


@dataclass
class ScheduleSlot:
    day: str
    start_time: QTime
    end_time: QTime
    selected: bool


class Class:
    def __init__(self, class_code: str, class_name: str, instructor_id: str, section: str,
                 attendance_policy: float, late_threshold: int, total_weeks: int,
                 total_hours: float, weekly_hours: float, schedule: Dict[str, List[ScheduleSlot]],
                 class_id: Optional[str] = None, students: Optional[List[dict]] = None,
                 archived: bool = False):
        self.class_id = class_id
        self.class_code = class_code
        self.class_name = class_name
        self.instructor_id = instructor_id
        self.section = section
        self.attendance_policy = attendance_policy
        self.late_threshold = late_threshold
        self.total_weeks = total_weeks
        self.total_hours = total_hours
        self.weekly_hours = weekly_hours
        self.schedule = schedule
        self.students = students or []
        self.archived = archived

    def to_dict(self):
        return {
            "class_code": self.class_code,
            "class_name": self.class_name,
            "instructor_id": self.instructor_id,
            "section": self.section,
            "attendance_policy": self.attendance_policy,
            "late_threshold": self.late_threshold,
            "total_weeks": self.total_weeks,
            "total_hours": self.total_hours,
            "weekly_hours": self.weekly_hours,
            "schedule": {
                day: [
                    {
                        "start_time": slot.start_time.toString("HH:mm"),
                        "end_time": slot.end_time.toString("HH:mm"),
                        "selected": slot.selected,
                    }
                    for slot in slots
                ]
                for day, slots in self.schedule.items()
            },
            "students": self.students,
        }

    @classmethod
    def from_dict(cls, data):
        schedule = {
            day: [
                ScheduleSlot(
                    day=day,
                    start_time=QTime.fromString(slot["start_time"], "HH:mm"),
                    end_time=QTime.fromString(slot["end_time"], "HH:mm"),
                    selected=slot["selected"],
                )
                for slot in slots
            ]
            for day, slots in data["schedule"].items()
        }

        return cls(
            class_code=data["class_code"],
            class_name=data["class_name"],
            instructor_id=data["instructor_id"],
            section=data["section"],
            attendance_policy=data["attendance_policy"],
            late_threshold=data["late_threshold"],
            total_weeks=data["total_weeks"],
            total_hours=data["total_hours"],
            weekly_hours=data["weekly_hours"],
            schedule=schedule,
            class_id=data.get("class_id"),
            archived=data.get("archived", False),
        )


class ClassManager:
    """Thin wrapper around the attendance server's class endpoints."""

    def __init__(self, api_client=None):
        self.api_client = api_client or ApiClient()
        self.classes: List[Class] = []

    def load_classes_for_instructor(self, instructor_id: str, include_archived: bool = False) -> List[Class]:
        try:
            data = self.api_client.list_classes(instructor_id, include_archived=include_archived)
        except ApiError:
            return []
        self.classes = [Class.from_dict(c) for c in data]
        return self.classes

    def add_class(self, new_class: Class) -> None:
        """Raises ApiError (e.g. duplicate class code) on failure."""
        data = self.api_client.create_class(new_class.to_dict())
        new_class.class_id = data["class_id"]
        self.classes.append(new_class)

    def update_class(self, class_id: str, fields: dict) -> dict:
        """Raises ApiError (e.g. class not found) on failure."""
        return self.api_client.update_class(class_id, fields)

    def archive_class(self, class_id: str) -> bool:
        try:
            self.update_class(class_id, {"archived": True})
        except ApiError:
            return False
        return True

    def unarchive_class(self, class_id: str) -> bool:
        try:
            self.update_class(class_id, {"archived": False})
        except ApiError:
            return False
        return True

    def delete_class(self, class_id: str) -> bool:
        try:
            self.api_client.delete_class(class_id)
        except ApiError:
            return False
        self.classes = [c for c in self.classes if c.class_id != class_id]
        return True

    def get_class_by_code(self, class_code: str) -> Optional[Class]:
        return next((cls for cls in self.classes if cls.class_code == class_code), None)

    # --- Roster / attendance / statistics ---
    # Proxied so views never need to touch ApiClient directly.

    def get_student_table(self, class_id: str) -> dict:
        return self.api_client.get_student_table(class_id)

    def get_roster(self, class_id: str) -> list:
        return self.api_client.get_roster(class_id)

    def add_student(self, class_id: str, student_number: str, name_surname: str) -> dict:
        """Raises ApiError on failure."""
        return self.api_client.add_student(class_id, student_number, name_surname)

    def remove_student(self, student_id) -> bool:
        try:
            self.api_client.remove_student(student_id)
        except ApiError:
            return False
        return True

    def register_card(self, student_id: str, card_id: str) -> None:
        self.api_client.register_card(student_id, card_id)

    def submit_attendance(self, class_id: str, records: list) -> None:
        self.api_client.submit_attendance(class_id, records)

    def get_statistics(self, class_id: str) -> dict:
        return self.api_client.get_statistics(class_id)

    def get_attendance_sheet(self, class_id: str, date: str) -> list:
        return self.api_client.get_attendance_sheet(class_id, date)
