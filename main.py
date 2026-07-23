import sys
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QTimer, QDateTime
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PyQt5.QtWidgets import (
    QApplication, QWidget, QFrame, QLabel, QVBoxLayout,
    QHBoxLayout, QScrollArea, QSizePolicy, QLayout, QLineEdit,
    QPushButton, QStackedWidget
)

from faceplate_dialog import FaceplateDialog
from sidebar import SidebarWidget
from plc_cadastro_screen import PLCCadastroScreen  # <-- Importação da tela de PLC

# --- DADOS INICIAIS ---
MOTORES_DATA = [
    {"tag": "EST10.30", "desc": "(B20.06) ESTEIRA DE ASA P/ EMBALAGEM", "ua": "29/08/2024 15:30", "mode": "REM", "dir": "REV", "corrente": "0,55 A", "velocidade": "900 Rpm", "status": "ON"},
    {"tag": "EST10.31", "desc": "(B19.10) SASSAMI REFILADO", "ua": "29/08/2024 15:30", "mode": "REM", "dir": "DIR", "corrente": "0,00 A", "velocidade": "0 Rpm", "status": "OFF"},
    {"tag": "EST10.32", "desc": "(B19.09) SASSAMI PARA REFILE", "ua": "29/08/2024 15:30", "mode": "REM", "dir": "REV", "corrente": "1,01 A", "velocidade": "450 Rpm", "status": "ON"},
    {"tag": "EST10.33", "desc": "(B19.12) EST P/ PADRONIZACAO DE PACOTES", "ua": "29/08/2024 15:30", "mode": "REM", "dir": "DIR", "corrente": "0,71 A", "velocidade": "900 Rpm", "status": "ON"},
    {"tag": "EST10.35", "desc": "(B19.04) GIRAFA PEITO P/ MARINADOS", "ua": "29/08/2024 15:30", "mode": "REM", "dir": "DIR", "corrente": "0,00 A", "velocidade": "0 Rpm", "status": "OFF"},
    {"tag": "EST10.36", "desc": "(B19.06) DESCARTE SASSAMI", "ua": "29/08/2024 15:30", "mode": "REM", "dir": "REV", "corrente": "0,67 A", "velocidade": "1800 Rpm", "status": "ON"},
    {"tag": "EST10.39", "desc": "(INV-B22.03) AÉREA P/ FOODMATE BL", "ua": "29/08/2024 15:30", "mode": "REM", "dir": "DIR", "corrente": "0,80 A", "velocidade": "2100 Rpm", "status": "ON"},
    {"tag": "EST10.40", "desc": "(INV-B22.04) COXA E SOBRECOXA DESOSSADA", "ua": "29/08/2024 15:30", "mode": "REM", "dir": "REV", "corrente": "0,00 A", "velocidade": "0 Rpm", "status": "OFF"},
    {"tag": "EST10.41", "desc": "(INV-B22.10) ELEVATÓRIA COXA SOBRECOXA DESOSSADA", "ua": "29/08/2024 15:30", "mode": "REM", "dir": "REV", "corrente": "1,15 A", "velocidade": "1500 Rpm", "status": "ON"},
    {"tag": "EST10.42", "desc": "(INV-B22.05) SAÍDA BL DA FOODMATE", "ua": "29/08/2024 15:30", "mode": "REM", "dir": "DIR", "corrente": "0,72 A", "velocidade": "1050 Rpm", "status": "ON"},
    {"tag": "EST10.43", "desc": "(INV-B22.06) ELEVATÓRIA DE OSSO", "ua": "29/08/2024 15:30", "mode": "REM", "dir": "REV", "corrente": "0,00 A", "velocidade": "0 Rpm", "status": "OFF"},
    {"tag": "EST10.44", "desc": "(INV-B22.08) PENDURA COXA E SOBRECOXA", "ua": "29/08/2024 15:30", "mode": "REM", "dir": "DIR", "corrente": "0,66 A", "velocidade": "2100 Rpm", "status": "ON"},
    {"tag": "EST10.45", "desc": "(INV-B22.09) ESTEIRA REFILE DE COXA E SOBRECOXA", "ua": "29/08/2024 15:30", "mode": "REM", "dir": "DIR", "corrente": "0,79 A", "velocidade": "600 Rpm", "status": "ON"},
    {"tag": "EST10.46", "desc": "(INV-B22.11) BL PACOTE SELAGEM", "ua": "29/08/2024 15:30", "mode": "REM", "dir": "REV", "corrente": "0,00 A", "velocidade": "0 Rpm", "status": "OFF"},
    {"tag": "EST10.47", "desc": "(INV-B22.12) ESTEIRA ELEVATÓRIA PACOTES", "ua": "29/08/2024 15:30", "mode": "REM", "dir": "DIR", "corrente": "1,06 A", "velocidade": "1200 Rpm", "status": "ON"},
    {"tag": "EST10.48", "desc": "(B20.13) ESTEIRA AEREA CORTES P/ EMBALAGEM", "ua": "29/08/2024 15:30", "mode": "REM", "dir": "REV", "corrente": "0,51 A", "velocidade": "900 Rpm", "status": "ON"}
]


# --- LAYOUT FLUIDO E RESPONSIVO ---
class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=10):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._doLayout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def _doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        spacing = self.spacing()
        container_width = rect.width()

        if not self.itemList or container_width <= 0:
            return 0

        visible_items = [
            item for item in self.itemList 
            if item.widget() is not None and not item.widget().isHidden()
        ]

        if not visible_items:
            return 0

        min_card_width = visible_items[0].widget().minimumWidth()
        cols = max(1, (container_width + spacing) // (min_card_width + spacing))
        total_spacing = spacing * (cols - 1)
        item_width = (container_width - total_spacing) // cols

        line_height = 0
        current_col = 0

        for item in visible_items:
            widget = item.widget()
            item_height = widget.height()
            
            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), QSize(item_width, item_height)))

            line_height = max(line_height, item_height)
            current_col += 1

            if current_col >= cols:
                current_col = 0
                x = rect.x()
                y += line_height + spacing
                line_height = 0
            else:
                x += item_width + spacing

        return y + line_height - rect.y()


# --- WIDGET DO ÍCONE DO MOTOR (ISA-101: CORES NEUTRAS) ---
class MotorWidgetSVG(QWidget):
    def __init__(self, is_on=False, parent=None):
        super().__init__(parent)
        self.is_on = is_on
        self.setFixedSize(38, 28)

    def set_status(self, is_on):
        self.is_on = is_on
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor("#4B5563"), 1.2)
        painter.setPen(pen)

        body_color = QColor("#374151") if self.is_on else QColor("#9CA3AF")
        painter.setBrush(QBrush(body_color))
        painter.drawRoundedRect(8, 7, 24, 15, 2, 2)

        for y in [10, 13, 16, 19]:
            painter.drawLine(4, y, 8, y)

        dark_brush = QBrush(QColor("#1F2937"))
        painter.setBrush(dark_brush)
        painter.drawRect(32, 11, 5, 6)
        painter.drawRect(15, 3, 10, 4)

        painter.drawLine(11, 22, 11, 25)
        painter.drawLine(29, 22, 29, 25)
        painter.drawLine(7, 25, 33, 25)


# --- CARD INDIVIDUAL DO MOTOR ---
class MotorCard(QFrame):
    def __init__(self, data, main_app, parent=None):
        super().__init__(parent)
        self.data = data
        self.main_app = main_app
        self.setCursor(Qt.PointingHandCursor)
        
        self.setMinimumWidth(220)
        self.setMaximumWidth(1000)
        self.setFixedHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.setToolTip(f"Última Atualização: {self.data['ua']}")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(4)

        self.lbl_tag = QLabel(self.data['tag'])

        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(3)
        
        self.lbl_mode = self.create_badge(self.data['mode'], "#F3F4F6", "#374151", "#E5E7EB")
        self.lbl_dir = self.create_badge(self.data['dir'], "#F3F4F6", "#374151", "#E5E7EB")
        
        self.lbl_status = QLabel()
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setFixedHeight(16)
        self.lbl_status.setMinimumWidth(28)

        badges_layout.addWidget(self.lbl_mode)
        badges_layout.addWidget(self.lbl_dir)
        badges_layout.addWidget(self.lbl_status)

        top_layout.addWidget(self.lbl_tag)
        top_layout.addStretch()
        top_layout.addLayout(badges_layout)

        lbl_desc = QLabel(self.data['desc'])
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("""
            font-size: 11px; 
            font-weight: 700; 
            color: #1F2937; 
            border: none; 
            background: transparent;
        """)
        lbl_desc.setFixedHeight(30)

        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 2, 0, 0)
        
        data_layout = QVBoxLayout()
        data_layout.setSpacing(2)

        self.lbl_corr = QLabel()
        self.lbl_vel = QLabel()
        
        self.lbl_corr.setStyleSheet("font-size: 11px; color: #4B5563; border: none; background: transparent;")
        self.lbl_vel.setStyleSheet("font-size: 11px; color: #4B5563; border: none; background: transparent;")

        data_layout.addWidget(self.lbl_corr)
        data_layout.addWidget(self.lbl_vel)

        self.icon_widget = MotorWidgetSVG(self.data['status'] == "ON")

        body_layout.addLayout(data_layout)
        body_layout.addStretch()
        body_layout.addWidget(self.icon_widget, alignment=Qt.AlignVCenter)

        layout.addLayout(top_layout)
        layout.addWidget(lbl_desc)
        layout.addLayout(body_layout)

        self.update_style()

    def update_data_labels(self):
        self.lbl_corr.setText(f"Corrente: <b style='color:#111827;'>{self.data['corrente']}</b>")
        self.lbl_vel.setText(f"Velocidade: <b style='color:#111827;'>{self.data['velocidade']}</b>")

    def create_badge(self, text, bg_color, text_color, border_color="#E5E7EB"):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setFixedHeight(16)
        lbl.setMinimumWidth(26)
        lbl.setStyleSheet(f"""
            background-color: {bg_color};
            color: {text_color};
            font-size: 9px;
            font-weight: bold;
            border: 1px solid {border_color};
            border-radius: 3px;
            padding: 0 3px;
        """)
        return lbl

    def update_style(self):
        is_on = self.data['status'] == "ON"
        self.lbl_status.setText(self.data['status'])
        self.icon_widget.set_status(is_on)
        self.update_data_labels()

        if is_on:
            self.setStyleSheet("""
                MotorCard {
                    background-color: #FFFFFF;
                    border: 1px solid #D1D5DB;
                    border-radius: 6px;
                }
                MotorCard:hover {
                    background-color: #F8FAFC;
                    border: 1px solid #9CA3AF;
                }
            """)
            self.lbl_tag.setStyleSheet("font-size: 12px; font-weight: 800; color: #1F2937; border: none; background: transparent;")
            self.lbl_status.setStyleSheet("""
                background-color: #374151; color: #FFFFFF; font-size: 9px;
                font-weight: bold; border: 1px solid #1F2937; border-radius: 3px; padding: 0 3px;
            """)
        else:
            self.setStyleSheet("""
                MotorCard {
                    background-color: #F9FAFB;
                    border: 1px solid #E5E7EB;
                    border-radius: 6px;
                }
                MotorCard:hover {
                    background-color: #F3F4F6;
                    border: 1px solid #D1D5DB;
                }
            """)
            self.lbl_tag.setStyleSheet("font-size: 12px; font-weight: 800; color: #6B7280; border: none; background: transparent;")
            self.lbl_status.setStyleSheet("""
                background-color: #E5E7EB; color: #4B5563; font-size: 9px;
                font-weight: bold; border: 1px solid #D1D5DB; border-radius: 3px; padding: 0 3px;
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.main_app.open_faceplate(self.data)


# --- TELA GENÉRICA ---
class GenericScreenWidget(QWidget):
    def __init__(self, category, screen_name, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        lbl_msg = QLabel(f"Tela: {screen_name}\n[Categoria: {category}]")
        lbl_msg.setAlignment(Qt.AlignCenter)
        lbl_msg.setStyleSheet("font-size: 20px; font-weight: bold; color: #374151;")

        lbl_sub = QLabel("Esta tela está pronta para receber os componentes do seu módulo.")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet("font-size: 13px; color: #6b7280; margin-top: 8px;")

        layout.addWidget(lbl_msg)
        layout.addWidget(lbl_sub)


# --- APLICAÇÃO PRINCIPAL ---
class SupervisorioApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Supervisório de Motores - ISA 101")
        self.resize(1280, 750)
        self.setMinimumSize(600, 400)
        self.setStyleSheet("background-color: #F3F4F6;")

        self.cards_dict = {}
        self.current_status_filter = "ALL"
        self.created_screens = {}
        self.current_dialog = None

        self.init_ui()

    def init_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar Retrátil Lateral
        self.sidebar = SidebarWidget(self)
        self.sidebar.screen_requested.connect(self.navigate_to_screen)
        root_layout.addWidget(self.sidebar)

        # Gerenciador de Telas Stacked
        self.screen_stack = QStackedWidget()
        self.screen_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # === TELA PRINCIPAL (Motores) ===
        self.main_screen = QWidget()
        main_layout = QVBoxLayout(self.main_screen)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(8)

        # Cabeçalho ISA-101
        header = QFrame()
        header.setFixedHeight(44)
        header.setStyleSheet("background: #1F2937; border-radius: 4px;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 0, 12, 0)
        h_layout.setSpacing(15)

        lbl_title = QLabel("SUPERVISÓRIO DE MOTORES")
        lbl_title.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: bold; border: none; background: transparent;")

        self.lbl_clock = QLabel()
        self.lbl_clock.setStyleSheet("color: #9CA3AF; font-size: 11px; font-weight: 600; border: none; background: transparent;")
        
        self.timer_clock = QTimer(self)
        self.timer_clock.timeout.connect(self.update_clock)
        self.timer_clock.start(1000)
        self.update_clock()

        plc_box = QFrame()
        plc_box.setFixedHeight(24)
        plc_box.setStyleSheet("background: #111827; border: 1px solid #374151; border-radius: 3px;")
        p_layout = QHBoxLayout(plc_box)
        p_layout.setContentsMargins(8, 0, 8, 0)
        p_layout.setSpacing(6)

        dot = QLabel("●")
        dot.setStyleSheet("color: #22C55E; font-size: 10px; border: none; background: transparent;")

        lbl_plc = QLabel("PLC: ONLINE")
        lbl_plc.setStyleSheet("color: #E5E7EB; font-size: 10px; font-weight: bold; border: none; background: transparent;")

        p_layout.addWidget(dot)
        p_layout.addWidget(lbl_plc)

        kpi_box = QFrame()
        kpi_box.setFixedHeight(24)
        kpi_box.setStyleSheet("background: #111827; border: 1px solid #374151; border-radius: 3px;")
        k_layout = QHBoxLayout(kpi_box)
        k_layout.setContentsMargins(8, 0, 8, 0)
        k_layout.setSpacing(10)

        self.lbl_kpi_on = QLabel("ON: 0")
        self.lbl_kpi_off = QLabel("OFF: 0")
        self.lbl_kpi_alm = QLabel("ALM: 0")

        self.lbl_kpi_on.setStyleSheet("color: #E5E7EB; font-size: 10px; font-weight: bold; border: none; background: transparent;")
        self.lbl_kpi_off.setStyleSheet("color: #9CA3AF; font-size: 10px; font-weight: bold; border: none; background: transparent;")
        self.lbl_kpi_alm.setStyleSheet("color: #9CA3AF; font-size: 10px; font-weight: bold; border: none; background: transparent;")

        k_layout.addWidget(self.lbl_kpi_on)
        k_layout.addWidget(self.lbl_kpi_off)
        k_layout.addWidget(self.lbl_kpi_alm)

        h_layout.addWidget(lbl_title)
        h_layout.addWidget(self.lbl_clock)
        h_layout.addStretch()
        h_layout.addWidget(plc_box)
        h_layout.addWidget(kpi_box)

        # Barra de Filtros Neutra
        filter_bar = QFrame()
        filter_bar.setFixedHeight(42)
        filter_bar.setStyleSheet("background: #FFFFFF; border: 1px solid #D1D5DB; border-radius: 4px;")
        f_layout = QHBoxLayout(filter_bar)
        f_layout.setContentsMargins(10, 5, 10, 5)
        f_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisar por TAG ou Descrição...")
        self.search_input.setFixedHeight(30)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: #F9FAFB;
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                padding: 0 10px;
                font-size: 11px;
                color: #111827;
            }
            QLineEdit:focus {
                border: 1.5px solid #4B5563;
                background: #FFFFFF;
            }
        """)
        self.search_input.textChanged.connect(self.apply_filters)

        self.btn_filter_all = QPushButton("Todos")
        self.btn_filter_on = QPushButton("ON")
        self.btn_filter_off = QPushButton("OFF")
        self.btn_filter_alert = QPushButton("Alertas")

        self.filter_buttons = {
            "ALL": self.btn_filter_all,
            "ON": self.btn_filter_on,
            "OFF": self.btn_filter_off,
            "ALERT": self.btn_filter_alert
        }

        for mode, btn in self.filter_buttons.items():
            btn.setFixedHeight(28)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, m=mode: self.set_status_filter(m))

        f_layout.addWidget(self.search_input, stretch=1)
        f_layout.addWidget(self.btn_filter_all)
        f_layout.addWidget(self.btn_filter_on)
        f_layout.addWidget(self.btn_filter_off)
        f_layout.addWidget(self.btn_filter_alert)

        # Scroll e FlowLayout
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        
        self.flow_layout = FlowLayout(scroll_content, margin=0, spacing=10)
        self.populate_cards()

        scroll.setWidget(scroll_content)

        main_layout.addWidget(header)
        main_layout.addWidget(filter_bar)
        main_layout.addWidget(scroll)

        # Adiciona a tela principal ao QStackedWidget e mapeia no dicionário de telas
        self.screen_stack.addWidget(self.main_screen)
        self.created_screens["Circuitos->Cortes"] = self.main_screen
        self.created_screens["Circuitos->Secundária"] = self.main_screen

        # === TELA DE CADASTRO DE PLCs ===
        self.plc_cadastro_screen = PLCCadastroScreen()
        self.screen_stack.addWidget(self.plc_cadastro_screen)
        # Mapeia exatamente com o nome da categoria e subitem definidos na sidebar
        self.created_screens["PLCs->Cadastrar"] = self.plc_cadastro_screen

        root_layout.addWidget(self.screen_stack)
        self.update_counters()

    def update_clock(self):
        now = QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm:ss")
        self.lbl_clock.setText(f"|  {now}")

    def populate_cards(self):
        for data in MOTORES_DATA:
            card = MotorCard(data, self)
            self.cards_dict[data['tag']] = card
            self.flow_layout.addWidget(card)

    def set_status_filter(self, mode):
        self.current_status_filter = mode
        self.update_filter_button_styles()
        self.apply_filters()

    def update_filter_button_styles(self):
        total_all = len(MOTORES_DATA)
        total_on = sum(1 for m in MOTORES_DATA if m['status'] == "ON")
        total_off = sum(1 for m in MOTORES_DATA if m['status'] == "OFF")
        total_alert = 0

        self.btn_filter_all.setText(f"Todos ({total_all})")
        self.btn_filter_on.setText(f"ON ({total_on})")
        self.btn_filter_off.setText(f"OFF ({total_off})")
        self.btn_filter_alert.setText(f"Alertas ({total_alert})")

        base_style = """
            QPushButton {
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                padding: 0 10px;
                border: 1px solid #D1D5DB;
            }
        """

        for mode, btn in self.filter_buttons.items():
            if mode == self.current_status_filter:
                color_style = "background: #374151; color: #FFFFFF; border-color: #374151;"
            else:
                if mode == "ALERT" and total_alert > 0:
                    color_style = "background: #FEF3C7; color: #92400E; border-color: #F59E0B;"
                else:
                    color_style = "background: #FFFFFF; color: #374151;"

            btn.setStyleSheet(base_style + color_style)

    def apply_filters(self):
        search_text = self.search_input.text().lower().strip()

        for data in MOTORES_DATA:
            tag = data['tag']
            card = self.cards_dict[tag]

            matches_text = (search_text in tag.lower()) or (search_text in data['desc'].lower())
            
            matches_status = True
            if self.current_status_filter == "ON":
                matches_status = (data['status'] == "ON")
            elif self.current_status_filter == "OFF":
                matches_status = (data['status'] == "OFF")
            elif self.current_status_filter == "ALERT":
                matches_status = False

            if matches_text and matches_status:
                card.show()
            else:
                card.hide()

        self.flow_layout.update()

    def update_counters(self):
        total_on = sum(1 for m in MOTORES_DATA if m['status'] == "ON")
        total_off = sum(1 for m in MOTORES_DATA if m['status'] == "OFF")
        total_alm = 0

        self.lbl_kpi_on.setText(f"ON: {total_on}")
        self.lbl_kpi_off.setText(f"OFF: {total_off}")
        self.lbl_kpi_alm.setText(f"ALM: {total_alm}")

        if total_alm > 0:
            self.lbl_kpi_alm.setStyleSheet("color: #F87171; font-size: 10px; font-weight: bold; border: none; background: transparent;")
        else:
            self.lbl_kpi_alm.setStyleSheet("color: #9CA3AF; font-size: 10px; font-weight: bold; border: none; background: transparent;")

        self.update_filter_button_styles()

    def open_faceplate(self, data):
        if self.current_dialog is not None:
            try:
                self.current_dialog.reject()
            except RuntimeError:
                pass
            self.current_dialog = None

        dialog = FaceplateDialog(data, self, parent=self)
        dialog.setAttribute(Qt.WA_DeleteOnClose)
        self.current_dialog = dialog
        dialog.exec_()

    def update_motor_card(self, tag):
        if tag in self.cards_dict:
            self.cards_dict[tag].update_style()
            self.update_counters()
            self.apply_filters()

    def navigate_to_screen(self, category, screen_name):
        key = f"{category}->{screen_name}"

        if key not in self.created_screens:
            new_screen = GenericScreenWidget(category, screen_name)
            self.screen_stack.addWidget(new_screen)
            self.created_screens[key] = new_screen

        target_widget = self.created_screens[key]
        self.screen_stack.setCurrentWidget(target_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    font = QFont()
    font.setFamilies(["Segoe UI", "Helvetica Neue", "Arial", "sans-serif"])
    font.setPointSize(9)
    app.setFont(font)

    window = SupervisorioApp()
    window.show()
    sys.exit(app.exec_())