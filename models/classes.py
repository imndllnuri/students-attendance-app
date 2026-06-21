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
                 class_id: Optional[str] = None, students: Optional[List[dict]] = None):
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
        )


class ClassManager:
    """Thin wrapper around the attendance server's class endpoints."""

    def __init__(self, api_client=None):
        self.api_client = api_client or ApiClient()
        self.classes: List[Class] = []

    def load_classes_for_instructor(self, instructor_id: str) -> List[Class]:
        try:
            data = self.api_client.list_classes(instructor_id)
        except ApiError:
            return []
        self.classes = [Class.from_dict(c) for c in data]
        return self.classes

    def add_class(self, new_class: Class) -> None:
        """Raises ApiError (e.g. duplicate class code) on failure."""
        data = self.api_client.create_class(new_class.to_dict())
        new_class.class_id = data["class_id"]
        self.classes.append(new_class)

    def delete_class(self, class_id: str) -> bool:
        try:
            self.api_client.delete_class(class_id)
        except ApiError:
            return False
        self.classes = [c for c in self.classes if c.class_id != class_id]
        return True

    def get_class_by_code(self, class_code: str) -> Optional[Class]:
        return next((cls for cls in self.classes if cls.class_code == class_code), None)
