import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QFont
from PyQt5.QtWidgets import (
    QWidget, QFrame, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QStackedLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QGroupBox
)

# Tenta importar o TrendWindow, tratando exceção caso o módulo não esteja presente
try:
    from trend_chart import TrendWindow
except ImportError:
    TrendWindow = None


class FaceplateDialog(QDialog):
    def __init__(self, data, main_app, parent=None):
        super().__init__(parent)
        self.data = data
        self.main_app = main_app
        
        if 'modo' not in self.data:
            self.data['modo'] = 'MAN'  # 'MAN' ou 'AUTO'
            
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(450, 530)
        self.setStyleSheet("""
            QDialog {
                background-color: #EAEBF0; 
                border: 1.5px solid #4B5563; 
                border-radius: 4px;
            }
        """)
        
        self.drag_position = None
        self.trend_win = None
        self.status_labels = {}

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- 1. CABEÇALHO (ISA-101) ---
        header = QFrame()
        header.setFixedHeight(34)
        header.setStyleSheet("background: #1F2937; border-bottom: 1px solid #374151;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 0, 12, 0)

        lbl_header_tag = QLabel(self.data.get('tag', 'TAG'))
        lbl_header_tag.setStyleSheet("font-weight: bold; color: #FFFFFF; font-size: 13px; border: none; background: transparent;")

        btn_close = QPushButton("×")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("color: #9CA3AF; font-size: 20px; font-weight: bold; border: none; background: transparent;")
        btn_close.clicked.connect(self.close)

        h_layout.addWidget(lbl_header_tag)
        h_layout.addStretch()
        h_layout.addWidget(btn_close)

        # --- 2. BARRA DE ABAS ---
        tabs_frame = QFrame()
        tabs_frame.setFixedHeight(36)
        tabs_frame.setStyleSheet("background: #D1D5DB; border-bottom: 1px solid #9CA3AF;")
        t_layout = QHBoxLayout(tabs_frame)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.setSpacing(0)

        self.tab_buttons = []
        tabs_names = ["Comando", "Alarmes", "Configuração", "Interlocks", "Outros"]

        for i, name in enumerate(tabs_names):
            btn = QPushButton(name)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(36)
            btn.clicked.connect(lambda _, idx=i: self.switch_tab(idx))
            self.tab_buttons.append(btn)
            t_layout.addWidget(btn)

        # --- 3. CONTAINER DAS PÁGINAS (STACKED LAYOUT) ---
        stack_container = QWidget()
        self.stack = QStackedLayout(stack_container)
        self.stack.setContentsMargins(0, 0, 0, 0)

        # === ABA 0: COMANDO ===
        tab_cmd = QWidget()
        v_cmd = QVBoxLayout(tab_cmd)
        v_cmd.setContentsMargins(12, 10, 12, 10)
        v_cmd.setSpacing(8)

        # Título e Acesso ao Gráfico
        title_box = QHBoxLayout()
        title_box.setAlignment(Qt.AlignCenter)

        lbl_title = QLabel(f"[ {self.data.get('tag', '')} ] - {self.data.get('desc', '')}")
        lbl_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #111827; border: none; background: transparent;")

        btn_chart = QPushButton("📊")
        btn_chart.setToolTip("Abrir Gráfico de Tendência")
        btn_chart.setCursor(Qt.PointingHandCursor)
        btn_chart.setStyleSheet("""
            QPushButton {
                font-size: 12px; border: 1px solid #9CA3AF;
                background-color: #F3F4F6; border-radius: 3px; padding: 2px 6px;
            }
            QPushButton:hover { background-color: #D1D5DB; }
        """)
        btn_chart.clicked.connect(self.open_trend_popup)

        title_box.addWidget(lbl_title)
        title_box.addWidget(btn_chart)
        v_cmd.addLayout(title_box)

        # Estilo Padrão para os Grupos/Seções
        group_style = """
            QGroupBox {
                font-size: 9px; font-weight: bold; color: #4B5563;
                border: 1px solid #CBD5E1; border-radius: 4px;
                margin-top: 6px; background-color: #F8FAFC;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 8px; padding: 0 3px; background-color: #EAEBF0;
            }
        """

        # --- SEÇÃO 1: MODO DE OPERAÇÃO ---
        gb_mode = QGroupBox("MODO DE OPERAÇÃO")
        gb_mode.setStyleSheet(group_style)
        mode_layout = QHBoxLayout(gb_mode)
        mode_layout.setContentsMargins(10, 8, 10, 8)
        mode_layout.setAlignment(Qt.AlignCenter)
        mode_layout.setSpacing(12)

        self.btn_man = QPushButton("MANUAL")
        self.btn_auto = QPushButton("AUTOMÁTICO")

        for b in [self.btn_man, self.btn_auto]:
            b.setFixedSize(120, 26)
            b.setCursor(Qt.PointingHandCursor)

        self.btn_man.clicked.connect(lambda: self.set_control_mode('MAN'))
        self.btn_auto.clicked.connect(lambda: self.set_control_mode('AUTO'))

        mode_layout.addWidget(self.btn_man)
        mode_layout.addWidget(self.btn_auto)
        v_cmd.addWidget(gb_mode)

        # --- SEÇÃO 2: PARÂMETROS DO PROCESSO ---
        gb_params = QGroupBox("VARIÁVEIS DO PROCESSO")
        gb_params.setStyleSheet(group_style)
        form_grid = QGridLayout(gb_params)
        form_grid.setContentsMargins(10, 8, 10, 8)
        form_grid.setHorizontalSpacing(10)
        form_grid.setVerticalSpacing(4)
        form_grid.setAlignment(Qt.AlignCenter)

        vel_str = str(self.data.get('velocidade', '0')).replace(' Rpm', '').strip()
        rpm_val = int(vel_str) if vel_str.isdigit() else 0
        freq_calc = f"{((rpm_val / 1800) * 60):.2f}".replace('.', ',')
        corr_str = str(self.data.get('corrente', '0')).replace(' A', '').strip()

        self.inp_setpoint = self.add_form_row(form_grid, 0, "SetPoint", freq_calc, "Hz", editable=True, is_numeric=True)
        self.add_form_row(form_grid, 1, "Corrente", corr_str, "A", editable=False)
        self.add_form_row(form_grid, 2, "Vel. Atual", str(rpm_val), "Rpm", editable=False)
        self.add_form_row(form_grid, 3, "Frequência", freq_calc, "Hz", editable=False)
        
        v_cmd.addWidget(gb_params)

        # --- SEÇÃO 3: COMANDOS OPERACIONAIS ---
        gb_cmd = QGroupBox("AÇÃO DE COMANDO")
        gb_cmd.setStyleSheet(group_style)
        cmd_layout = QHBoxLayout(gb_cmd)
        cmd_layout.setContentsMargins(10, 8, 10, 8)
        cmd_layout.setAlignment(Qt.AlignCenter)
        cmd_layout.setSpacing(12)

        self.btn_off = QPushButton()
        self.btn_on = QPushButton()

        for b in [self.btn_off, self.btn_on]:
            b.setFixedSize(120, 28)
            b.setCursor(Qt.PointingHandCursor)

        self.btn_off.clicked.connect(lambda: self.send_command(False))
        self.btn_on.clicked.connect(lambda: self.send_command(True))

        cmd_layout.addWidget(self.btn_off)
        cmd_layout.addWidget(self.btn_on)
        v_cmd.addWidget(gb_cmd)

        # --- SEÇÃO 4: PAINEL DE STATUS E INTERLOCKS ---
        status_box = QFrame()
        status_box.setStyleSheet("border: 1px solid #CBD5E1; background: #E2E8F0; border-radius: 4px;")
        s_layout = QVBoxLayout(status_box)
        s_layout.setContentsMargins(8, 6, 8, 6)
        s_layout.setSpacing(4)

        lbl_s_title = QLabel("STATUS E INTERLOCKS")
        lbl_s_title.setStyleSheet("font-size: 9px; font-weight: bold; color: #4B5563; border: none; background: transparent;")

        grid_status = QGridLayout()
        grid_status.setSpacing(3)
        status_items = ["IN-STS", "READY", "INTERT", "FALHA", "EMERG", "FCURS", "REV", "REM", "MAN", "COMM"]

        for idx, st in enumerate(status_items):
            item = QLabel(st)
            item.setAlignment(Qt.AlignCenter)
            self.status_labels[st] = item
            grid_status.addWidget(item, idx // 5, idx % 5)

        s_layout.addWidget(lbl_s_title)
        s_layout.addLayout(grid_status)
        v_cmd.addWidget(status_box)

        # === DEMAIS ABAS ===
        tab_alarm = self.create_table_tab(["Horário", "Alarme", "Estado"], [["06:18:02", "Sobrecorrente Motor", "Ativo"]])
        tab_config = self.create_config_tab()
        tab_interlock = self.create_table_tab(["Condição", "Status"], [["Nível Mínimo Tanque", "OK"], ["Presença de Fase", "OK"]])
        tab_other = self.create_other_tab()

        self.stack.addWidget(tab_cmd)
        self.stack.addWidget(tab_alarm)
        self.stack.addWidget(tab_config)
        self.stack.addWidget(tab_interlock)
        self.stack.addWidget(tab_other)

        # Adiciona elementos ao Layout Principal
        main_layout.addWidget(header)
        main_layout.addWidget(tabs_frame)
        main_layout.addWidget(stack_container)

        self.switch_tab(0)
        self.update_ui_state()

    def open_trend_popup(self):
        if TrendWindow is None:
            return
            
        if self.trend_win is None or not self.trend_win.isVisible():
            self.trend_win = TrendWindow(self.data, self)
            self.trend_win.show()
        else:
            self.trend_win.raise_()
            self.trend_win.activateWindow()

    def add_form_row(self, grid, row, label, value, unit, editable=False, is_numeric=False):
        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #374151; border: none; background: transparent;")

        inp = QLineEdit(str(value))
        inp.setAlignment(Qt.AlignRight)
        inp.setFixedSize(90, 24)

        if is_numeric and editable:
            validator = QDoubleValidator(0.0, 100.0, 2, inp)
            validator.setNotation(QDoubleValidator.StandardNotation)
            inp.setValidator(validator)

        if not editable:
            inp.setReadOnly(True)
            inp.setFocusPolicy(Qt.NoFocus)
            # Fonte forte e fundo destacado para variáveis do processo (PVs)
            inp.setStyleSheet("""
                QLineEdit {
                    background-color: #E2E8F0;
                    border: 1px solid #CBD5E1;
                    border-radius: 3px;
                    font-size: 11px;
                    font-weight: bold;
                    color: #0F172A;
                    padding-right: 4px;
                }
            """)

        u_lbl = QLabel(unit)
        u_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #475569; border: none; background: transparent;")

        grid.addWidget(lbl, row, 0)
        grid.addWidget(inp, row, 1)
        grid.addWidget(u_lbl, row, 2)
        
        return inp

    def create_table_tab(self, headers, data):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(10, 10, 10, 10)

        table = QTableWidget(len(data), len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF; gridline-color: #E5E7EB;
                font-size: 11px; border: 1px solid #9CA3AF; border-radius: 2px;
            }
            QHeaderView::section {
                background-color: #374151; color: #FFFFFF;
                font-size: 11px; font-weight: bold; border: none; padding: 4px; height: 24px;
            }
            QTableWidget::item { padding: 4px; color: #111827; }
        """)

        for r, row in enumerate(data):
            for c, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(r, c, item)

        l.addWidget(table)
        return w

    def create_config_tab(self):
        w = QWidget()
        l = QGridLayout(w)
        l.setContentsMargins(16, 16, 16, 16)
        self.add_form_row(l, 0, "Freq. Mínima", "5,0", "Hz", editable=True, is_numeric=True)
        self.add_form_row(l, 1, "Freq. Máxima", "60,0", "Hz", editable=True, is_numeric=True)
        l.setRowStretch(2, 1)
        return w

    def create_other_tab(self):
        w = QWidget()
        l = QGridLayout(w)
        l.setContentsMargins(16, 16, 16, 16)
        self.add_form_row(l, 0, "Horas Trab.", "1240", "h", editable=False)
        l.setRowStretch(1, 1)
        return w

    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.tab_buttons):
            if i == index:
                btn.setStyleSheet("background: #EAEBF0; color: #111827; font-weight: bold; border: none; border-bottom: 3px solid #2563EB;")
            else:
                btn.setStyleSheet("background: #D1D5DB; color: #4B5563; font-weight: 600; border: none;")

    def set_control_mode(self, mode):
        self.data['modo'] = mode
        self.update_ui_state()
        if hasattr(self.main_app, 'update_motor_mode'):
            self.main_app.update_motor_mode(self.data['tag'], mode)

    def update_ui_state(self):
        is_manual = (self.data.get('modo', 'MAN') == 'MAN')
        is_on = (self.data.get('status') == "ON")

        # 1. Estilização do Seletor de Modo
        style_active_mode = "background: #374151; color: #FFFFFF; font-weight: bold; border: 1px solid #1F2937; border-radius: 3px; font-size: 10px;"
        style_inactive_mode = "background: #FFFFFF; color: #4B5563; font-weight: bold; border: 1px solid #9CA3AF; border-radius: 3px; font-size: 10px;"

        if is_manual:
            self.btn_man.setStyleSheet(style_active_mode)
            self.btn_man.setEnabled(False)
            self.btn_auto.setStyleSheet(style_inactive_mode)
            self.btn_auto.setEnabled(True)
        else:
            self.btn_auto.setStyleSheet(style_active_mode)
            self.btn_auto.setEnabled(False)
            self.btn_man.setStyleSheet(style_inactive_mode)
            self.btn_man.setEnabled(True)

        # 2. Habilitação do Setpoint
        if is_manual:
            self.inp_setpoint.setReadOnly(False)
            self.inp_setpoint.setFocusPolicy(Qt.StrongFocus)
            self.inp_setpoint.setStyleSheet("""
                QLineEdit {
                    background: #FFFFFF; border: 1.5px solid #2563EB; border-radius: 3px;
                    font-size: 11px; font-weight: bold; color: #111827; padding-right: 4px;
                }
                QLineEdit:focus { border: 2px solid #1D4ED8; background: #F0F9FF; }
            """)
        else:
            self.inp_setpoint.setReadOnly(True)
            self.inp_setpoint.setFocusPolicy(Qt.NoFocus)
            self.inp_setpoint.setStyleSheet("""
                QLineEdit {
                    background: #E2E8F0; border: 1px solid #CBD5E1; border-radius: 3px;
                    font-size: 11px; font-weight: bold; color: #64748B; padding-right: 4px;
                }
            """)

        # 3. Atualização dos Botões de Comando
        style_state_confirmed = "background: #374151; color: #FFFFFF; font-weight: bold; border: 1.5px solid #1F2937; border-radius: 3px; font-size: 11px;"
        style_action_available = "background: #FFFFFF; color: #1F2937; font-weight: bold; border: 1.5px solid #6B7280; border-radius: 3px; font-size: 11px;"
        style_disabled_cmd = "background: #E2E8F0; color: #94A3B8; font-weight: bold; border: 1px solid #CBD5E1; border-radius: 3px; font-size: 11px;"

        if not is_manual:
            self.btn_on.setText("LIGADO" if is_on else "LIGAR")
            self.btn_off.setText("DESLIGAR" if is_on else "DESLIGADO")
            self.btn_on.setStyleSheet(style_disabled_cmd)
            self.btn_off.setStyleSheet(style_disabled_cmd)
            self.btn_on.setEnabled(False)
            self.btn_off.setEnabled(False)
        else:
            if is_on:
                self.btn_on.setText("LIGADO")
                self.btn_on.setStyleSheet(style_state_confirmed)
                self.btn_on.setEnabled(False)

                self.btn_off.setText("DESLIGAR")
                self.btn_off.setStyleSheet(style_action_available)
                self.btn_off.setEnabled(True)
            else:
                self.btn_off.setText("DESLIGADO")
                self.btn_off.setStyleSheet(style_state_confirmed)
                self.btn_off.setEnabled(False)

                self.btn_on.setText("LIGAR")
                self.btn_on.setStyleSheet(style_action_available)
                self.btn_on.setEnabled(True)

        # 4. Atualização da Matriz de Status
        self.update_status_matrix(is_manual)

    def update_status_matrix(self, is_manual):
        for st, lbl in self.status_labels.items():
            is_fault = (st == "FALHA" and self.data.get('falha', False))
            is_emerg = (st == "EMERG" and self.data.get('emergencia', False))
            is_interlock = (st == "INTERT" and self.data.get('interlock', False))
            is_man_active = (st == "MAN" and is_manual)
            is_rem_active = (st == "REM" and not is_manual)

            if is_fault or is_emerg:
                bg, color, border = "#B91C1C", "#FFFFFF", "#991B1B"
            elif is_interlock:
                bg, color, border = "#D97706", "#FFFFFF", "#B45309"
            elif is_man_active or is_rem_active:
                bg, color, border = "#475569", "#FFFFFF", "#334155"
            else:
                bg, color, border = "#CBD5E1", "#334155", "#94A3B8"

            lbl.setStyleSheet(f"""
                background: {bg}; color: {color}; font-size: 9px;
                font-weight: bold; padding: 3px; border: 1px solid {border}; border-radius: 2px;
            """)

    def send_command(self, turn_on):
        new_status = "ON" if turn_on else "OFF"
        self.data['status'] = new_status
        self.update_ui_state()
        if hasattr(self.main_app, 'update_motor_card'):
            self.main_app.update_motor_card(self.data['tag'])

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.y() <= 34:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def closeEvent(self, event):
        if self.trend_win and self.trend_win.isVisible():
            self.trend_win.close()
        super().closeEvent(event)