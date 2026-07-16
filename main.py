import sys
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication
from logging_config import setup_logging
from shared.font_scale import load_font_scale, point_size_for_scale
from views.login_window import LoginWindow

THEME_QSS_PATH = "resources/styles/theme.qss"

def main():
    setup_logging()
    app = QApplication(sys.argv)
    with open(THEME_QSS_PATH) as f:
        app.setStyleSheet(f.read())
    font = app.font()
    font.setPointSize(point_size_for_scale(load_font_scale()))
    app.setFont(font)
    window = LoginWindow()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
