import sys
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QFont, QCursor, QIcon, QPixmap, QColor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFrame, QGraphicsDropShadowEffect, QSizePolicy, QSpacerItem
)

class CalculationWindow(QWidget):
    def __init__(self, method, option, parent):
        super().__init__()
        self.method = method
        self.option = option
        self.parent = parent
        color = "#2563eb" if method == "Sodano" else "#f59e42"
        self.setWindowTitle(f"{method} - {option.capitalize()} Calculation")
        self.setMinimumSize(500, 480)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 32, 40, 28)
        main_layout.setSpacing(18)

        title = QLabel(f"{method} - {option.capitalize()}")
        title.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {color};")
        main_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #e0e0e0; background: #e0e0e0; margin-bottom: 10px;")
        main_layout.addWidget(sep)

        form = QVBoxLayout()
        form.setSpacing(12)
        font = QFont("Segoe UI", 14)
        if option == "forward":
            for label in ["Latitude 1", "Longitude 1", "Azimuth", "Ellipsoidal Distance"]:
                lbl = QLabel(label)
                lbl.setFont(font)
                edit = QLineEdit()
                edit.setFont(font)
                form.addWidget(lbl)
                form.addWidget(edit)
        else:
            for label in ["Latitude 1", "Longitude 1", "Latitude 2", "Longitude 2"]:
                lbl = QLabel(label)
                lbl.setFont(font)
                edit = QLineEdit()
                edit.setFont(font)
                form.addWidget(lbl)
                form.addWidget(edit)
        main_layout.addLayout(form)

        main_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        btn_layout = QHBoxLayout()
        self.back_btn = QPushButton("← Volver")
        self.back_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.back_btn.setStyleSheet(
            f"background:{color}22; color:{color}; border-radius:8px; padding:8px 24px;"
            f"font-size:16px;"
            f"border: none;"
        )
        self.back_btn.clicked.connect(self.go_back)
        btn_layout.addWidget(self.back_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

    def go_back(self):
        self.close()
        self.parent.show()

class MethodCard(QFrame):
    def __init__(self, method, color, icon_path=None):
        super().__init__()
        self.method = method
        self.color = color
        self.expanded = False
        self.setStyleSheet(f"""
            QFrame {{
                background: #fff;
                border-radius: 22px;
                border: 3px solid {color}44;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(color))
        self.setGraphicsEffect(shadow)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(32, 32, 32, 28)
        self.layout.setSpacing(15)

        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if icon_path:
            icon_label.setPixmap(QPixmap(icon_path).scaled(50,50, Qt.AspectRatioMode.KeepAspectRatio,
                                                           Qt.TransformationMode.SmoothTransformation))
        else:
            icon_label.setText("🌐" if method == "Sodano" else "🧮")
            icon_label.setFont(QFont("Segoe UI Emoji", 40))
        self.layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel(method)
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {color}; margin-bottom:6px;")
        self.layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.options_widget = QWidget()
        opt_layout = QHBoxLayout()
        opt_layout.setSpacing(12)
        self.forward_btn = QPushButton("Forward")
        self.inverse_btn = QPushButton("Inverse")
        for btn in [self.forward_btn, self.inverse_btn]:
            btn.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(
                f"background:#fff; color:{color}; border-radius:14px; "
                f"border:2px solid {color}; padding:13px 32px; font-size:16px;"
            )
        self.forward_btn.setIcon(QIcon.fromTheme("go-next"))
        self.inverse_btn.setIcon(QIcon.fromTheme("go-previous"))
        opt_layout.addWidget(self.forward_btn)
        opt_layout.addWidget(self.inverse_btn)
        self.options_widget.setLayout(opt_layout)
        self.options_widget.setVisible(False)
        self.layout.addWidget(self.options_widget)

    def mousePressEvent(self, event):
        self.expand(True)

    def expand(self, state):
        self.expanded = state
        self.options_widget.setVisible(state)
        anim = QPropertyAnimation(self, b"geometry")
        anim.setDuration(220)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        if state:
            anim.setEndValue(QRect(self.x(), self.y(), self.width(), 320))
        else:
            anim.setEndValue(QRect(self.x(), self.y(), self.width(), 220))
        anim.start()
        self.anim = anim

    def collapse(self):
        self.expand(False)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GeoProblems - Geodesic Toolkit")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("background: #f8fafc;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 32, 40, 24)
        main_layout.setSpacing(15)

        title = QLabel("GeoProblems")
        title.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        title.setStyleSheet("color: #222; letter-spacing: 2px; margin-bottom: 6px;")
        main_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Direct and inverse geodetic calculations with Sodano and Puissant methods")
        subtitle.setFont(QFont("Segoe UI", 15))
        subtitle.setStyleSheet("color: #7c7c7c; margin-bottom: 16px;")
        main_layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)

        card_layout = QHBoxLayout()
        card_layout.setSpacing(40)
        sodano_color = "#2563eb"
        puissant_color = "#f59e42"

        self.sodano_card = MethodCard("Sodano", sodano_color)
        self.puissant_card = MethodCard("Puissant", puissant_color)

        card_layout.addWidget(self.sodano_card)
        card_layout.addWidget(self.puissant_card)
        main_layout.addLayout(card_layout)

        self.sodano_card.forward_btn.clicked.connect(lambda: self.open_calc("Sodano", "forward"))
        self.sodano_card.inverse_btn.clicked.connect(lambda: self.open_calc("Sodano", "inverse"))
        self.puissant_card.forward_btn.clicked.connect(lambda: self.open_calc("Puissant", "forward"))
        self.puissant_card.inverse_btn.clicked.connect(lambda: self.open_calc("Puissant", "inverse"))

        self.sodano_card.forward_btn.clicked.connect(lambda: self.sodano_card.collapse())
        self.sodano_card.inverse_btn.clicked.connect(lambda: self.sodano_card.collapse())
        self.puissant_card.forward_btn.clicked.connect(lambda: self.puissant_card.collapse())
        self.puissant_card.inverse_btn.clicked.connect(lambda: self.puissant_card.collapse())
        self.sodano_card.mousePressEvent = lambda e: self.expand_card(self.sodano_card, self.puissant_card)
        self.puissant_card.mousePressEvent = lambda e: self.expand_card(self.puissant_card, self.sodano_card)

        main_layout.addItem(QSpacerItem(10, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    def expand_card(self, card, other_card):
        card.expand(True)
        other_card.collapse()

    def open_calc(self, method, option):
        self.calc_window = CalculationWindow(method, option, self)
        self.calc_window.show()
        self.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())