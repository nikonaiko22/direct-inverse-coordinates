import sys
from calculo_sodano import sodano_directo
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QTimer
from PyQt6.QtGui import QFont, QCursor, QColor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFrame, QGraphicsDropShadowEffect, QSizePolicy, QSpacerItem,
    QComboBox, QListView, QMessageBox, QTextEdit, QDialog
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
    def __init__(self, color, expand_callback):
        super().__init__()
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
        icon_label.setText("🌐")
        icon_label.setFont(QFont("Segoe UI Emoji", 40))
        self.layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Sodano")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {color}; margin-bottom:6px;")
        self.layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.controls_container = QWidget()
        controls_layout = QVBoxLayout(self.controls_container)
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        controls_layout.setSpacing(18)
        self.controls_container.setVisible(False)
        self.ellipsoid_label = QLabel("Reference Ellipsoid:")
        self.ellipsoid_label.setFont(QFont("Segoe UI", 12))
        self.ellipsoid_label.setStyleSheet("margin-bottom:5px;")
        controls_layout.addWidget(self.ellipsoid_label, alignment=Qt.AlignmentFlag.AlignLeft)
        self.ellipsoid_selector = QComboBox()
        for ellip in ELLIPSOIDS:
            self.ellipsoid_selector.addItem(ellip[0])
        self.ellipsoid_selector.setFont(QFont("Segoe UI", 14))
        self.ellipsoid_selector.setStyleSheet(
            f"""
            QComboBox {{
                background: #f6f6f6;
                border: 2px solid {color};
                border-radius: 10px;
                padding: 8px 14px;
                color: {color};
                font-size: 15px;
            }}
            QComboBox QAbstractItemView {{
                background: #fff;
                selection-background-color: {color}22;
                color: #222;
                border-radius: 10px;
            }}
            """
        )
        self.ellipsoid_selector.setMaxVisibleItems(8)
        self.ellipsoid_selector.setView(QListView())
        self.ellipsoid_selector.setPlaceholderText("Select reference ellipsoid...")
        controls_layout.addWidget(self.ellipsoid_selector, alignment=Qt.AlignmentFlag.AlignLeft)
        idx_international = [i for i, e in enumerate(ELLIPSOIDS) if e[0] == "International"]
        if idx_international:
            self.ellipsoid_selector.setCurrentIndex(idx_international[0])
        self.selected_ellipsoid = ELLIPSOIDS[self.ellipsoid_selector.currentIndex()]
        self.options_widget = QWidget()
        opt_layout = QHBoxLayout(self.options_widget)
        opt_layout.setSpacing(18)
        self.forward_btn = QPushButton("Forward")
        self.inverse_btn = QPushButton("Inverse")
        for btn in [self.forward_btn, self.inverse_btn]:
            btn.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(
                f"background:#f8fafc; color:{color}; border-radius:16px; "
                f"border:2.5px solid {color}; padding:16px 38px; font-size:17px;"
            )
            btn.setEnabled(True)
        opt_layout.addWidget(self.forward_btn)
        opt_layout.addWidget(self.inverse_btn)
        controls_layout.addWidget(self.options_widget)
        self.ellipsoid_selector.currentIndexChanged.connect(self.enable_options)
        self.layout.addWidget(self.controls_container)
        self.card_anim = None
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
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f6faff, stop:1 #e6f0ff);
                border-radius: 22px;
                border: 3px solid {self.border_color};
                box-shadow: 0 0 30px #0002;
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
        color = "#2563eb"
        self.setWindowTitle(f"{method} - {option.capitalize()} Calculation")
        self.setMinimumSize(700, 600)
        self.setStyleSheet("background: #f8fafc;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 32, 40, 28)
        main_layout.setSpacing(18)

        title = QLabel(f"{method} - {option.capitalize()} | {ellipsoid[0]}")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {color}; margin-bottom:10px; letter-spacing:1px;")
        main_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        ellip_info = QLabel(
            f"Semi-Major Axis: {ellipsoid[1]} m   |   1/Flattening: {ellipsoid[2]}"
        )
        ellip_info.setFont(QFont("Segoe UI", 14))
        ellip_info.setStyleSheet("color: #535353; margin-bottom: 20px;")
        main_layout.addWidget(ellip_info, alignment=Qt.AlignmentFlag.AlignCenter)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #e0e0e0; background: #e0e0e0; margin-bottom: 18px;")
        main_layout.addWidget(sep)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        label_font = QFont("Segoe UI", 15, QFont.Weight.Bold)
        input_font = QFont("Segoe UI", 13)
        input_style = (
            "QLineEdit, QComboBox { background: #f8fbff; border: 1.5px solid #b6cdf7; border-radius: 7px; padding: 7px 10px; font-size:14px; color: #222; min-width: 55px; }"
            "QLineEdit:focus, QComboBox:focus { border-color: #2563eb; background: #eef4ff; }"
        )

        self.inputs = {}
        if option == "forward":
            # Latitude
            lat_row = QHBoxLayout()
            lat_row.setSpacing(8)
            lat_label = QLabel("Latitude  (h default = S)")
            lat_label.setFont(label_font)
            lat_label.setStyleSheet("color:#2563eb; min-width:180px;")
            lat_label.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
            lat_h = QComboBox()
            lat_h.addItems(["N", "S"])
            lat_h.setCurrentIndex(1)
            lat_h.setFont(input_font)
            lat_h.setFixedWidth(50)
            lat_h.setStyleSheet(input_style)
            lat_deg = QLineEdit()
            lat_deg.setPlaceholderText("DD")
            lat_deg.setFont(input_font)
            lat_deg.setFixedWidth(55)
            lat_deg.setStyleSheet(input_style)
            lat_min = QLineEdit()
            lat_min.setPlaceholderText("MM")
            lat_min.setFont(input_font)
            lat_min.setFixedWidth(55)
            lat_min.setStyleSheet(input_style)
            lat_sec = QLineEdit()
            lat_sec.setPlaceholderText("SS.ssssss")
            lat_sec.setFont(input_font)
            lat_sec.setFixedWidth(90)
            lat_sec.setStyleSheet(input_style)
            lat_row.addWidget(lat_label)
            lat_row.addWidget(QLabel("h"))
            lat_row.addWidget(lat_h)
            lat_row.addWidget(lat_deg)
            lat_row.addWidget(lat_min)
            lat_row.addWidget(lat_sec)
            self.inputs['lat_h'] = lat_h
            self.inputs['lat_deg'] = lat_deg
            self.inputs['lat_min'] = lat_min
            self.inputs['lat_sec'] = lat_sec
            form.addRow(lat_row)

            # Longitude
            lon_row = QHBoxLayout()
            lon_row.setSpacing(8)
            lon_label = QLabel("Longitude  (h default = W)")
            lon_label.setFont(label_font)
            lon_label.setStyleSheet("color:#2563eb; min-width:180px;")
            lon_label.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
            lon_h = QComboBox()
            lon_h.addItems(["E", "W"])
            lon_h.setCurrentIndex(1)
            lon_h.setFont(input_font)
            lon_h.setFixedWidth(50)
            lon_h.setStyleSheet(input_style)
            lon_deg = QLineEdit()
            lon_deg.setPlaceholderText("DDD")
            lon_deg.setFont(input_font)
            lon_deg.setFixedWidth(60)
            lon_deg.setStyleSheet(input_style)
            lon_min = QLineEdit()
            lon_min.setPlaceholderText("MM")
            lon_min.setFont(input_font)
            lon_min.setFixedWidth(55)
            lon_min.setStyleSheet(input_style)
            lon_sec = QLineEdit()
            lon_sec.setPlaceholderText("SS.ssssss")
            lon_sec.setFont(input_font)
            lon_sec.setFixedWidth(90)
            lon_sec.setStyleSheet(input_style)
            lon_row.addWidget(lon_label)
            lon_row.addWidget(QLabel("h"))
            lon_row.addWidget(lon_h)
            lon_row.addWidget(lon_deg)
            lon_row.addWidget(lon_min)
            lon_row.addWidget(lon_sec)
            self.inputs['lon_h'] = lon_h
            self.inputs['lon_deg'] = lon_deg
            self.inputs['lon_min'] = lon_min
            self.inputs['lon_sec'] = lon_sec
            form.addRow(lon_row)

            # Azimuth
            az_row = QHBoxLayout()
            az_row.setSpacing(8)
            az_label = QLabel("Forward Azimuth  (from north)")
            az_label.setFont(label_font)
            az_label.setStyleSheet("color:#2563eb; min-width:180px;")
            az_label.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
            az_deg = QLineEdit()
            az_deg.setPlaceholderText("DDD")
            az_deg.setFont(input_font)
            az_deg.setFixedWidth(60)
            az_deg.setStyleSheet(input_style)
            az_min = QLineEdit()
            az_min.setPlaceholderText("MM")
            az_min.setFont(input_font)
            az_min.setFixedWidth(55)
            az_min.setStyleSheet(input_style)
            az_sec = QLineEdit()
            az_sec.setPlaceholderText("SS.sss")
            az_sec.setFont(input_font)
            az_sec.setFixedWidth(90)
            az_sec.setStyleSheet(input_style)
            az_row.addWidget(az_label)
            az_row.addWidget(az_deg)
            az_row.addWidget(az_min)
            az_row.addWidget(az_sec)
            self.inputs['az_deg'] = az_deg
            self.inputs['az_min'] = az_min
            self.inputs['az_sec'] = az_sec
            form.addRow(az_row)

            # Distance
            dist_row = QHBoxLayout()
            dist_row.setSpacing(8)
            dist_label = QLabel("Ellipsoidal Distance  (in meters)")
            dist_label.setFont(label_font)
            dist_label.setStyleSheet("color:#2563eb; min-width:180px;")
            dist_label.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
            dist = QLineEdit()
            dist.setPlaceholderText("DDDDDD.dddd")
            dist.setFont(input_font)
            dist.setFixedWidth(120)
            dist.setStyleSheet(input_style)
            dist_row.addWidget(dist_label)
            dist_row.addWidget(dist)
            self.inputs['dist'] = dist
            form.addRow(dist_row)
        else:
            # ... Aquí agrega los campos inverse igual que en tu código ...
            pass

        self.btn_calc = QPushButton("Calcular")
        self.btn_calc.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.btn_calc.setStyleSheet("background:#e8f0fe; color:#2563eb; border-radius:7px; padding:8px 20px;")
        self.btn_calc.clicked.connect(self.realizar_calculo)
        form.addRow(self.btn_calc)

        self.label_resultado = QLabel("")
        self.label_resultado.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.label_resultado.setStyleSheet("color:#2563eb; margin-top:15px;")
        form.addRow(QLabel("Resultado:"), self.label_resultado)

        main_layout.addLayout(form)
        main_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        btn_layout = QHBoxLayout()
        self.back_btn = QPushButton("← Volver")
        self.back_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.back_btn.setStyleSheet(
            "background:#e8ffe8; color:#2563eb; border-radius:8px; padding:9px 24px; font-size:15px; font-weight:bold; border:none;"
        )
        self.back_btn.setMinimumHeight(32)
        self.back_btn.clicked.connect(self.go_back)
        btn_layout.addWidget(self.back_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

    def realizar_calculo(self):
        # Recoge datos de entrada desde los QLineEdit / QComboBox
        lat1 = float(self.inputs['lat_deg'].text())
        lon1 = float(self.inputs['lon_deg'].text())
        az12 = float(self.inputs['az_deg'].text())
        S = float(self.inputs['dist'].text())
        a = float(self.ellipsoid[1])   # semi-major axis
        f = float(self.ellipsoid[2])   # flattening

        # Ejecuta el cálculo Sodano directo
        resultados = sodano_directo(lat1, lon1, az12, S, a, f)

        # Muestra el resultado final (φ2, λ2), y puedes mostrar todos los pasos en el historial
        result_str = f"φ2: {resultados['φ2']:.8f}°, λ2: {resultados['λ2']:.8f}°"
        steps_str = "\n".join([f"{k}: {v}" for k,v in resultados.items()])
        self.label_resultado.setText(result_str)

        # Para el historial, guarda también todos los pasos
        self.parent.calculos_historial.append({
            "entrada": {
                "lat1": lat1,
                "lon1": lon1,
                "az12": az12,
                "S": S,
                "a": a,
                "f": f
            },
            "resultado": result_str,
            "formula": "Sodano Directo",
            "pasos": steps_str
        })

    def go_back(self):
        self.close()
        self.parent.show()

class HistorialDialog(QDialog):
    def __init__(self, historial):
        super().__init__()
        self.setWindowTitle("Historial de cálculos realizados")
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)
        if not historial:
            layout.addWidget(QLabel("No hay cálculos realizados aún."))
        else:
            for idx, calc in enumerate(historial, 1):
                group = QFrame()
                group.setFrameShape(QFrame.Shape.Box)
                vlay = QVBoxLayout(group)
                entrada = calc.get('entrada', '')
                resultado = calc.get('resultado', '')
                formula = calc.get('formula', '')
                pasos = calc.get('pasos', '')
                vlay.addWidget(QLabel(f"<b>Cálculo #{idx}</b>"))
                vlay.addWidget(QLabel(f"<b>Entrada:</b> {entrada}"))
                vlay.addWidget(QLabel(f"<b>Resultado:</b> {resultado}"))
                vlay.addWidget(QLabel(f"<b>Fórmula utilizada:</b> {formula}"))
                pasos_text = QTextEdit()
                pasos_text.setReadOnly(True)
                pasos_text.setPlainText(f"Pasos explicados:\n{pasos}")
                vlay.addWidget(pasos_text)
                layout.addWidget(group)
        btn = QPushButton("Cerrar")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GeoProblems - Geodesic Toolkit")
        self.setMinimumSize(700, 500)
        self.setStyleSheet("background: #eef4fa;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 14)
        main_layout.setSpacing(10)
        title = QLabel("GeoProblems")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet("color: #222; letter-spacing: 2px; margin-bottom: 4px;")
        main_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Direct and inverse geodetic calculations with Sodano method")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: #7c7c7c; margin-bottom: 10px;")
        main_layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout = QHBoxLayout()
        sodano_color = "#2563eb"
        def expand_card(card_clicked):
            if card_clicked.expanded:
                return
            card_clicked.expand(True)
        self.sodano_card = MethodCard(sodano_color, expand_card)
        card_layout.addWidget(self.sodano_card)
        main_layout.addLayout(card_layout)
        self.sodano_card.forward_btn.clicked.connect(
            lambda: self.open_calc("Sodano", "forward", self.sodano_card.selected_ellipsoid)
        )
        self.sodano_card.inverse_btn.clicked.connect(
            lambda: self.open_calc("Sodano", "inverse", self.sodano_card.selected_ellipsoid)
        )
        self.calculos_historial = []
        self.btn_ver_calculos = QPushButton("Ver cálculos realizados")
        self.btn_ver_calculos.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.btn_ver_calculos.setStyleSheet("background:#e8f0fe; color:#2563eb; border-radius:7px; padding:8px 20px;")
        self.btn_ver_calculos.clicked.connect(self.mostrar_historial_calculos)
        main_layout.addWidget(self.btn_ver_calculos, alignment=Qt.AlignmentFlag.AlignRight)
        main_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        self.setLayout(main_layout)

    def open_calc(self, method, option, ellipsoid):
        if ellipsoid is None:
            return
        self.calc_window = CalculationWindow(method, option, ellipsoid, self)
        self.calc_window.show()
        self.hide()

    def mostrar_historial_calculos(self):
        dlg = HistorialDialog(self.calculos_historial)
        dlg.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())