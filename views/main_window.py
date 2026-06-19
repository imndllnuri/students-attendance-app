from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QPushButton, QSpacerItem, QGridLayout, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStackedWidget
from resources.images import qrc
from views.add_new_class_window import AddNewClassWindow
from models.classes import Class, ClassManager
from pathlib import Path
import json
class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        uic.loadUi("ui/main_window.ui", self)
        
        self.user = user
        self.user_id = user.user_id

        # Display logged-in user's name and surname
        self.user_info_lbl.setText(f"{user.name} {user.surname}")
        # Connect buttons to respective actions
        self.profile_btn.clicked.connect(self.show_profile)
        self.my_classes_btn.clicked.connect(self.show_my_classes)
        self.settings_btn.clicked.connect(self.show_settings)
        self.log_out_btn.clicked.connect(self.confirm_logout)

        self.create_new_class_btn.clicked.connect(self.open_add_new_class_window)
        
        self.load_classes()
        self.show()
        
    def show_profile(self):
        """Opens stackedWidget at index 3 for profile view."""
        self.stackedWidget.setCurrentIndex(3)

    def show_my_classes(self):
        """Opens stackedWidget at index 0 for my classes view."""
        self.stackedWidget.setCurrentIndex(0)
        self.load_classes()

    def load_classes(self):
        """Load class buttons into class_btns_layout"""
        # Clear existing buttons from class_btns_layout
        while self.class_btns_layout.count():
            item = self.class_btns_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Load classes from data directory
        class_dir = Path("data") / str(self.user_id)
        if not class_dir.exists():
            return

        # Load and sort classes
        classes = []
        for cls_folder in class_dir.iterdir():
            if cls_folder.is_dir():
                cls_file = cls_folder / "class_info.json"
                if cls_file.exists():
                    try:
                        with open(cls_file, "r") as f:
                            classes.append(Class.from_dict(json.load(f)))
                    except Exception as e:
                        print(f"Error loading {cls_folder.name}: {e}")

        # Add sorted buttons to class_btns_layout
        for cls in sorted(classes, key=lambda c: c.class_code):
            class_widget = QWidget()  # Create a container widget
            class_layout = QHBoxLayout(class_widget)  # Layout for button + delete button
            class_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins

            # Class button
            class_btn = QPushButton(f"{cls.class_name} ({cls.class_code})")
            class_btn.setProperty("class_id", cls.class_id)
            class_btn.clicked.connect(lambda _, c=cls: self.open_class_window(c))

            # Delete button
            delete_btn = QPushButton("X")
            delete_btn.setStyleSheet("color: red; font-weight: bold;")  # Optional styling
            delete_btn.setFixedSize(25, 25)  # Small button size
            delete_btn.clicked.connect(lambda _, c=cls: self.delete_class(c))

            # Add widgets to layout
            class_layout.addWidget(class_btn)
            class_layout.addWidget(delete_btn)

            # Add to main layout
            self.class_btns_layout.addWidget(class_widget)
    
    def delete_class(self, cls):
        """Delete class from file system and UI with confirmation."""
        
        # Show confirmation message box
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the class '{cls.class_code}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Default button
        )

        if reply == QMessageBox.Yes:
            class_dir = Path("data") / str(self.user_id) / cls.class_code
            if class_dir.exists():
                try:
                    # Remove the class directory and all contents
                    import shutil
                    shutil.rmtree(class_dir)
                    print(f"Deleted class: {cls.class_code}")

                    # Reload UI
                    self.load_classes()

                    # Show success message
                    QMessageBox.information(self, "Success", f"Class '{cls.class_code}' has been deleted.")

                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error deleting {cls.class_code}:\n{e}")

    def open_class_window(self, class_obj):
        """Open ClassWindow inside stackedWidget"""
        existing_index = self.find_class_tab(class_obj.class_code)

        if existing_index is not None:
            # If class window already exists, switch to it
            self.stackedWidget.setCurrentIndex(existing_index)
        else:
            from views.class_window import ClassWindow  # Lazy import to avoid circular dependency
            
            # Create new class window and add to stackedWidget
            class_page = ClassWindow(class_obj, self)
            index = self.stackedWidget.addWidget(class_page)
            
            # Store class window reference (optional)
            class_page.setProperty("class_code", class_obj.class_code)
            
            # Switch to new class window
            self.stackedWidget.setCurrentIndex(index)

    def find_class_tab(self, class_code):
        """Find existing class tab in stackedWidget by class_code."""
        for i in range(self.stackedWidget.count()):
            widget = self.stackedWidget.widget(i)
            if widget.property("class_code") == class_code:
                return i
        return None  # Not found

    def show_settings(self):
        """Opens stackedWidget at index 1 for settings view."""
        self.stackedWidget.setCurrentIndex(1)

    def open_add_new_class_window(self):
        """Opens the Add New Class window when the button is clicked."""
        self.add_new_class_window = AddNewClassWindow(user_id = self.user_id)  # Create an instance of AddNewClassWindow
        self.add_new_class_window.show()  # Open the AddNewClassWindow as a modal dialog (exec_)
    
    def confirm_logout(self):
        """Asks for confirmation to log out and return to the login window."""
        reply = QMessageBox.question(self, 'Log Out', 'Are you sure you want to log out?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.logout()

    def logout(self):
        from views.login_window import LoginWindow  # Import LoginWindow for navigation
        """Handles logout by showing the login window."""
        self.close()  # Close the main window
        self.login_window = LoginWindow()  # Create an instance of LoginWindow
        self.login_window.show()  # Show the login window

    

