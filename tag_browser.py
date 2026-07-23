import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeView, QPushButton, QLineEdit, QLabel, QMessageBox,
    QHeaderView, QStyle, QMenu, QAction
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
from pycomm3 import LogixDriver


class ControlLogixBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.plc = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("ControlLogix Tag Browser")
        self.setGeometry(100, 100, 950, 650)

        style = QApplication.style()
        self.icon_folder = style.standardIcon(QStyle.SP_DirIcon)            # Pasta Amarela
        self.icon_file = style.standardIcon(QStyle.SP_FileIcon)              # Tag Simples
        self.icon_drive = style.standardIcon(QStyle.SP_DriveHDIcon)          # Controlador / Programas

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Painel Superior: Conexão ---
        conn_layout = QHBoxLayout()
        conn_layout.addWidget(QLabel("IP do CLP:"))
        
        self.ip_input = QLineEdit("172.16.40.3")
        conn_layout.addWidget(self.ip_input)

        self.btn_connect = QPushButton("Conectar e Ler Tags")
        self.btn_connect.clicked.connect(self.connect_plc)
        conn_layout.addWidget(self.btn_connect)

        main_layout.addLayout(conn_layout)

        # --- Painel de Filtro ---
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Buscar Tag:"))
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Digite para filtrar...")
        self.filter_input.textChanged.connect(self.filter_tree)
        filter_layout.addWidget(self.filter_input)

        main_layout.addLayout(filter_layout)

        # --- Árvore de Tags (QTreeView) ---
        self.tree_view = QTreeView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Nome da Tag / Membro", "Tipo de Dado"])
        self.tree_view.setModel(self.model)
        
        self.tree_view.setItemsExpandable(True)
        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(20)

        self.tree_view.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree_view.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
        self.tree_view.expanded.connect(self.on_item_expanded)
        self.tree_view.doubleClicked.connect(self.copy_tag_to_clipboard)
        
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        
        main_layout.addWidget(self.tree_view)

        # --- Barra de Status Inferior ---
        self.status_label = QLabel("Status: Desconectado. Dica: Clique com botão direito ou clique duplo na tag para copiar.")
        main_layout.addWidget(self.status_label)

    def connect_plc(self):
        ip = self.ip_input.text().strip()
        if not ip:
            QMessageBox.warning(self, "Aviso", "Por favor, insira um IP válido.")
            return

        self.status_label.setText(f"Conectando a {ip} e mapeando tags... Aguarde.")
        QApplication.processEvents()

        try:
            if self.plc and self.plc.connected:
                self.plc.close()

            self.plc = LogixDriver(ip, init_tags=True, init_program_tags=True)
            self.plc.open()

            if self.plc.connected:
                self.status_label.setText(f"Conectado ao CLP ({self.plc.info.get('product_name', 'ControlLogix')})")
                self.populate_root_tags()
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível conectar ao CLP.")
                self.status_label.setText("Status: Erro na conexão.")
        except Exception as e:
            QMessageBox.critical(self, "Erro de Conexão", str(e))
            self.status_label.setText("Status: Erro na conexão.")

    def populate_root_tags(self):
        self.model.removeRows(0, self.model.rowCount())

        root_controller = QStandardItem(self.icon_drive, "Controller Tags")
        root_programs = QStandardItem(self.icon_folder, "Program Tags")
        
        self.model.appendRow([root_controller, QStandardItem("")])
        self.model.appendRow([root_programs, QStandardItem("")])

        programs_dict = {}
        tags_dict = self.plc.tags
        
        for tag_name, tag_info in tags_dict.items():
            dt = tag_info.get('data_type', 'UNK')
            prog_name = tag_info.get('program_name')
            
            if prog_name:
                if prog_name not in programs_dict:
                    prog_item = QStandardItem(self.icon_folder, f"Program:{prog_name}")
                    root_programs.appendRow([prog_item, QStandardItem("")])
                    programs_dict[prog_name] = prog_item
                parent_node = programs_dict[prog_name]
            else:
                parent_node = root_controller

            has_sub_items = self._has_children(tag_info)
            item_icon = self.icon_folder if has_sub_items else self.icon_file

            item_name = QStandardItem(item_icon, tag_name)
            item_type = QStandardItem(str(dt))
            
            item_name.setData(tag_info, Qt.UserRole)

            if has_sub_items:
                item_name.appendRow([QStandardItem("Carregando..."), QStandardItem("")])

            parent_node.appendRow([item_name, item_type])

        self.tree_view.expand(root_controller.index())

    def _has_children(self, tag_info):
        """Verifica de forma robusta se a tag ou membro possui subelementos (Array ou UDT)."""
        if not isinstance(tag_info, dict):
            return False
        
        # Verifica se é um array com dimensões
        array_len = tag_info.get('array', 0) or tag_info.get('dim', 0)
        if array_len > 0:
            return True

        # Obtém o nome ou a estrutura do tipo de dado
        dt_name = tag_info.get('data_type_name') or tag_info.get('data_type')
        
        # Se o tipo de dado for um dicionário (comum em estruturas internas do pycomm3)
        if isinstance(dt_name, dict):
            if dt_name.get('internal_tags') or dt_name.get('attributes') or dt_name.get('fields'):
                return True
            dt_name = dt_name.get('name')

        # Se o nome do tipo de dado existe no dicionário de UDTs/estruturas globais do CLP
        if self.plc and self.plc.data_types:
            if isinstance(dt_name, str) and dt_name in self.plc.data_types:
                return True
                
        if tag_info.get('data_type_class') in ['struct', 'udt']:
            return True
            
        return False

    def on_item_expanded(self, index):
        item = self.model.itemFromIndex(index)
        if not item or item.rowCount() == 0:
            return

        first_child = item.child(0, 0)
        if first_child and first_child.text() == "Carregando...":
            item.removeRow(0)
            tag_info = item.data(Qt.UserRole)
            if tag_info:
                self._load_children(item, tag_info)

    def _load_children(self, parent_item, tag_info):
        dt_name = tag_info.get('data_type_name') or tag_info.get('data_type')
        array_len = tag_info.get('array', 0) or tag_info.get('dim', 0)

        # 1. Expandir ARRAYS
        if array_len > 0:
            base_dt = tag_info.get('data_type_name') or tag_info.get('data_type')
            limit = min(array_len, 200)
            for i in range(limit):
                # Repassa a estrutura base para o elemento do array preservar o UDT/tipo complexo
                child_info = {
                    'data_type': base_dt, 
                    'data_type_name': base_dt, 
                    'array': 0,
                    'dim': 0
                }
                has_sub = self._has_children(child_info)
                icon = self.icon_folder if has_sub else self.icon_file

                child_name = QStandardItem(icon, f"[{i}]")
                
                # Trata exibição limpa do tipo de dado na coluna 2
                display_dt = base_dt.get('name', str(base_dt)) if isinstance(base_dt, dict) else str(base_dt)
                child_type = QStandardItem(display_dt)
                
                child_name.setData(child_info, Qt.UserRole)

                if has_sub:
                    child_name.appendRow([QStandardItem("Carregando..."), QStandardItem("")])

                parent_item.appendRow([child_name, child_type])
            return

        # Extrai o nome real da UDT caso venha em formato de dicionário
        if isinstance(dt_name, dict):
            # Se o próprio dicionário já trouxer os atributos internos (como o POWER_FLEX_525 na imagem)
            internal = dt_name.get('internal_tags') or dt_name.get('attributes') or dt_name.get('fields')
            if internal:
                udt_def = dt_name
            else:
                real_name = dt_name.get('name')
                udt_def = self.plc.data_types.get(real_name, {}) if self.plc else {}
        else:
            udt_def = self.plc.data_types.get(dt_name, {}) if self.plc else {}

        members = udt_def.get('internal_tags') or udt_def.get('attributes') or udt_def.get('fields') or {}

        items_iterator = members.items() if isinstance(members, dict) else enumerate(members)

        for key, m_info in items_iterator:
            if isinstance(m_info, dict):
                m_name = m_info.get('name') or key
                m_type = m_info.get('data_type_name') or m_info.get('data_type', 'UNK')
            else:
                m_name = str(key)
                m_type = str(m_info)
                m_info = {'data_type': m_type, 'data_type_name': m_type}

            if isinstance(m_info, dict) and 'data_type_name' not in m_info:
                m_info['data_type_name'] = m_type

            has_sub = self._has_children(m_info)
            icon = self.icon_folder if has_sub else self.icon_file

            child_name = QStandardItem(icon, str(m_name))
            
            display_m_type = m_type.get('name', str(m_type)) if isinstance(m_type, dict) else str(m_type)
            child_type = QStandardItem(display_m_type)
            
            child_name.setData(m_info, Qt.UserRole)

            if has_sub:
                child_name.appendRow([QStandardItem("Carregando..."), QStandardItem("")])

            parent_item.appendRow([child_name, child_type])

    def show_context_menu(self, position):
        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu(self)
        copy_action = QAction("Copy Path", self)
        copy_action.triggered.connect(lambda: self.copy_tag_to_clipboard(index))
        menu.addAction(copy_action)

        menu.exec_(self.tree_view.viewport().mapToGlobal(position))

    def copy_tag_to_clipboard(self, index):
        first_col_index = index.sibling(index.row(), 0)
        item = self.model.itemFromIndex(first_col_index)
        
        if not item or not item.text() or item.text() == "Carregando...":
            return

        path_parts = []
        current = item
        
        while current is not None:
            text = current.text()
            if text not in ["Controller Tags", "Program Tags"]:
                path_parts.insert(0, text)
            current = current.parent()

        if not path_parts:
            return

        full_tag_path = ""
        for i, part in enumerate(path_parts):
            if i == 0:
                full_tag_path = part
            elif part.startswith("["):
                full_tag_path += part
            else:
                full_tag_path += f".{part}"

        clipboard = QApplication.clipboard()
        clipboard.setText(full_tag_path)
        self.status_label.setText(f"Copiado para a área de transferência: '{full_tag_path}'")

    def filter_tree(self):
        filter_text = self.filter_input.text().lower()
        
        def filter_item(item):
            match = False
            for row in range(item.rowCount()):
                child = item.child(row, 0)
                if child:
                    child_match = filter_item(child)
                    text_match = filter_text in child.text().lower()
                    
                    visible = text_match or child_match
                    self.tree_view.setRowHidden(row, item.index(), not visible)
                    if visible:
                        match = True
            return match

        for root_row in range(self.model.rowCount()):
            root_item = self.model.item(root_row, 0)
            if root_item:
                filter_item(root_item)

    def closeEvent(self, event):
        if self.plc and self.plc.connected:
            self.plc.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ControlLogixBrowser()
    window.show()
    sys.exit(app.exec_())