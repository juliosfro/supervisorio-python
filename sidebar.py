from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPen, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QScrollArea
)


class VectorIconGenerator:
    """Gerador de ícones vetoriais no padrão ISA-101."""
    @staticmethod
    def create_icon(icon_type, color="#A0A0A0", size=20):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor(color))
        pen.setWidthF(1.8)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)

        if icon_type == "menu":
            painter.drawLine(2, 6, 18, 6)
            painter.drawLine(2, 10, 18, 10)
            painter.drawLine(2, 14, 18, 14)
        elif icon_type == "home":
            path = QPainterPath()
            path.moveTo(2, 9)
            path.lineTo(10, 2)
            path.lineTo(18, 9)
            path.lineTo(18, 18)
            path.lineTo(2, 18)
            path.closeSubpath()
            painter.drawPath(path)
        elif icon_type == "grid":
            painter.drawRoundedRect(2, 2, 6, 6, 1, 1)
            painter.drawRoundedRect(12, 2, 6, 6, 1, 1)
            painter.drawRoundedRect(2, 12, 6, 6, 1, 1)
            painter.drawRoundedRect(12, 12, 6, 6, 1, 1)
        elif icon_type == "factory":
            path = QPainterPath()
            path.moveTo(2, 18)
            path.lineTo(2, 9)
            path.lineTo(7, 12)
            path.lineTo(7, 9)
            path.lineTo(12, 12)
            path.lineTo(12, 5)
            path.lineTo(18, 9)
            path.lineTo(18, 18)
            path.closeSubpath()
            painter.drawPath(path)
        elif icon_type == "waves":
            for y in [6, 10, 14]:
                path = QPainterPath()
                path.moveTo(2, y)
                path.quadTo(6, y - 2, 10, y)
                path.quadTo(14, y + 2, 18, y)
                painter.drawPath(path)
        elif icon_type == "bell":
            path = QPainterPath()
            path.moveTo(10, 2)
            path.arcTo(5, 4, 10, 10, 0, 180)
            path.lineTo(3, 14)
            path.lineTo(17, 14)
            path.lineTo(15, 13)
            painter.drawPath(path)
            painter.drawArc(8, 15, 4, 3, 0, -180 * 16)
        elif icon_type == "database":
            painter.drawEllipse(3, 2, 14, 4)
            painter.drawArc(3, 7, 14, 4, 0, -180 * 16)
            painter.drawArc(3, 12, 14, 4, 0, -180 * 16)
            painter.drawLine(3, 4, 3, 14)
            painter.drawLine(17, 4, 17, 14)
        elif icon_type == "clock":
            painter.drawEllipse(2, 2, 16, 16)
            painter.drawLine(10, 6, 10, 10)
            painter.drawLine(10, 10, 13, 12)
        elif icon_type == "monitor":
            painter.drawRoundedRect(2, 3, 16, 11, 2, 2)
            painter.drawLine(10, 14, 10, 18)
            painter.drawLine(6, 18, 14, 18)
        elif icon_type == "cards":
            painter.drawRoundedRect(6, 2, 12, 13, 2, 2)
            path = QPainterPath()
            path.moveTo(3, 6)
            path.lineTo(3, 17)
            path.lineTo(14, 17)
            painter.drawPath(path)
        elif icon_type == "network":
            painter.drawEllipse(8, 2, 4, 4)
            painter.drawEllipse(2, 14, 4, 4)
            painter.drawEllipse(14, 14, 4, 4)
            painter.drawLine(10, 6, 10, 10)
            painter.drawLine(4, 10, 16, 10)
            painter.drawLine(4, 10, 4, 14)
            painter.drawLine(16, 10, 16, 14)

        painter.end()
        return QIcon(pixmap)


class SidebarWidget(QWidget):
    """Componente Sidebar em Árvore (Tree Menu) neutro conforme ISA-101."""
    screen_requested = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_expanded = True
        self.collapsed_width = 60
        self.expanded_width = 200

        self.active_category = "Circuitos"
        self.active_subitem = "Cortes"

        self.setFixedWidth(self.expanded_width)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Frame da Barra Lateral
        self.sidebar_frame = QFrame(self)
        self.sidebar_frame.setStyleSheet("QFrame { background-color: #2B2B2B; border: none; }")

        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Cabeçalho do Menu
        self.header_btn = QPushButton("  MENU")
        self.header_btn.setIcon(VectorIconGenerator.create_icon("menu", "#FFFFFF", 18))
        self.header_btn.setIconSize(QSize(18, 18))
        self.header_btn.setFixedHeight(48)
        self.header_btn.setCursor(Qt.PointingHandCursor)
        self.header_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A1A1A; color: #FFFFFF; font-weight: bold;
                font-size: 13px; text-align: left; padding-left: 18px; border: none;
                border-bottom: 1px solid #3A3A3A;
            }
            QPushButton:hover { background-color: #383838; }
        """)
        self.header_btn.clicked.connect(self.toggle_sidebar)
        sidebar_layout.addWidget(self.header_btn)

        # Área de Rolagem do Menu
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: #2B2B2B; width: 6px; margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #444444; min-height: 20px; border-radius: 3px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.menu_layout = QVBoxLayout(scroll_content)
        self.menu_layout.setContentsMargins(0, 0, 0, 0)
        self.menu_layout.setSpacing(0)

        # Estrutura ordenada em ordem alfabética
        self.menu_structure = [
            ("home", "Abatedouro", None, ["Recepção", "Pendura", "Sangria", "Escaldagem"]),
            ("cards", "Alarme Cards", None, ["Visão Geral Cards"]),
            ("bell", "Alarmes", "45", ["Alarmes Ativos", "Histórico de Alarmes", "Configurações"]),
            ("grid", "Circuitos", None, ["Cortes", "Depenagem", "Evisceração", "Expedição", "Gaiolas", "Pendura", "Resfriamento", "Sangria", "Secundária", "TRV"]),
            ("database", "Histórico", None, ["Tendências", "Relatórios"]),
            ("factory", "Industrializados", None, ["Massa", "Embalagem", "Termoformadora"]),
            ("network", "PLCs", None, ["Cadastrar", "Relatório", "Status"]),
            ("clock", "Rastreamento", None, ["Lotes", "Turnos"]),
            ("waves", "Sala Máquinas", None, ["Compressores", "Condensadores", "Bombas"]),
            ("network", "Scanners", None, ["Leitores RFID", "Código de Barras"]),
            ("monitor", "Viewers", "3", ["Telas Clientes", "Sessões Ativas"])
        ]

        self.categories = []

        for icon_key, category_name, badge, subs in self.menu_structure:
            cat_widget = self.create_tree_category(icon_key, category_name, badge, subs)
            self.menu_layout.addWidget(cat_widget)

        self.menu_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        sidebar_layout.addWidget(scroll_area)

        main_layout.addWidget(self.sidebar_frame)

    def create_tree_category(self, icon_key, category_name, badge, sub_items):
        cat_container = QWidget()
        cat_layout = QVBoxLayout(cat_container)
        cat_layout.setContentsMargins(0, 0, 0, 0)
        cat_layout.setSpacing(0)

        btn = QPushButton()
        btn.setFixedHeight(45)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip(category_name)

        is_active = (category_name == self.active_category)

        node = {
            "container": cat_container,
            "button": btn,
            "icon_key": icon_key,
            "name": category_name,
            "badge": badge,
            "subs": sub_items,
            "sub_frame": None,
            "sub_buttons": [],
            "is_expanded": is_active
        }

        self.update_category_button_style(node, is_active)

        btn.clicked.connect(lambda: self.on_category_clicked(node))
        cat_layout.addWidget(btn)

        if sub_items:
            sub_frame = QFrame()
            sub_frame.setStyleSheet("background-color: #222222;")
            sub_layout = QVBoxLayout(sub_frame)
            sub_layout.setContentsMargins(0, 0, 0, 0)
            sub_layout.setSpacing(0)

            for sub_name in sub_items:
                is_sub_active = (is_active and sub_name == self.active_subitem)
                sub_btn = QPushButton(f"  {sub_name}")
                sub_btn.setFixedHeight(32)
                sub_btn.setCursor(Qt.PointingHandCursor)

                self.apply_subitem_style(sub_btn, is_sub_active)

                sub_btn.clicked.connect(lambda _, c=category_name, s=sub_name, sb=sub_btn, n=node: self.on_subitem_clicked(c, s, sb, n))
                sub_layout.addWidget(sub_btn)
                node["sub_buttons"].append((sub_btn, sub_name))

            cat_layout.addWidget(sub_frame)
            node["sub_frame"] = sub_frame
            sub_frame.setVisible(is_active and self.is_expanded)

        self.categories.append(node)
        return cat_container

    def apply_subitem_style(self, button, is_active):
        """Aplica estilo neutro cinza para o subitem, reservando cores saturadas conforme ISA-101."""
        if is_active:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #454545;
                    color: #FFFFFF;
                    font-size: 12px;
                    font-weight: bold;
                    border: none;
                    border-left: 3px solid #808080;
                    padding-left: 33px;
                    text-align: left;
                }
            """)
        else:
            button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #A0A0A0;
                    font-size: 12px;
                    border: none;
                    padding-left: 36px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #333333;
                    color: #FFFFFF;
                }
            """)

    def update_category_button_style(self, node, is_active):
        btn = node["button"]
        icon_key = node["icon_key"]
        text = node["name"]
        badge = node["badge"]
        has_subs = bool(node["subs"])
        is_tree_expanded = node["is_expanded"]

        icon_color = "#FFFFFF" if is_active else "#A0A0A0"
        btn.setIcon(VectorIconGenerator.create_icon(icon_key, icon_color, 18))
        btn.setIconSize(QSize(18, 18))

        if self.is_expanded:
            badge_str = f" ({badge})" if badge else ""
            arrow = " ▾" if (has_subs and is_tree_expanded) else (" ▸" if has_subs else "")
            btn.setText(f"  {text}{badge_str}{arrow}")
        else:
            btn.setText("")

        bg_color = "#3A3A3A" if is_active else "transparent"
        text_color = "#FFFFFF" if is_active else "#B0B0B0"

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color}; color: {text_color};
                font-size: 13px; text-align: left; padding-left: 18px; border: none;
            }}
            QPushButton:hover {{ background-color: #383838; color: #FFFFFF; }}
        """)

    def on_category_clicked(self, node):
        if not self.is_expanded:
            self.toggle_sidebar()

        self.active_category = node["name"]
        node["is_expanded"] = not node["is_expanded"]

        if node["sub_frame"]:
            node["sub_frame"].setVisible(node["is_expanded"])

        for cat in self.categories:
            is_act = (cat["name"] == self.active_category)
            if not is_act and cat["sub_frame"]:
                cat["is_expanded"] = False
                cat["sub_frame"].setVisible(False)
            self.update_category_button_style(cat, is_act)

        if not node["subs"]:
            self.screen_requested.emit(node["name"], "")

    def on_subitem_clicked(self, category, sub_name, clicked_btn, parent_node):
        self.active_category = category
        self.active_subitem = sub_name

        for cat in self.categories:
            for s_btn, s_name in cat["sub_buttons"]:
                is_curr = (s_btn == clicked_btn)
                self.apply_subitem_style(s_btn, is_curr)

        self.screen_requested.emit(category, sub_name)

    def toggle_sidebar(self):
        start_width = self.width()
        end_width = self.collapsed_width if self.is_expanded else self.expanded_width

        self.anim = QPropertyAnimation(self, b"minimumWidth")
        self.anim.setDuration(200)
        self.anim.setStartValue(start_width)
        self.anim.setEndValue(end_width)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)

        self.anim_max = QPropertyAnimation(self, b"maximumWidth")
        self.anim_max.setDuration(200)
        self.anim_max.setStartValue(start_width)
        self.anim_max.setEndValue(end_width)
        self.anim_max.setEasingCurve(QEasingCurve.InOutQuad)

        self.anim.start()
        self.anim_max.start()
        self.is_expanded = not self.is_expanded

        for cat in self.categories:
            if cat["sub_frame"]:
                cat["sub_frame"].setVisible(self.is_expanded and cat["is_expanded"])
            self.update_category_button_style(cat, cat["name"] == self.active_category)

        self.header_btn.setText("  MENU" if self.is_expanded else "")