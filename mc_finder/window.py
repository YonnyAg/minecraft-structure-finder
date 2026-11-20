"""Interfaz de búsqueda y resultados de estructuras."""

import json
import math

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFormLayout, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow, QPlainTextEdit,
    QPushButton, QScrollArea, QSizePolicy, QSpinBox, QSplitter, QTableWidget, QTabWidget,
    QVBoxLayout, QWidget, QTableWidgetItem, QProgressBar,
)

from .domain import Dimension, SearchMode, SearchRequest, StructureGroup, STRUCTURES
from .services import SearchService
from .engine import HUT, MAX_RADIUS
from .worker import SearchWorker
from .groups import MAX_GROUP_RADIUS
from .perimeter_panel import PerimeterPanel


STYLE = """
QMainWindow, QWidget#root { background: #111113; color: #ededf1; }
QWidget { font-family: 'Segoe UI'; font-size: 13px; color: #ededf1; }
QFrame#panel { background: #1b1b20; border: 1px solid #303037; border-radius: 8px; }
QWidget#paper { background: #1b1b20; }
QFrame#masthead { background: #111113; border-bottom: 1px solid #303037; }
QLabel#title { font-size: 25px; font-weight: 700; color: #fafaff; }
QLabel#eyebrow { font-size: 11px; font-weight: 600; color: #aaa1c5; letter-spacing: 2px; }
QLabel#section { font-size: 16px; font-weight: 600; color: #f5f4fa; }
QLabel#muted { color: #aaa8b7; }
QLabel#badge { color: #cbb9ff; background: #292332; border: 1px solid #493a61; padding: 8px 14px; border-radius: 12px; }
QLabel#notice { color: #b8a8dc; padding: 4px 0; }
QLabel#step { color: #b59ae9; font-size: 11px; font-weight: 600; letter-spacing: 1px; }
QLabel#empty { color: #bbb5cd; background: #24212e; padding: 16px; border: 1px solid #393144; border-radius: 6px; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit {
    background: #141417; border: 1px solid #40404a; border-radius: 5px; padding: 7px;
    selection-background-color: #7656b5; selection-color: #ffffff;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border: 1px solid #b399ee; }
QLineEdit:read-only { background: #222228; color: #aaa8b7; }
QSpinBox QLineEdit, QDoubleSpinBox QLineEdit { background: transparent; border: none; padding: 0; }
QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { width: 0; height: 0; border: none; }
QSpinBox::up-arrow, QSpinBox::down-arrow, QDoubleSpinBox::up-arrow, QDoubleSpinBox::down-arrow { image: none; width: 0; height: 0; }
QComboBox QAbstractItemView { background: #25252c; color: #ededf1; selection-background-color: #66508d; selection-color: #ffffff; border: 1px solid #484052; }
QPushButton { background: #25252c; border: 1px solid #42424c; border-radius: 6px; padding: 10px 18px; }
QPushButton:hover { background: #323039; border-color: #847397; }
QPushButton#primary { background: #b99cf5; color: #20152f; border: 1px solid #b99cf5; font-weight: 700; }
QPushButton#primary:hover { background: #cbb3ff; }
QPushButton:disabled { background: #202026; color: #777480; border-color: #303037; }
QTableWidget { background: #17171b; alternate-background-color: #1d1d23; border: 1px solid #303037; gridline-color: #303037; selection-background-color: #45365e; }
QTableWidget QTableCornerButton::section { background: #26262e; border: none; }
QHeaderView::section { background: #26262e; color: #b9b6c7; padding: 12px 8px; border: none; border-bottom: 1px solid #3b3745; }
QPlainTextEdit { font-family: 'Consolas'; font-size: 12px; }
QTabWidget::pane { background: #1b1b20; border: 1px solid #303037; border-radius: 6px; }
QTabBar::tab { background: #111113; color: #9691a2; padding: 10px 18px; margin: 0 6px 8px 0; border-radius: 5px; }
QTabBar::tab:selected { background: #332a45; color: #dbcbff; }
QTabBar::tab:hover { color: #e5d6ff; background: #26222f; }
QStatusBar { background: #111113; color: #9691a2; }
QSplitter::handle { background: #111113; }
QScrollArea { background: transparent; border: none; }
QScrollBar:vertical { background: #1b1b20; width: 8px; margin: 0; }
QScrollBar::handle:vertical { background: #49434f; min-height: 28px; border-radius: 4px; }
QScrollBar::handle:vertical:hover { background: #79678f; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
QScrollBar:horizontal { background: #1b1b20; height: 8px; margin: 0; }
QScrollBar::handle:horizontal { background: #49434f; min-width: 28px; border-radius: 4px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }
QToolTip { background: #2c2638; color: #eee6ff; border: 1px solid #706080; padding: 6px; }
QProgressBar { background: #141417; border: 1px solid #40364e; border-radius: 4px; text-align: center; min-height: 18px; }
QProgressBar::chunk { background: #68508d; border-radius: 3px; }
"""


def heading(text: str, name: str = "section") -> QLabel:
    label = QLabel(text)
    label.setObjectName(name)
    return label


def panel() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("panel")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(14)
    return frame, layout


def number(value: int, low: int, high: int) -> QSpinBox:
    field = QSpinBox()
    # Qt 6.12 + styled NoButtons collapses the editor to one pixel.
    # Hide the button subcontrols in STYLE instead, preserving a usable editor.
    field.lineEdit().setTextMargins(8, 0, 8, 0)
    field.setRange(low, high)
    field.setValue(value)
    field.setGroupSeparatorShown(True)
    return field


class MainWindow(QMainWindow):
    def __init__(self, service: SearchService | None = None):
        super().__init__()
        self.service = service if service is not None else SearchService()
        self.prepared_request: SearchRequest | None = None
        self.worker: SearchWorker | None = None
        self.active_request: SearchRequest | None = None
        self.group_results: list[StructureGroup] = []
        self.closing_after_search = False
        self.setWindowTitle("Minecraft Structure Finder · Java 26.3")
        self.resize(1200, 820)
        self.setMinimumSize(1000, 680)
        self.setStyleSheet(STYLE)
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(16)

        masthead = QFrame()
        masthead.setObjectName("masthead")
        top = QHBoxLayout(masthead)
        top.setContentsMargins(0, 10, 0, 18)
        titles = QVBoxLayout()
        titles.addWidget(heading("MINECRAFT  /  EXPLORADOR", "eyebrow"))
        titles.addWidget(heading("Structure Finder", "title"))
        top.addLayout(titles)
        top.addStretch()
        top.addWidget(heading("Java 26.3", "badge"))
        layout.addWidget(masthead)

        world, world_layout = panel()
        world_layout.setContentsMargins(18, 12, 18, 14)
        world_layout.setSpacing(8)
        world_row = QHBoxLayout()
        world_row.setSpacing(18)
        world_layout.addLayout(world_row)
        layout.addWidget(world)
        self.world_panel = world

        split = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(split, 1)
        config, fields = panel()
        self.config_panel = config
        config.setMinimumWidth(330)
        config_scroll = QScrollArea()
        config_scroll.setWidgetResizable(True)
        config_scroll.setMinimumWidth(350)
        config_scroll.setWidget(config)
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(10)
        sidebar_layout.addWidget(config_scroll, 1)
        split.addWidget(sidebar)
        fields.setSpacing(10)
        fields.addWidget(heading("BÚSQUEDA", "step"))
        fields.addWidget(heading("Filtros de exploración"))
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setSpacing(6)
        self.seed = QLineEdit()
        self.seed.setPlaceholderText("Ej.: 5067257298883736067")
        self.seed.setMaxLength(32)
        self.seed.setToolTip("Seed numérica con signo de 64 bits. Se conserva como entero, sin decimales.")
        seed_column = QVBoxLayout()
        seed_column.addWidget(QLabel("Seed del mundo"))
        seed_column.addWidget(self.seed)
        world_row.addLayout(seed_column, 3)
        version = QLineEdit("Java 26.3")
        version.setReadOnly(True)
        version_column = QVBoxLayout()
        version_column.addWidget(QLabel("Versión objetivo"))
        version_column.addWidget(version)
        world_row.addLayout(version_column, 1)
        self.dimension = QComboBox()
        for label, value in (("Overworld", Dimension.OVERWORLD), ("Nether", Dimension.NETHER), ("End", Dimension.END)):
            self.dimension.addItem(label, value)
        for index in (1, 2):
            item = self.dimension.model().item(index)
            item.setEnabled(False)
            item.setToolTip("Disponible en una próxima etapa.")
        dimension_column = QVBoxLayout()
        dimension_column.addWidget(QLabel("Dimensión"))
        dimension_column.addWidget(self.dimension)
        world_row.addLayout(dimension_column, 1)
        self.structure = QComboBox()
        form.addRow("Estructura", self.structure)
        self.mode = QComboBox()
        for label, value in (("Estructura más cercana", SearchMode.NEAREST), ("Todas dentro del área", SearchMode.AREA), ("Agrupación de estructuras", SearchMode.GROUP)):
            self.mode.addItem(label, value)
        self.mode.model().item(2).setToolTip("Cabañas que caben en un círculo común; no valida un punto AFK.")
        form.addRow("Tipo de búsqueda", self.mode)
        self.origin_x = number(0, -30_000_000, 30_000_000)
        self.origin_z = number(0, -30_000_000, 30_000_000)
        origin_row = QHBoxLayout()
        origin_row.addWidget(QLabel("X"))
        origin_row.addWidget(self.origin_x)
        origin_row.addWidget(QLabel("Z"))
        origin_row.addWidget(self.origin_z)
        form.addRow("Punto de referencia", origin_row)
        self.search_radius = number(10_000, 1, MAX_RADIUS)
        self.search_radius.setToolTip("Límite de esta primera etapa: 50.000 bloques.")
        self.search_radius.setSuffix(" bloques")
        form.addRow("Radio de exploración", self.search_radius)
        fields.addLayout(form)
        self.group_frame = QFrame()
        group_form = QFormLayout(self.group_frame)
        group_form.setContentsMargins(0, 0, 0, 0)
        group_form.setSpacing(6)
        group_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.minimum_count = number(4, 2, 100)
        self.group_radius = number(200, 1, MAX_GROUP_RADIUS)
        self.group_radius.setToolTip("Radio del círculo común en X/Z. No garantiza activación simultánea de granjas.")
        self.group_radius.setSuffix(" bloques")
        group_form.addRow("Cantidad mínima", self.minimum_count)
        group_form.addRow("Radio del grupo", self.group_radius)
        fields.addWidget(self.group_frame)
        help_text = heading(
            "Exploración: área alrededor del origen.\nGrupo: círculo común que debe contener las estructuras.\nDistancias horizontales X/Z en la dimensión elegida.", "muted"
        )
        help_text.setWordWrap(True)
        fields.addWidget(help_text)
        fields.addStretch()
        self.feedback = QLabel("Introduce una seed para buscar cabañas de brujas.")
        self.feedback.setWordWrap(True)
        # Las acciones quedan en un pie fijo, fuera del formulario desplazable.
        self.prepare_button = QPushButton("Buscar estructuras")
        self.prepare_button.setObjectName("primary")
        self.prepare_button.clicked.connect(self.start_search)
        self.example_button = QPushButton("Cargar ejemplo")
        self.example_button.clicked.connect(self.load_example)

        results_tabs = QTabWidget()
        self.results_tabs = results_tabs
        results_tabs.setMinimumWidth(490)
        split.addWidget(results_tabs)
        results = QWidget()
        results.setObjectName("paper")
        output = QVBoxLayout(results)
        output.setContentsMargins(20, 20, 20, 20)
        output.setSpacing(16)
        results_scroll = QScrollArea()
        results_scroll.setWidgetResizable(True)
        results_scroll.setWidget(results)
        results_tabs.addTab(results_scroll, "Ubicaciones")
        split.setSizes([350, 800])
        output.addWidget(heading("RESULTADOS", "step"))
        output.addWidget(heading("Ubicaciones de estructuras"))
        self.result_hint = heading("Primera etapa: cabañas de brujas del Overworld.\nBusca la más cercana o todas dentro del radio indicado.", "empty")
        self.result_hint.setWordWrap(True)
        output.addWidget(self.result_hint)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Estructura", "X", "Z", "Distancia", "Estado"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setMinimumHeight(140)
        output.addWidget(self.table, 1)
        self.copy_coordinates_button = QPushButton("Copiar X / Z seleccionadas")
        self.copy_coordinates_button.setEnabled(False)
        self.copy_coordinates_button.clicked.connect(self.copy_coordinates)
        self.table.itemSelectionChanged.connect(self.update_location_actions)
        location_actions = QHBoxLayout()
        location_actions.addWidget(self.copy_coordinates_button)
        self.location_perimeter_button = QPushButton("Ver perímetro")
        self.location_perimeter_button.setEnabled(False)
        self.location_perimeter_button.clicked.connect(self.use_location_perimeter)
        location_actions.addWidget(self.location_perimeter_button)
        output.addLayout(location_actions)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        notice = heading("Predicciones por seed y bioma · Mundo estándar Java 26.3 · Comprueba las ubicaciones en el juego.", "notice")
        notice.setWordWrap(True)
        output.addWidget(notice)
        query_page = QWidget()
        query_page.setObjectName("paper")
        query_output = QVBoxLayout(query_page)
        query_output.setContentsMargins(20, 20, 20, 20)
        query_output.setSpacing(16)
        results_tabs.addTab(query_page, "Parámetros JSON")
        query_output.addWidget(heading("Consulta preparada"))
        query_help = heading("Parámetros de la consulta actual.", "muted")
        query_help.setWordWrap(True)
        query_output.addWidget(query_help)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Los parámetros aparecerán al iniciar una búsqueda.")
        self.preview.setMinimumHeight(150)
        self.preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        query_output.addWidget(self.preview, 1)
        self.copy_button = QPushButton("Copiar consulta JSON")
        self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(self.copy_query)
        query_output.addWidget(self.copy_button)

        group_page = QWidget()
        group_page.setObjectName("paper")
        group_output = QVBoxLayout(group_page)
        group_output.setContentsMargins(20, 20, 20, 20)
        group_output.setSpacing(14)
        group_output.addWidget(heading("AGRUPACIONES", "step"))
        self.groups_hint = heading("Configura cantidad mínima y radio para buscar grupos.", "empty")
        self.groups_hint.setWordWrap(True)
        group_output.addWidget(self.groups_hint)
        self.group_table = QTableWidget(0, 6)
        self.group_table.setHorizontalHeaderLabels(["Grupo", "Cabañas", "Centro X", "Centro Z", "Radio", "Distancia"])
        self.group_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.group_table.verticalHeader().hide()
        self.group_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.group_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.group_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.group_table.setAlternatingRowColors(True)
        self.group_table.setMinimumHeight(140)
        self.group_table.itemSelectionChanged.connect(self.select_group)
        group_output.addWidget(self.group_table, 1)
        group_note = heading(
            "Centro geométrico X/Z, no punto AFK validado. Se usan referencias de generación; faltan altura y zonas de aparición.\n"
            "Todas las cabañas del grupo deben estar dentro del radio de exploración.", "notice"
        )
        group_note.setWordWrap(True)
        group_output.addWidget(group_note)
        group_actions = QHBoxLayout()
        self.view_group_button = QPushButton("Ver cabañas del grupo")
        self.view_group_button.setEnabled(False)
        self.view_group_button.clicked.connect(lambda: self.results_tabs.setCurrentIndex(0))
        self.copy_group_button = QPushButton("Copiar centro y cabañas")
        self.copy_group_button.setEnabled(False)
        self.copy_group_button.clicked.connect(self.copy_group)
        group_actions.addWidget(self.view_group_button)
        group_actions.addWidget(self.copy_group_button)
        group_output.addLayout(group_actions)
        self.group_perimeter_button = QPushButton("Perímetro de este grupo")
        self.group_perimeter_button.setEnabled(False)
        self.group_perimeter_button.clicked.connect(self.use_group_perimeter)
        group_output.addWidget(self.group_perimeter_button)
        group_scroll = QScrollArea()
        group_scroll.setWidgetResizable(True)
        group_scroll.setWidget(group_page)
        self.groups_tab_index = results_tabs.addTab(group_scroll, "Grupos")
        results_tabs.setTabVisible(self.groups_tab_index, False)
        self.perimeter_panel = PerimeterPanel()
        perimeter_scroll = QScrollArea()
        perimeter_scroll.setWidgetResizable(True)
        perimeter_scroll.setWidget(self.perimeter_panel)
        self.perimeter_tab_index = results_tabs.addTab(perimeter_scroll, "Perímetro")
        layout.addWidget(self.progress_bar)
        footer = QHBoxLayout()
        footer.setSpacing(16)
        footer.addWidget(self.example_button)
        footer.addWidget(self.feedback, 1)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel_search)
        footer.addWidget(self.cancel_button)
        footer.addWidget(self.prepare_button)
        layout.addLayout(footer)
        self.statusBar().showMessage("Cubiomes · Java 26.3 · Cabañas de brujas · Radio máximo: 50.000 bloques")
        self.dimension.currentIndexChanged.connect(self.update_structures)
        self.mode.currentIndexChanged.connect(self.update_mode)
        for field in (self.seed,):
            field.textChanged.connect(self.invalidate_query)
        for combo in (self.dimension, self.structure, self.mode):
            combo.currentIndexChanged.connect(self.invalidate_query)
        for field in (self.origin_x, self.origin_z, self.search_radius, self.minimum_count, self.group_radius):
            field.valueChanged.connect(self.invalidate_query)
        self.update_structures()
        self.update_mode()

    def update_structures(self) -> None:
        self.structure.clear()
        for item in STRUCTURES:
            if item.dimension == self.dimension.currentData():
                self.structure.addItem(item.label, item.id)
                if item.id != HUT:
                    option = self.structure.model().item(self.structure.count() - 1)
                    option.setEnabled(False)
                    option.setToolTip("Disponible en una próxima etapa.")

    def update_mode(self) -> None:
        grouped = self.mode.currentData() == SearchMode.GROUP
        self.group_frame.setVisible(grouped)
        self.results_tabs.setTabVisible(self.groups_tab_index, grouped)

    def invalidate_query(self) -> None:
        self.perimeter_panel.invalidate_imported_reference()
        self.prepared_request = None
        self.preview.clear()
        self.copy_button.setEnabled(False)
        self.table.setRowCount(0)
        self.group_results = []
        self.group_table.setRowCount(0)
        self.view_group_button.setEnabled(False)
        self.copy_group_button.setEnabled(False)
        self.group_perimeter_button.setEnabled(False)
        self.groups_hint.setText("Parámetros modificados. Ejecuta una búsqueda para actualizar los grupos.")
        self.result_hint.setText("Parámetros modificados. Ejecuta una búsqueda para obtener resultados actualizados.")
        self.feedback.setText("Parámetros pendientes de validar.")
        self.feedback.setStyleSheet("color: #aaa8b7;")

    def load_example(self) -> None:
        self.seed.setText("5067257298883736067")
        self.origin_x.setValue(-2599)
        self.origin_z.setValue(1953)
        self.dimension.setCurrentIndex(0)
        self.structure.setCurrentIndex(0)
        self.mode.setCurrentIndex(0)
        self.minimum_count.setValue(4)
        self.group_radius.setValue(200)
        self.search_radius.setValue(10_000)

    def prepare_query(self) -> None:
        try:
            raw = self.seed.text().strip()
            digits = raw[1:] if raw.startswith(("+", "-")) else raw
            if not digits or not digits.isascii() or not digits.isdigit():
                raise ValueError("Introduce una seed numérica entera, sin espacios ni decimales.")
            request = self.service.prepare(SearchRequest(
                seed=int(raw), version="26.3", dimension=Dimension(self.dimension.currentData()),
                structure_id=self.structure.currentData(), mode=SearchMode(self.mode.currentData()),
                origin_x=self.origin_x.value(), origin_z=self.origin_z.value(),
                search_radius=self.search_radius.value(), minimum_count=self.minimum_count.value(),
                group_radius=self.group_radius.value(),
            ))
        except ValueError as error:
            self.invalidate_query()
            self.feedback.setText(str(error))
            self.feedback.setStyleSheet("color: #ff9caa;")
            return
        self.prepared_request = request
        payload = {
            # Texto para preservar los 64 bits en consumidores JSON/JavaScript.
            "seed": str(request.seed), "edition": "java", "version": request.version,
            "dimension": request.dimension.value, "structure": request.structure_id,
            "mode": request.mode.value,
            "origin": {"x": request.origin_x, "z": request.origin_z},
            "search_radius_blocks": request.search_radius,
        }
        if request.mode == SearchMode.GROUP:
            payload["group"] = {"minimum_count": request.minimum_count, "radius_blocks": request.group_radius}
        self.preview.setPlainText(json.dumps(payload, indent=2, ensure_ascii=False))
        self.copy_button.setEnabled(True)
        self.feedback.setText("Consulta válida.")
        self.feedback.setStyleSheet("color: #c3a5fa;")

    def start_search(self) -> None:
        if self.worker is not None:
            return
        self.prepare_query()
        if self.prepared_request is None:
            return
        self.active_request = self.prepared_request
        self.table.setRowCount(0)
        self.group_results = []
        self.group_table.setRowCount(0)
        self.view_group_button.setEnabled(False)
        self.copy_group_button.setEnabled(False)
        self.group_perimeter_button.setEnabled(False)
        self.perimeter_panel.invalidate_imported_reference()
        self.groups_hint.setText("Buscando cabañas y calculando agrupaciones…")
        self.result_hint.setText("Buscando cabañas de brujas dentro del área. Puedes cancelar la búsqueda.")
        self.results_tabs.setCurrentIndex(self.groups_tab_index if self.active_request.mode == SearchMode.GROUP else 0)
        self.progress_bar.setValue(0)
        self.set_busy(True)
        self.worker = SearchWorker(self.service, self.active_request, self)
        self.worker.progress.connect(self.show_progress)
        self.worker.completed.connect(self.show_results)
        self.worker.failed.connect(self.show_error)
        self.worker.cancelled.connect(self.show_cancelled)
        self.worker.finished.connect(self.search_finished)
        self.worker.start()

    def set_busy(self, busy: bool) -> None:
        self.world_panel.setEnabled(not busy)
        self.config_panel.setEnabled(not busy)
        self.example_button.setEnabled(not busy)
        self.prepare_button.setEnabled(not busy)
        self.cancel_button.setVisible(busy)
        self.cancel_button.setEnabled(busy)
        self.progress_bar.setVisible(busy)
        if busy:
            self.feedback.setText("Explorando regiones de generación…")

    def show_progress(self, done: int, total: int) -> None:
        self.progress_bar.setValue(done * 100 // total if total else 0)
        if self.active_request is not None and self.active_request.mode == SearchMode.GROUP:
            self.progress_bar.setFormat("Búsqueda de grupos · %p%")
            self.feedback.setText("Calculando grupos…" if done >= 75 else "Explorando regiones de generación…")
        else:
            self.progress_bar.setFormat(f"{done:,} / {total:,} regiones · %p%")

    def show_results(self, locations: list) -> None:
        request = self.active_request
        if request is None:
            return
        if request.mode == SearchMode.GROUP:
            self.show_groups(locations)
            return
        self.table.setHorizontalHeaderLabels(["Estructura", "X", "Z", "Distancia", "Estado"])
        self.table.setRowCount(len(locations))
        for row, location in enumerate(locations):
            distance = math.hypot(location.x - request.origin_x, location.z - request.origin_z)
            values = ("Cabaña de bruja", str(location.x), str(location.z), f"{distance:,.1f} bloques", "Predicción")
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if column in (1, 2, 3):
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                cell.setToolTip("Posición de generación predicha por Cubiomes y comprobada por bioma. Altura Y no calculada.")
                self.table.setItem(row, column, cell)
        if locations:
            self.result_hint.setText(
                f"{len(locations)} ubicación(es) predicha(s) · Ordenadas por distancia desde X {request.origin_x}, Z {request.origin_z}.\n"
                f"Radio explorado: {request.search_radius:,} bloques."
            )
        else:
            self.result_hint.setText("No se encontraron cabañas de brujas dentro del radio indicado. Puedes ampliar el área o cambiar el origen.")
        self.feedback.setText("Búsqueda completada.")
        self.feedback.setStyleSheet("color: #c3a5fa;")

    def show_groups(self, groups: list[StructureGroup]) -> None:
        self.group_results = groups
        self.group_table.setRowCount(len(groups))
        request = self.active_request
        if request is None:
            return
        for row, group in enumerate(groups):
            distance = math.hypot(group.center_x-request.origin_x, group.center_z-request.origin_z)
            values = (str(row+1), str(len(group.members)), f"{group.center_x:.3f}", f"{group.center_z:.3f}",
                      f"{math.ceil(group.radius*10)/10:.1f}", f"{distance:,.1f}")
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                cell.setToolTip("Radio geométrico mínimo en bloques; centro de referencia, no punto AFK validado.")
                self.group_table.setItem(row, column, cell)
        if groups:
            self.groups_hint.setText(
                f"{len(groups)} grupo(s) de al menos {request.minimum_count} cabañas, con radio ≤ {request.group_radius} bloques.\n"
                "Ordenados por cercanía del centro al origen. Selecciona un grupo para ver sus cabañas."
            )
            self.group_table.selectRow(0)
            self.select_group()
        else:
            message = (f"No se encontraron grupos de al menos {request.minimum_count} cabañas "
                       f"con radio común de {request.group_radius} bloques en el área explorada.\n"
                       "Puedes ampliar el radio de exploración, aumentar el radio del grupo o reducir la cantidad.")
            self.groups_hint.setText(message)
            self.result_hint.setText(message)
        self.feedback.setText("Búsqueda de grupos completada.")
        self.feedback.setStyleSheet("color: #c3a5fa;")

    def select_group(self) -> None:
        row = self.group_table.currentRow()
        selected = bool(self.group_table.selectedItems()) and 0 <= row < len(self.group_results)
        self.view_group_button.setEnabled(selected)
        self.copy_group_button.setEnabled(selected)
        self.group_perimeter_button.setEnabled(selected)
        if not selected:
            return
        group = self.group_results[row]
        self.table.setHorizontalHeaderLabels(["Estructura", "X", "Z", "Al centro", "Estado"])
        self.table.setRowCount(len(group.members))
        for index, location in enumerate(group.members):
            distance = math.hypot(location.x-group.center_x, location.z-group.center_z)
            values = ("Cabaña de bruja", str(location.x), str(location.z), f"{distance:,.1f} bloques", "Predicción")
            for column, value in enumerate(values):
                self.table.setItem(index, column, QTableWidgetItem(value))
        self.result_hint.setText(
            f"Grupo {row+1} · {len(group.members)} cabañas · Centro X {group.center_x:.3f}, Z {group.center_z:.3f}.\n"
            f"Radio geométrico: {math.ceil(group.radius*10)/10:.1f} bloques. No es un punto AFK validado."
        )

    def copy_group(self) -> None:
        row = self.group_table.currentRow()
        if not self.group_table.selectedItems() or not 0 <= row < len(self.group_results):
            return
        group = self.group_results[row]
        lines = [f"Grupo {row+1} · {len(group.members)} cabañas de brujas",
                 f"Centro geométrico X: {group.center_x:.6f}, Z: {group.center_z:.6f}",
                 f"Radio: {math.ceil(group.radius*1000)/1000:.3f} bloques",
                 "Centro de referencia; no es un punto AFK validado."]
        lines.extend(f"Cabaña {i+1}: X: {p.x}, Z: {p.z}" for i, p in enumerate(group.members))
        QApplication.clipboard().setText("\n".join(lines))
        self.statusBar().showMessage("Centro y cabañas del grupo copiados", 4000)

    def show_error(self, message: str) -> None:
        self.table.setRowCount(0)
        self.group_results = []
        self.group_table.setRowCount(0)
        self.groups_hint.setText("No se pudo completar la búsqueda de grupos.")
        self.result_hint.setText("No se pudo completar la búsqueda. No se han generado resultados.")
        self.feedback.setText(message)
        self.feedback.setStyleSheet("color: #ff9caa;")

    def show_cancelled(self, message: str) -> None:
        self.table.setRowCount(0)
        self.group_results = []
        self.group_table.setRowCount(0)
        self.groups_hint.setText(message)
        self.result_hint.setText(message)
        self.feedback.setText("Búsqueda cancelada.")

    def cancel_search(self) -> None:
        if self.worker is not None:
            self.worker.cancel()
            self.cancel_button.setEnabled(False)
            self.feedback.setText("Cancelando búsqueda…")

    def search_finished(self) -> None:
        worker = self.worker
        self.worker = None
        self.set_busy(False)
        if worker is not None:
            worker.deleteLater()
        if self.closing_after_search:
            self.close()

    def closeEvent(self, event) -> None:
        if self.worker is not None:
            self.closing_after_search = True
            self.cancel_search()
            event.ignore()
        else:
            super().closeEvent(event)

    def copy_query(self) -> None:
        if self.prepared_request is not None:
            QApplication.clipboard().setText(self.preview.toPlainText())
            self.statusBar().showMessage("Consulta copiada al portapapeles", 4000)

    def copy_coordinates(self) -> None:
        row = self.table.currentRow()
        x, z = self.table.item(row, 1), self.table.item(row, 2)
        if x is not None and z is not None:
            QApplication.clipboard().setText(f"X: {x.text()}, Z: {z.text()}")
            self.statusBar().showMessage("Coordenadas copiadas al portapapeles", 4000)

    def update_location_actions(self) -> None:
        selected = bool(self.table.selectedItems())
        self.copy_coordinates_button.setEnabled(selected)
        self.location_perimeter_button.setEnabled(selected)

    def use_location_perimeter(self) -> None:
        row = self.table.currentRow()
        x, z = self.table.item(row, 1), self.table.item(row, 2)
        if not self.table.selectedItems() or x is None or z is None:
            return
        seed = self.active_request.seed if self.active_request is not None else ""
        self.perimeter_panel.use_reference(int(x.text()), int(z.text()), f"Cabaña seleccionada · Seed {seed}")
        self.results_tabs.setCurrentIndex(self.perimeter_tab_index)

    def use_group_perimeter(self) -> None:
        row = self.group_table.currentRow()
        if not self.group_table.selectedItems() or not 0 <= row < len(self.group_results):
            return
        group = self.group_results[row]
        seed = self.active_request.seed if self.active_request is not None else ""
        self.perimeter_panel.use_reference(group.center_x, group.center_z,
                                           f"Centro del grupo {row+1} · Seed {seed}", group.radius)
        self.results_tabs.setCurrentIndex(self.perimeter_tab_index)
