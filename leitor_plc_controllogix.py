import sys
import collections
import time
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
from pycomm3 import LogixDriver

# Configurações do CLP ControlLogix
PLC_IP = "172.16.40.3:44818"
TAG_FREQ = "INVERSOR_B23_01.POWER_FLEX_525.FREQUECIA_CMD"     # Tag de Frequência (Hz)
TAG_CORRENTE = "INVERSOR_B23_01.POWER_FLEX_525.CORRENTE"        # Tag de Corrente (A)
TAG_ROTACAO = "INVERSOR_B23_01.POWER_FLEX_525.ROTACAO"          # Tag de Rotação (RPM)
TAG_STATUS = "INVERSOR_B23_01.POWER_FLEX_525.CONTROL_STATUS"   # Word de Status (DINT / 32 bits)
TAG_NOME = "INVERSOR_B23_01.NOME"                             # Tag de Nome
TAG_CODIGO = "INVERSOR_B23_01.TAG"                            # Tag de Código/Identificação
SLOT = 0                                                      # Slot da CPU no rack


class WorkerThread(QtCore.QThread):
    """
    Thread dedicada para a comunicação Ethernet/IP via pycomm3.
    """
    data_received = QtCore.pyqtSignal(float, float, float, bool, bool, bool, bool, bool, str, str)  
    status_changed = QtCore.pyqtSignal(str, str)

    def __init__(self, ip, tag_freq, tag_corrente, tag_rotacao, tag_status, tag_nome, tag_codigo, interval_ms=100):
        super().__init__()
        self.ip = ip
        self.tag_freq = tag_freq
        self.tag_corrente = tag_corrente
        self.tag_rotacao = tag_rotacao
        self.tag_status = tag_status
        self.tag_nome = tag_nome
        self.tag_codigo = tag_codigo
        self.interval = interval_ms / 1000.0
        self.running = True

    def run(self):
        try:
            with LogixDriver(self.ip, slot=SLOT) as plc:
                self.status_changed.emit(f"ONLINE | {self.ip}", "#A0CA92")
                
                while self.running:
                    start_time = time.time()
                    
                    results = plc.read(
                        self.tag_freq, 
                        self.tag_corrente, 
                        self.tag_rotacao, 
                        self.tag_status,
                        self.tag_nome, 
                        self.tag_codigo
                    )
                    
                    freq_val = 0.0
                    corrente_val = 0.0
                    rotacao_val = 0.0
                    is_ligado = False
                    is_reverso = False
                    is_manual = False
                    is_remoto = False
                    is_ready = False
                    nome_val = "DESCONHECIDO"
                    codigo_val = "N/A"
                    
                    if results[0] and results[0].value is not None:
                        freq_val = float(results[0].value)

                    if results[1] and results[1].value is not None:
                        corrente_val = float(results[1].value)

                    if results[2] and results[2].value is not None:
                        rotacao_val = float(results[2].value)
                    
                    # Extração dos Bits do CONTROL_STATUS com inversão corrigida para REV e MAN/AUT
                    if results[3] and results[3].value is not None:
                        status_word = int(results[3].value)
                        is_ligado = bool((status_word >> 17) & 1)     # Bit 17: Run
                        is_reverso = not bool((status_word >> 24) & 1) # Bit 24: Invertido
                        is_manual = not bool((status_word >> 20) & 1)  # Bit 20: Invertido
                        is_remoto = bool((status_word >> 19) & 1)     # Bit 19: Remoto
                        is_ready = bool((status_word >> 16) & 1)      # Bit 16: Ready

                    if results[4] and results[4].value is not None:
                        nome_val = str(results[4].value)

                    if results[5] and results[5].value is not None:
                        codigo_val = str(results[5].value)

                    self.data_received.emit(freq_val, corrente_val, rotacao_val, is_ligado, is_reverso, is_manual, is_remoto, is_ready, nome_val, codigo_val)

                    elapsed = time.time() - start_time
                    sleep_time = max(0.01, self.interval - elapsed)
                    time.sleep(sleep_time)

        except Exception as e:
            self.status_changed.emit(f"FALHA COMM: {e}", "#E57373")

    def stop(self):
        self.running = False
        self.wait()


class FrequencyMonitorApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.max_points = 200
        self.freq_data = collections.deque([0.0] * self.max_points, maxlen=self.max_points)
        self.corrente_data = collections.deque([0.0] * self.max_points, maxlen=self.max_points)
        self.x_data = collections.deque(range(-self.max_points, 0), maxlen=self.max_points)

        self.init_ui()

        self.worker = WorkerThread(
            PLC_IP, TAG_FREQ, TAG_CORRENTE, TAG_ROTACAO, TAG_STATUS, TAG_NOME, TAG_CODIGO, interval_ms=100
        )
        self.worker.data_received.connect(self.update_data)
        self.worker.status_changed.connect(self.update_status)
        self.worker.start()

    def init_ui(self):
        self.setWindowTitle("IHM ISA-101 - Inversor PowerFlex 525")
        self.resize(1120, 620)

        central_widget = QtWidgets.QWidget()
        central_widget.setStyleSheet("background-color: #1E2226;")
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # 1. Painel Cabeçalho Padrão Industrial
        title_card = QtWidgets.QFrame()
        title_card.setStyleSheet("background-color: #2A2E33; border: 1px solid #3A3F45; border-radius: 4px; padding: 6px;")
        title_layout = QtWidgets.QHBoxLayout(title_card)

        info_text_layout = QtWidgets.QVBoxLayout()
        
        self.tag_label = QtWidgets.QLabel("TAG: --")
        self.tag_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #B0B5BA;")
        info_text_layout.addWidget(self.tag_label)

        self.name_label = QtWidgets.QLabel("EQUIPAMENTO: AGUARDANDO COMUNICAÇÃO...")
        self.name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #E0E0E0;")
        info_text_layout.addWidget(self.name_label)

        title_layout.addLayout(info_text_layout)
        title_layout.addStretch()

        self.status_label = QtWidgets.QLabel("CONECTANDO...")
        self.status_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #80868B; padding-right: 8px;")
        title_layout.addWidget(self.status_label)

        main_layout.addWidget(title_card)

        # 2. Mostradores Analógicos/Digitais ISA-101
        cards_layout = QtWidgets.QHBoxLayout()
        cards_layout.setSpacing(10)

        card_style = "background-color: #2A2E33; border: 1px solid #3A3F45; border-radius: 4px; padding: 8px;"
        title_style = "font-size: 11px; font-weight: bold; color: #9AA0A6; letter-spacing: 1px;"
        value_style = "font-size: 32px; font-weight: bold; color: #FFFFFF;"

        # Card de Status do Inversor
        status_card = QtWidgets.QFrame()
        status_card.setStyleSheet(card_style)
        status_card_layout = QtWidgets.QVBoxLayout(status_card)

        status_card_title = QtWidgets.QLabel("ESTADO OPERACIONAL")
        status_card_title.setStyleSheet(title_style)

        status_sub_layout = QtWidgets.QHBoxLayout()
        status_sub_layout.setSpacing(4)

        self.drive_status_label = QtWidgets.QLabel("PARADO")
        self.drive_status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.drive_status_label.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #B0B5BA; "
            "background-color: #3A3F45; border-radius: 3px; padding: 6px;"
        )

        self.drive_dir_label = QtWidgets.QLabel("DIR")
        self.drive_dir_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.drive_dir_label.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #B0B5BA; "
            "background-color: #3A3F45; border-radius: 3px; padding: 6px; min-width: 36px;"
        )

        self.drive_mode_label = QtWidgets.QLabel("AUT")
        self.drive_mode_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.drive_mode_label.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #B0B5BA; "
            "background-color: #3A3F45; border-radius: 3px; padding: 6px; min-width: 36px;"
        )

        self.drive_loc_label = QtWidgets.QLabel("LOC")
        self.drive_loc_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.drive_loc_label.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #B0B5BA; "
            "background-color: #3A3F45; border-radius: 3px; padding: 6px; min-width: 36px;"
        )

        self.drive_ready_label = QtWidgets.QLabel("RDY")
        self.drive_ready_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.drive_ready_label.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #B0B5BA; "
            "background-color: #3A3F45; border-radius: 3px; padding: 6px; min-width: 36px;"
        )

        status_sub_layout.addWidget(self.drive_status_label, stretch=3)
        status_sub_layout.addWidget(self.drive_dir_label, stretch=1)
        status_sub_layout.addWidget(self.drive_mode_label, stretch=1)
        status_sub_layout.addWidget(self.drive_loc_label, stretch=1)
        status_sub_layout.addWidget(self.drive_ready_label, stretch=1)

        status_card_layout.addWidget(status_card_title)
        status_card_layout.addLayout(status_sub_layout)
        cards_layout.addWidget(status_card)

        # Card de Frequência
        freq_card = QtWidgets.QFrame()
        freq_card.setStyleSheet(card_style)
        freq_card_layout = QtWidgets.QVBoxLayout(freq_card)
        
        freq_title = QtWidgets.QLabel("FREQUÊNCIA CMD")
        freq_title.setStyleSheet(title_style)
        self.freq_value_label = QtWidgets.QLabel("0.00 Hz")
        self.freq_value_label.setStyleSheet(value_style)
        
        freq_card_layout.addWidget(freq_title)
        freq_card_layout.addWidget(self.freq_value_label)
        cards_layout.addWidget(freq_card)

        # Card de Corrente
        curr_card = QtWidgets.QFrame()
        curr_card.setStyleSheet(card_style)
        curr_card_layout = QtWidgets.QVBoxLayout(curr_card)

        curr_title = QtWidgets.QLabel("CORRENTE MOTOR")
        curr_title.setStyleSheet(title_style)
        self.curr_value_label = QtWidgets.QLabel("0.00 A")
        self.curr_value_label.setStyleSheet(value_style)

        curr_card_layout.addWidget(curr_title)
        curr_card_layout.addWidget(self.curr_value_label)
        cards_layout.addWidget(curr_card)

        # Card de Rotação
        rot_card = QtWidgets.QFrame()
        rot_card.setStyleSheet(card_style)
        rot_card_layout = QtWidgets.QVBoxLayout(rot_card)

        rot_title = QtWidgets.QLabel("VELOCIDADE")
        rot_title.setStyleSheet(title_style)
        self.rot_value_label = QtWidgets.QLabel("0 RPM")
        self.rot_value_label.setStyleSheet(value_style)

        rot_card_layout.addWidget(rot_title)
        rot_card_layout.addWidget(self.rot_value_label)
        cards_layout.addWidget(rot_card)

        main_layout.addLayout(cards_layout)

        # 3. Gráfico de Tendência (Trend Graphic conforme ISA-101)
        pg.setConfigOption('background', '#2A2E33')
        pg.setConfigOption('foreground', '#B0B5BA')

        self.plot_widget = pg.PlotWidget(title="<span style='color: #E0E0E0; font-size: 13px;'>Tendência: Frequência vs Corrente</span>")
        self.plot_widget.setLabel('left', 'Frequência', units='Hz', color='#B0B5BA')
        self.plot_widget.setLabel('bottom', 'Amostras (Tempo Real)')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.15)
        self.plot_widget.setYRange(0, 65)

        freq_pen = pg.mkPen(color='#E0E0E0', width=2)
        self.freq_curve = self.plot_widget.plot(self.x_data, self.freq_data, pen=freq_pen, name="Frequência")

        self.curr_plot_item = pg.ViewBox()
        self.plot_widget.scene().addItem(self.curr_plot_item)
        self.plot_widget.getAxis('right').linkToView(self.curr_plot_item)
        self.curr_plot_item.setXLink(self.plot_widget.plotItem)
        
        self.plot_widget.showAxis('right')
        self.plot_widget.setLabel('right', 'Corrente', units='A', color='#81D4FA')

        curr_pen = pg.mkPen(color='#81D4FA', width=1.5, style=QtCore.Qt.PenStyle.DashLine)
        self.curr_curve = pg.PlotDataItem(self.x_data, self.corrente_data, pen=curr_pen)
        self.curr_plot_item.addItem(self.curr_curve)

        self.plot_widget.plotItem.vb.sigResized.connect(self.update_views)

        main_layout.addWidget(self.plot_widget)

    def update_views(self):
        self.curr_plot_item.setGeometry(self.plot_widget.plotItem.vb.sceneBoundingRect())
        self.curr_plot_item.linkedViewChanged(self.plot_widget.plotItem.vb, self.curr_plot_item.XAxis)

    @QtCore.pyqtSlot(float, float, float, bool, bool, bool, bool, bool, str, str)
    def update_data(self, freq, corrente, rotacao, is_ligado, is_reverso, is_manual, is_remoto, is_ready, nome, codigo_tag):
        if codigo_tag:
            self.tag_label.setText(f"TAG: {codigo_tag.upper()}")
        if nome:
            self.name_label.setText(f"EQUIPAMENTO: {nome.upper()}")
        
        if is_ligado:
            self.drive_status_label.setText("EM OPERAÇÃO")
            self.drive_status_label.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #FFFFFF; "
                "background-color: #2E5A36; border: 1px solid #4CAF50; border-radius: 3px; padding: 6px;"
            )
        else:
            self.drive_status_label.setText("PARADO")
            self.drive_status_label.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #B0B5BA; "
                "background-color: #3A3F45; border: 1px solid #4A4E53; border-radius: 3px; padding: 6px;"
            )

        if is_reverso:
            self.drive_dir_label.setText("REV")
            self.drive_dir_label.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #FFD54F; "
                "background-color: #4A3E22; border: 1px solid #FFC107; border-radius: 3px; padding: 6px;"
            )
        else:
            self.drive_dir_label.setText("DIR")
            self.drive_dir_label.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #B0B5BA; "
                "background-color: #3A3F45; border: 1px solid #4A4E53; border-radius: 3px; padding: 6px;"
            )

        if is_manual:
            self.drive_mode_label.setText("MAN")
            self.drive_mode_label.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #4FC3F7; "
                "background-color: #1A3A4A; border: 1px solid #03A9F4; border-radius: 3px; padding: 6px;"
            )
        else:
            self.drive_mode_label.setText("AUT")
            self.drive_mode_label.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #B0B5BA; "
                "background-color: #3A3F45; border: 1px solid #4A4E53; border-radius: 3px; padding: 6px;"
            )

        if is_remoto:
            self.drive_loc_label.setText("REM")
            self.drive_loc_label.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #CE93D8; "
                "background-color: #3A2A40; border: 1px solid #AB47BC; border-radius: 3px; padding: 6px;"
            )
        else:
            self.drive_loc_label.setText("LOC")
            self.drive_loc_label.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #B0B5BA; "
                "background-color: #3A3F45; border: 1px solid #4A4E53; border-radius: 3px; padding: 6px;"
            )

        if is_ready:
            self.drive_ready_label.setText("RDY")
            self.drive_ready_label.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #A0CA92; "
                "background-color: #2E4A30; border: 1px solid #81C784; border-radius: 3px; padding: 6px;"
            )
        else:
            self.drive_ready_label.setText("RDY")
            self.drive_ready_label.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #B0B5BA; "
                "background-color: #3A3F45; border: 1px solid #4A4E53; border-radius: 3px; padding: 6px;"
            )

        self.freq_value_label.setText(f"{freq:.2f} Hz")
        self.curr_value_label.setText(f"{corrente:.2f} A")
        self.rot_value_label.setText(f"{rotacao:.0f} RPM")
        
        self.freq_data.append(freq)
        self.corrente_data.append(corrente)

        self.freq_curve.setData(self.x_data, self.freq_data)
        self.curr_curve.setData(self.x_data, self.corrente_data)

    @QtCore.pyqtSlot(str, str)
    def update_status(self, text, color_hex):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {color_hex};")

    def closeEvent(self, event):
        self.worker.stop()
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = FrequencyMonitorApp()
    window.show()
    sys.exit(app.exec())