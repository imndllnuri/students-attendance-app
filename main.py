import sys
from PyQt5.QtWidgets import QApplication
from logging_config import setup_logging
from shared.theme import load_theme_preference, stylesheet_path
from views.login_window import LoginWindow

def main():
    setup_logging()
    app = QApplication(sys.argv)
    with open(stylesheet_path(load_theme_preference())) as f:
        app.setStyleSheet(f.read())
    window = LoginWindow()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
