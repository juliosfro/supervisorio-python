from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QLabel, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)


class PLCCadastroScreen(QWidget):
    """Tela de Cadastro e Gerenciamento de PLCs aderente ao ISA-101 e responsiva para 7 polegadas (sem scroll bar)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Layout Principal contendo APENAS o conteúdo da tela (sem Sidebar)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)
        self.setStyleSheet("background-color: #1E1E1E;")

        # Título Centralizado
        title_label = QLabel("CADASTRO E GERENCIAMENTO DE PLCs")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 16px;
                font-weight: bold;
                background-color: #2B2B2B;
                padding: 10px;
                border-radius: 4px;
            }
        """)
        main_layout.addWidget(title_label)

        # Container interno dividido em Formulário e Tabela
        body_layout = QHBoxLayout()
        body_layout.setSpacing(15)

        # Painel Esquerdo: Formulário de Cadastro
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #242424;
                border: 1px solid #3A3A3A;
                border-radius: 6px;
            }
        """)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(8)

        form_title = QLabel("Dados do Controlador")
        form_title.setStyleSheet("color: #E0E0E0; font-size: 13px; font-weight: bold; border: none;")
        form_layout.addWidget(form_title)

        # Campos do Formulário
        self.input_tag = self.create_form_field(form_layout, "Tag do PLC:", "ex: PLC_CORTE_01")
        self.input_ip = self.create_form_field(form_layout, "Endereço IP:", "ex: 192.168.0.10")
        self.input_port = self.create_form_field(form_layout, "Porta Modbus:", "502")
        
        # Modelo do PLC (ComboBox)
        model_label = QLabel("Modelo / Fabricante:")
        model_label.setStyleSheet("color: #A0A0A0; font-size: 11px; border: none;")
        form_layout.addWidget(model_label)
        
        self.combo_model = QComboBox()
        self.combo_model.addItems(["Rockwell Micro850", "Rockwell MicroLogix 1400", "Modbus TCP Genérico", "Siemens S7-1200"])
        self.combo_model.setFixedHeight(30)
        self.combo_model.setStyleSheet("""
            QComboBox {
                background-color: #1E1E1E; color: #FFFFFF; border: 1px solid #3A3A3A;
                border-radius: 3px; padding-left: 5px; font-size: 12px;
            }
            QComboBox::drop-down { border: 0px; }
            QComboBox QAbstractItemView {
                background-color: #2B2B2B; color: #FFFFFF; selection-background-color: #454545;
            }
        """)
        form_layout.addWidget(self.combo_model)

        form_layout.addStretch()

        # Botões de Ação do Formulário
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_test = QPushButton("Testar")
        self.btn_test.setFixedHeight(35)
        self.btn_test.setCursor(Qt.PointingHandCursor)
        self.btn_test.setStyleSheet("""
            QPushButton {
                background-color: #3A3A3A; color: #FFFFFF; font-weight: bold;
                border: none; border-radius: 3px; font-size: 12px;
            }
            QPushButton:hover { background-color: #4A4A4A; }
        """)
        self.btn_test.clicked.connect(self.test_connection)
        btn_layout.addWidget(self.btn_test)

        self.btn_save = QPushButton("Salvar")
        self.btn_save.setFixedHeight(35)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #2D5A27; color: #FFFFFF; font-weight: bold;
                border: none; border-radius: 3px; font-size: 12px;
            }
            QPushButton:hover { background-color: #387032; }
        """)
        self.btn_save.clicked.connect(self.save_plc)
        btn_layout.addWidget(self.btn_save)

        form_layout.addLayout(btn_layout)
        body_layout.addWidget(form_frame, 1)

        # Painel Direito: Tabela de PLCs Cadastrados
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                background-color: #242424;
                border: 1px solid #3A3A3A;
                border-radius: 6px;
            }
        """)
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(10, 10, 10, 10)
        table_layout.setSpacing(5)

        table_title = QLabel("PLCs Cadastrados na Rede")
        table_title.setStyleSheet("color: #E0E0E0; font-size: 13px; font-weight: bold; border: none;")
        table_layout.addWidget(table_title)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Tag", "IP", "Modelo", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
                gridline-color: #3A3A3A;
                border: 1px solid #3A3A3A;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #2B2B2B;
                color: #FFFFFF;
                padding: 4px;
                border: 1px solid #3A3A3A;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 4px;
            }
        """)
        
        # Inserir alguns dados de exemplo padrão
        sample_data = [
            ("PLC_CORTE_01", "192.168.0.10", "Micro850", "Online"),
            ("PLC_EMB_02", "192.168.0.12", "MicroLogix 1400", "Online"),
            ("PLC_SALA_03", "192.168.0.15", "Modbus TCP", "Offline")
        ]
        self.table.setRowCount(len(sample_data))
        for row, data in enumerate(sample_data):
            for col, text in enumerate(data):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                if col == 3:
                    item.setForeground(QColor("#2D5A27") if text == "Online" else QColor("#A0A0A0"))
                self.table.setItem(row, col, item)

        table_layout.addWidget(self.table)
        body_layout.addWidget(table_frame, 2)

        main_layout.addLayout(body_layout)

    def create_form_field(self, layout, label_text, placeholder):
        label = QLabel(label_text)
        label.setStyleSheet("color: #A0A0A0; font-size: 11px; border: none;")
        layout.addWidget(label)

        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.setFixedHeight(30)
        line_edit.setStyleSheet("""
            QLineEdit {
                background-color: #1E1E1E; color: #FFFFFF; border: 1px solid #3A3A3A;
                border-radius: 3px; padding-left: 5px; font-size: 12px;
            }
            QLineEdit:focus { border: 1px solid #606060; }
        """)
        layout.addWidget(line_edit)
        return line_edit

    def test_connection(self):
        tag = self.input_tag.text().strip()
        ip = self.input_ip.text().strip()
        if not ip:
            QMessageBox.warning(self, "Aviso", "Informe o endereço IP para testar a conexão.")
            return
        QMessageBox.information(self, "Teste de Conexão", f"Conexão bem-sucedida com o dispositivo {tag or 'PLC'} ({ip})!")

    def save_plc(self):
        tag = self.input_tag.text().strip()
        ip = self.input_ip.text().strip()
        model = self.combo_model.currentText()

        if not tag or not ip:
            QMessageBox.warning(self, "Aviso", "Preencha a Tag e o Endereço IP do PLC.")
            return

        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        
        item_tag = QTableWidgetItem(tag)
        item_ip = QTableWidgetItem(ip)
        item_model = QTableWidgetItem(model)
        item_status = QTableWidgetItem("Online")

        for item in [item_tag, item_ip, item_model, item_status]:
            item.setTextAlignment(Qt.AlignCenter)

        item_status.setForeground(QColor("#2D5A27"))

        self.table.setItem(row_position, 0, item_tag)
        self.table.setItem(row_position, 1, item_ip)
        self.table.setItem(row_position, 2, item_model)
        self.table.setItem(row_position, 3, item_status)

        self.input_tag.clear()
        self.input_ip.clear()
        self.input_port.clear()
        QMessageBox.information(self, "Sucesso", "PLC cadastrado com sucesso!")