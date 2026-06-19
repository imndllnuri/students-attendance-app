from pathlib import Path
import json
import uuid
from dataclasses import dataclass
from typing import List, Dict, Optional
from PyQt5.QtCore import QTime


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
                 spreadsheet_path: Optional[str] = ""):
        self.class_id = str(uuid.uuid4())
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
        self.spreadsheet_path = spreadsheet_path

    def to_dict(self):
        return {
            "class_id": self.class_id,
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
                        "selected": slot.selected
                    }
                    for slot in slots
                ]
                for day, slots in self.schedule.items()
            },
            "spreadsheet_path": self.spreadsheet_path
        }


    @classmethod
    def from_dict(cls, data):
        schedule = {
            day: [
                ScheduleSlot(
                    day=day,
                    start_time=QTime.fromString(slot["start_time"], "HH:mm"),
                    end_time=QTime.fromString(slot["end_time"], "HH:mm"),
                    selected=slot["selected"]
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
            spreadsheet_path=data["spreadsheet_path"]
        )

class ClassManager:
    def __init__(self):
        self.classes = self.load_classes()

    def load_classes(self) -> List[Class]:
        """Load all classes from the data directory structure."""
        classes = []
        data_dir = Path("data")
        
        if not data_dir.exists():
            return classes

        # Iterate over all instructor directories
        for instructor_dir in data_dir.iterdir():
            if instructor_dir.is_dir():
                instructor_id = instructor_dir.name
                
                # Iterate over all class directories
                for class_dir in instructor_dir.iterdir():
                    if class_dir.is_dir():
                        class_info_path = class_dir / "class_info.json"
                        
                        if class_info_path.exists():
                            try:
                                with open(class_info_path, "r") as f:
                                    data = json.load(f)
                                    cls = Class.from_dict(data)
                                    classes.append(cls)
                            except Exception as e:
                                print(f"Error loading {class_info_path}: {e}")
        return classes

    def save_class_to_fs(self, cls: Class) -> None:
        """Save a single class to the filesystem."""
        # Create directory: data/{instructor_id}/{class_code}
        class_dir = Path("data") / cls.instructor_id / cls.class_code
        class_dir.mkdir(parents=True, exist_ok=True)
        
        # Save class data
        class_info_path = class_dir / "class_info.json"
        with open(class_info_path, "w") as f:
            json.dump(cls.to_dict(), f, indent=4)

    def add_class(self, new_class: Class) -> None:
        """Add a new class and save it to the filesystem."""
        self.save_class_to_fs(new_class)
        self.classes.append(new_class)

    def get_classes_by_instructor(self, instructor_id: str) -> List[Class]:
        """Get classes for a specific instructor."""
        return [cls for cls in self.classes if cls.instructor_id == instructor_id]

    def get_class_by_code(self, class_code: str) -> Class | None:
        """Get a class by its code."""
        return next((cls for cls in self.classes if cls.class_code == class_code), None)