from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QToolButton


class UnderlineTabButton(QToolButton):
    """
    This class is responsible for the buttons in the tab panels that can often be found at the top of the page.
    """

    clicked_tab_button = pyqtSignal(object)
    common_stylesheet = """
    QToolButton {
        color: white;
        border: none;
        border-bottom: 3px solid #e67300;
        background: none;
        font-size: 14px;
    }
    """

    selected_stylesheet = """
    QToolButton { border-bottom: 3px solid #e67300; }
    """
    unselected_stylesheet = """
    QToolButton { border-bottom: 3px solid #666; }
    """

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.unselect_tab_button()

    def mouseReleaseEvent(self, event):
        self.clicked_tab_button.emit(self)

    def select_tab_button(self):
        self.setStyleSheet(self.common_stylesheet + '\n' + self.selected_stylesheet)

    def unselect_tab_button(self):
        self.setStyleSheet(self.common_stylesheet + '\n' + self.unselected_stylesheet)
