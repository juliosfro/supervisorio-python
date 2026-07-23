import random
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QSizePolicy
import pyqtgraph as pg


class TrendWindow(QDialog):
    """Janela Pop-up independente para o Gráfico de Tendência."""

    def __init__(self, data_ref, parent=None):
        super().__init__(parent)
        self.data_ref = data_ref

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(500, 360)
        self.setStyleSheet("background-color: #eaebf0; border: 1.5px solid #6b7280; border-radius: 2px;")

        self.drag_position = None

        # Histórico do gráfico (30 pontos)
        self.x_data = list(range(30))
        self.y_corrente = [0.0] * 30

        self.init_ui()
        self.start_trend_simulation()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- CABEÇALHO DO POP-UP ---
        header = QFrame()
        header.setFixedHeight(32)
        header.setStyleSheet("background: #4b5563; border-bottom: 1px solid #374151;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 0, 12, 0)

        lbl_title = QLabel(f"Gráfico de Tendência - {self.data_ref.get('tag', '')}")
        lbl_title.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 12px; border: none; background: transparent;")

        btn_close = QPushButton("×")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: bold; border: none; background: transparent;")
        btn_close.clicked.connect(self.close)

        h_layout.addWidget(lbl_title)
        h_layout.addStretch()
        h_layout.addWidget(btn_close)

        # --- GRÁFICO (PYQTGRAPH) ---
        chart_container = QWidget()
        c_layout = QVBoxLayout(chart_container)
        c_layout.setContentsMargins(10, 10, 10, 10)

        pg.setConfigOption('background', '#1f2937')
        pg.setConfigOption('foreground', '#f3f4f6')

        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setTitle("Corrente do Motor em Tempo Real", color="#ffffff", size="9pt")
        self.graph_widget.setLabel('left', 'Corrente (A)', color='#22c55e')
        self.graph_widget.setLabel('bottom', 'Tempo (s)', color='#9ca3af')
        self.graph_widget.showGrid(x=True, y=True, alpha=0.25)
        self.graph_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.curve_corrente = self.graph_widget.plot(
            self.x_data, self.y_corrente,
            pen=pg.mkPen(color='#22c55e', width=2)
        )

        c_layout.addWidget(self.graph_widget)

        main_layout.addWidget(header)
        main_layout.addWidget(chart_container)

    def start_trend_simulation(self):
        self.timer_trend = QTimer(self)
        self.timer_trend.timeout.connect(self.update_trend_data)
        self.timer_trend.start(1000)

    def update_trend_data(self):
        if self.data_ref.get('status') == "ON":
            try:
                raw_corr = self.data_ref.get('corrente', '0.75')
                base_corr = float(str(raw_corr).replace(',', '.').replace(' A', ''))
            except (ValueError, TypeError):
                base_corr = 0.75
            val_corr = round(base_corr + random.uniform(-0.05, 0.05), 2)
            val_corr = max(0.1, val_corr)
        else:
            val_corr = 0.0

        self.y_corrente.pop(0)
        self.y_corrente.append(val_corr)
        self.curve_corrente.setData(self.x_data, self.y_corrente)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.y() <= 32:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def closeEvent(self, event):
        if hasattr(self, 'timer_trend') and self.timer_trend.isActive():
            self.timer_trend.stop()
        super().closeEvent(event)