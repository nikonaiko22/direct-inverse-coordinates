import sys
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QTimer
from PyQt6.QtGui import QFont, QCursor, QColor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFrame, QGraphicsDropShadowEffect, QSizePolicy, QSpacerItem,
    QComboBox, QListView
)

ELLIPSOIDS = [
    ("Airy 1830", "6377563.396", "299.3249646"),
    ("Bessel 1841", "637397.155", "299.1528128"),
    ("Clarke 1866", "6378206.4", "294.9786982"),
    ("Clarke 1880", "6378249.145", "293.465"),
    ("Everest 1830", "6377276.345", "300.8017"),
    ("Fischer 1960 (Mercury)", "6378166.0", "298.3"),
    ("Fischer 1968", "6378150.0", "298.3"),
    ("G R S 1967", "6378160.0", "298.247167427"),
    ("G R S 1975", "6378140.0", "298.257"),
    ("G R S 1980", "6378137.0", "298.257222101"),
    ("Hough 1956", "6378270.0", "297.0"),
    ("International", "6378388.0", "297.0"),
    ("Krassovsky 1940", "6378245.0", "298.3"),
    ("South American 1969", "6378160.0", "298.25"),
    ("WGS 60", "6378165.0", "298.3"),
    ("WGS 66", "6378145.0", "298.25"),
    ("WGS 72", "6378135.0", "298.26"),
    ("WGS 84", "6378137.0", "298.257223563"),
]

def lerp_color(color1, color2, t):
    c1 = QColor(color1)
    c2 = QColor(color2)
    return QColor(
        int(c1.red() + (c2.red() - c1.red()) * t),
        int(c1.green() + (c2.green() - c1.green()) * t),
        int(c1.blue() + (c2.blue() - c1.blue()) * t)
    ).name()

class MethodCard(QFrame):
    def __init__(self, method, color, expand_callback):
        super().__init__()
        self.method = method
        self.color = color
        self.expand_callback = expand_callback
        self.selected_ellipsoid = None
        self.expanded = False
        self.animating = False

        self.default_border = "#d7d7d7"
        self.active_border = color
        self.border_color = self.default_border
        self.setFixedSize(420, 420)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.shadow = QGraphicsDropShadowEffect(self)
        self.setGraphicsEffect(self.shadow)
        self.update_style(active=False)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(32, 32, 32, 28)
        self.layout.setSpacing(15)

        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if method == "Sodano":
            icon_label.setText("🌐")
        else:
            icon_label.setText("🧮")
        icon_label.setFont(QFont("Segoe UI Emoji", 40))
        self.layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel(method)
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {color}; margin-bottom:6px;")
        self.layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.controls_container = QWidget()
        controls_layout = QVBoxLayout(self.controls_container)
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        controls_layout.setSpacing(11)
        self.controls_container.setVisible(False)

        self.ellipsoid_label = QLabel("Select Reference Ellipsoid:")
        self.ellipsoid_label.setFont(QFont("Segoe UI", 12))
        self.ellipsoid_label.setStyleSheet("margin-bottom:5px;")
        controls_layout.addWidget(self.ellipsoid_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.ellipsoid_selector = QComboBox()
        for ellip in ELLIPSOIDS:
            self.ellipsoid_selector.addItem(ellip[0])
        self.ellipsoid_selector.setFont(QFont("Segoe UI", 13))
        self.ellipsoid_selector.setStyleSheet(
            f"""
            QComboBox {{
                background: #f6f6f6;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 6px 10px;
                color: {color};
            }}
            QComboBox QAbstractItemView {{
                background: #fff;
                selection-background-color: {color}22;
                color: #222;
                border-radius: 8px;
            }}
            """
        )
        self.ellipsoid_selector.setMaxVisibleItems(8)
        self.ellipsoid_selector.setView(QListView())
        self.ellipsoid_selector.setPlaceholderText("Select reference ellipsoid...")
        controls_layout.addWidget(self.ellipsoid_selector, alignment=Qt.AlignmentFlag.AlignLeft)

        self.options_widget = QWidget()
        opt_layout = QHBoxLayout(self.options_widget)
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
            btn.setEnabled(False)
        opt_layout.addWidget(self.forward_btn)
        opt_layout.addWidget(self.inverse_btn)
        controls_layout.addWidget(self.options_widget)

        self.ellipsoid_selector.currentIndexChanged.connect(self.enable_options)
        self.layout.addWidget(self.controls_container)

        self.card_anim = None
        # For border color animation
        self.border_anim_timer = None
        self.border_anim_steps = 10
        self.border_anim_step = 0
        self.border_anim_from = self.default_border
        self.border_anim_to = self.active_border

    def enable_options(self, idx):
        enabled = idx >= 0
        self.forward_btn.setEnabled(enabled)
        self.inverse_btn.setEnabled(enabled)
        self.selected_ellipsoid = ELLIPSOIDS[idx] if enabled else None

    def mousePressEvent(self, event):
        if self.animating:
            return
        if not self.expanded:
            self.expand(True)
            if self.expand_callback:
                self.expand_callback(self)
        else:
            self.collapse()

    def expand(self, state):
        if self.animating:
            return
        self.expanded = state
        self.stop_animations()
        self.animate_card(expand=True)
        self.animate_border(self.default_border, self.active_border)
        self.update_style(active=True)
        self.controls_container.setVisible(True)

    def collapse(self):
        if self.animating or not self.expanded:
            return
        self.expanded = False
        self.stop_animations()
        self.animate_card(expand=False)
        self.animate_border(self.active_border, self.default_border)
        self.update_style(active=False)
        self.controls_container.setVisible(False)

    def animate_card(self, expand=True):
        self.animating = True
        if self.card_anim:
            self.card_anim.stop()
        self.card_anim = QPropertyAnimation(self, b"geometry")
        self.card_anim.setDuration(220)
        self.card_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        if expand:
            self.card_anim.setEndValue(QRect(self.x(), self.y(), self.width(), 370))
        else:
            self.card_anim.setEndValue(QRect(self.x(), self.y(), self.width(), 220))
        self.card_anim.finished.connect(self.animation_finished)
        self.card_anim.start()

    def animation_finished(self):
        self.animating = False
        self.card_anim = None

    def update_style(self, active):
        self.setStyleSheet(f"""
            QFrame {{
                background: #fff;
                border-radius: 22px;
                border: 3px solid {self.border_color};
            }}
        """)
        if active:
            self.graphicsEffect().setColor(QColor(self.color))
            self.graphicsEffect().setBlurRadius(35)
            self.graphicsEffect().setOffset(0, 12)
        else:
            self.graphicsEffect().setColor(QColor(self.default_border))
            self.graphicsEffect().setBlurRadius(24)
            self.graphicsEffect().setOffset(0, 8)

    def animate_border(self, from_color, to_color):
        # Animate border color in steps for a smooth transition
        if self.border_anim_timer:
            self.border_anim_timer.stop()
        self.border_anim_step = 0
        self.border_anim_from = from_color
        self.border_anim_to = to_color
        self.border_anim_timer = QTimer()
        self.border_anim_timer.timeout.connect(self.animate_border_step)
        self.border_anim_timer.start(22)

    def animate_border_step(self):
        t = self.border_anim_step / self.border_anim_steps
        self.border_color = lerp_color(self.border_anim_from, self.border_anim_to, t)
        self.update_style(self.expanded)
        self.border_anim_step += 1
        if self.border_anim_step > self.border_anim_steps:
            self.border_anim_timer.stop()
            self.border_anim_timer = None
            self.border_color = self.border_anim_to
            self.update_style(self.expanded)

    def stop_animations(self):
        if self.card_anim:
            self.card_anim.stop()
            self.card_anim = None
        if self.border_anim_timer:
            self.border_anim_timer.stop()
            self.border_anim_timer = None

class CalculationWindow(QWidget):
    def __init__(self, method, option, ellipsoid, parent):
        super().__init__()
        self.method = method
        self.option = option
        self.ellipsoid = ellipsoid
        self.parent = parent
        color = "#2563eb" if method == "Sodano" else "#f59e42"
        self.setWindowTitle(f"{method} - {option.capitalize()} Calculation")
        self.setMinimumSize(500, 480)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 32, 40, 28)
        main_layout.setSpacing(18)

        title = QLabel(f"{method} - {option.capitalize()} | {ellipsoid[0]}")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {color};")
        main_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        ellip_info = QLabel(
            f"Semi-Major Axis: {ellipsoid[1]} m   |   1/Flattening: {ellipsoid[2]}"
        )
        ellip_info.setFont(QFont("Segoe UI", 13))
        ellip_info.setStyleSheet("color: #535353; margin-bottom: 10px;")
        main_layout.addWidget(ellip_info, alignment=Qt.AlignmentFlag.AlignCenter)

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

        def expand_card(card_clicked):
            for card in [self.sodano_card, self.puissant_card]:
                if card is not card_clicked and card.expanded:
                    card.collapse()

        self.sodano_card = MethodCard("Sodano", sodano_color, expand_card)
        self.puissant_card = MethodCard("Puissant", puissant_color, expand_card)

        card_layout.addWidget(self.sodano_card)
        card_layout.addWidget(self.puissant_card)
        main_layout.addLayout(card_layout)

        self.sodano_card.forward_btn.clicked.connect(
            lambda: self.open_calc("Sodano", "forward", self.sodano_card.selected_ellipsoid)
        )
        self.sodano_card.inverse_btn.clicked.connect(
            lambda: self.open_calc("Sodano", "inverse", self.sodano_card.selected_ellipsoid)
        )
        self.puissant_card.forward_btn.clicked.connect(
            lambda: self.open_calc("Puissant", "forward", self.puissant_card.selected_ellipsoid)
        )
        self.puissant_card.inverse_btn.clicked.connect(
            lambda: self.open_calc("Puissant", "inverse", self.puissant_card.selected_ellipsoid)
        )

        main_layout.addItem(QSpacerItem(10, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    def open_calc(self, method, option, ellipsoid):
        if ellipsoid is None:
            return
        self.calc_window = CalculationWindow(method, option, ellipsoid, self)
        self.calc_window.show()
        self.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())