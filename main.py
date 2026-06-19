import sys
from PyQt5.QtWidgets import QApplication
from views.login_window import LoginWindow

def main():
    app = QApplication(sys.argv)
    window = LoginWindow()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
