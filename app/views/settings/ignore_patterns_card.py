from typing import List, Optional
from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from app.config.theme import ACCENT, ACCENT_HOVER, ACCENT_LIGHT, ACCENT_MUTED, BORDER, BORDER_DASHED, FONT_UI, TEXT_MAIN, TEXT_MUTED
from app.core.fonts import FONT_UI_FAMILY, make_font
from app.core.icons import render_pixmap
from app.core.ignore_manager import get_ignore_manager
from app.widgets.tag_chip import TagChip
from app.widgets.toggle_switch import ToggleSwitch

class FlowLayout(QLayout):
    """
    Standard Qt FlowLayout that automatically wraps child widgets
    based on available container width, fitting tags dynamically.
    """
    def __init__(self, parent=None, margin=0, h_spacing=6, v_spacing=6):
        super().__init__(parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self._item_list = []

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), apply_geometry=False)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, apply_geometry=True)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect, apply_geometry):
        margins = self.contentsMargins()
        effective_rect = rect.adjusted(+margins.left(), +margins.top(), -margins.right(), -margins.bottom())
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0

        for item in self._item_list:
            w = item.sizeHint().width()
            h = item.sizeHint().height()
            space_x = self._h_spacing
            space_y = self._v_spacing

            next_x = x + w + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + w + space_x
                line_height = 0

            if apply_geometry:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, h)

        return y + line_height - rect.y() + margins.bottom()


class IgnorePatternsCard(QFrame):
    """
    Card 1: Persistent Ignore Patterns management card with toggle, search/add bar,
    smart hint feedback ("No match — press Enter to add..."), newest tags on top,
    and automatic persistence in User_Data/RP_Ignore_pattern.json.
    """
    patterns_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("IgnoreCard")
        self.setStyleSheet(f"""
            QFrame#IgnoreCard {{
                background-color: #ffffff;
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)

        self.ignore_manager = get_ignore_manager()
        self.is_enabled = self.ignore_manager.is_enabled

        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(14, 14, 14, 14)
        root_lay.setSpacing(8)

        # 1. Header: Title + Toggle Switch
        h_row = QHBoxLayout()
        h_row.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel("Ignore Patterns")
        title_lbl.setFont(make_font(FONT_UI_FAMILY, 13, QFont.Weight.DemiBold))
        title_lbl.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 13px; font-weight: 600; background: transparent; border: none;")
        h_row.addWidget(title_lbl)
        h_row.addStretch(1)

        self.toggle = ToggleSwitch(checked=self.is_enabled, parent=self)
        self.toggle.toggled.connect(self._on_toggle)
        h_row.addWidget(self.toggle)
        root_lay.addLayout(h_row)

        # 2. Subtitle Description
        sub_lbl = QLabel("Files & folders matching these patterns\nwon't be scanned or exported.")
        sub_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-weight: 400; line-height: 1.3; background: transparent; border: none;")
        root_lay.addWidget(sub_lbl)

        # 3. Stats & Reset Row
        stats_row = QHBoxLayout()
        stats_row.setContentsMargins(0, 2, 0, 2)

        self.count_lbl = QLabel()
        self.count_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; background: transparent; border: none;")
        self._update_count_label()
        stats_row.addWidget(self.count_lbl)
        stats_row.addStretch(1)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #1d4ed8;
                font-size: 12px;
                font-weight: 600;
                border: none;
                padding: 0;
            }
            QPushButton:hover {
                color: #2563eb;
                text-decoration: underline;
            }
            QPushButton:pressed {
                color: #1e40af;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_defaults)
        stats_row.addWidget(self.reset_btn)
        root_lay.addLayout(stats_row)

        # 4. Search & Input Box
        search_box = QFrame()
        search_box.setStyleSheet(f"""
            QFrame {{
                background-color: #f8fafc;
                border: 1px solid {BORDER_DASHED};
                border-radius: 8px;
            }}
            QFrame:focus-within {{
                background-color: #ffffff;
                border: 1px solid {ACCENT};
            }}
        """)
        search_box.setFixedHeight(34)
        sb_lay = QHBoxLayout(search_box)
        sb_lay.setContentsMargins(8, 0, 8, 0)
        sb_lay.setSpacing(6)

        search_icon_lbl = QLabel()
        search_icon_lbl.setStyleSheet("background: transparent; border: none;")
        search_pm = render_pixmap("search", (14, 14), color=TEXT_MUTED)
        if search_pm:
            search_icon_lbl.setPixmap(search_pm)
        sb_lay.addWidget(search_icon_lbl)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search or type a new pattern...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {TEXT_MAIN};
                font-size: 12px;
                font-family: {FONT_UI};
            }}
        """)
        self.search_input.returnPressed.connect(self._on_add_pattern)
        self.search_input.textChanged.connect(self._on_search_filter)
        sb_lay.addWidget(self.search_input, 1)

        root_lay.addWidget(search_box)

        # Dynamic 'No match — press Enter to add "<query>"' Hint Label
        self.hint_lbl = QLabel(self)
        self.hint_lbl.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 11px;
                background: transparent;
                border: none;
                padding-left: 4px;
                padding-top: 1px;
                padding-bottom: 2px;
            }
        """)
        self.hint_lbl.hide()
        root_lay.addWidget(self.hint_lbl)

        # 5. Tag Flow Scroll Area with Slim Scrollbar and Top Alignment
        self.scroll_area = QScrollArea()
        self.scroll_area.setFixedHeight(140)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 4px;
                margin: 0px 1px 0px 0px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                min-height: 20px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        
        self.content_vbox = QVBoxLayout(self.scroll_content)
        self.content_vbox.setContentsMargins(0, 4, 4, 4)
        self.content_vbox.setSpacing(0)
        self.content_vbox.setAlignment(Qt.AlignTop)

        self.flow_container = QWidget()
        self.flow_container.setStyleSheet("background: transparent;")
        self.flow_layout = FlowLayout(self.flow_container, margin=0, h_spacing=6, v_spacing=6)
        self.content_vbox.addWidget(self.flow_container)

        self.scroll_area.setWidget(self.scroll_content)
        root_lay.addWidget(self.scroll_area)

        self._render_tags()

    def _update_count_label(self):
        patterns = self.ignore_manager.get_persistent_patterns()
        count = len(patterns)
        self.count_lbl.setText(f'<b style="color: {TEXT_MAIN};">{count}</b> patterns configured')

    def _render_tags(self, filter_text: str = "") -> int:
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            if item.widget():
                w = item.widget()
                w.hide()
                w.setParent(None)
                w.deleteLater()

        all_patterns = self.ignore_manager.get_persistent_patterns()
        filter_lower = filter_text.strip().lower()
        if filter_lower:
            display_tags = [t for t in all_patterns if filter_lower in t.lower()]
        else:
            display_tags = all_patterns

        for tag in display_tags:
            chip = TagChip(tag, parent=self.flow_container)
            chip.removed.connect(self._remove_pattern)
            self.flow_layout.addWidget(chip)
            chip.show()

        self.flow_container.adjustSize()
        self.scroll_content.adjustSize()
        return len(display_tags)

    def _on_search_filter(self, text: str):
        query = text.strip()
        match_count = self._render_tags(query)
        if query and match_count == 0:
            # Show matching hint from design: No match — press Enter to add "query"
            self.hint_lbl.setText(f"<span style='color: #64748b; font-style: italic;'>No match — press </span><b style='color: #0f172a;'>Enter</b><span style='color: #64748b; font-style: italic;'> to add \"{query}\"</span>")
            self.hint_lbl.show()
        else:
            self.hint_lbl.hide()

    def _on_add_pattern(self):
        new_tag = self.search_input.text().strip()
        if new_tag:
            self.ignore_manager.add_pattern(new_tag)
            self.search_input.clear()
            self.hint_lbl.hide()
            self._update_count_label()
            self._render_tags()
            # Scroll to top so user sees newly added tag immediately
            self.scroll_area.verticalScrollBar().setValue(0)
            self.patterns_changed.emit(self.ignore_manager.get_all_patterns())

    def _remove_pattern(self, tag: str):
        if self.ignore_manager.remove_pattern(tag):
            self._update_count_label()
            self._render_tags(self.search_input.text())
            self.patterns_changed.emit(self.ignore_manager.get_all_patterns())

    def reset_defaults(self):
        self.ignore_manager.reset_defaults()
        self.search_input.clear()
        self.hint_lbl.hide()
        self._update_count_label()
        self._render_tags()
        self.patterns_changed.emit(self.ignore_manager.get_all_patterns())

    def reset_search(self):
        """Clean and reset search input when leaving settings view."""
        self.search_input.clear()
        self.hint_lbl.hide()
        self._render_tags("")

    def refresh_patterns(self):
        """Reload and re-render tags from ignore_manager."""
        self._update_count_label()
        self._render_tags(self.search_input.text())

    def _on_toggle(self, checked: bool):
        self.is_enabled = checked
        self.ignore_manager.set_enabled(checked)
        self.scroll_area.setEnabled(checked)
        self.search_input.setEnabled(checked)
        self.reset_btn.setEnabled(checked)
        self.scroll_area.setStyleSheet(f"opacity: {'1.0' if checked else '0.4'};")
        self.patterns_changed.emit(self.ignore_manager.get_all_patterns())


