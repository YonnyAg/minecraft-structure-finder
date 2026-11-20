"""Manual/reference perimeter UI, separate from the search and AFK logic."""

import math

from PySide6.QtWidgets import (
    QApplication, QDoubleSpinBox, QHBoxLayout, QHeaderView, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from .perimeter import Perimeter, SPAWN_RADIUS, WORLD_LIMIT, calculate_perimeter


class PerimeterPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("paper")
        self.plan: Perimeter | None = None
        self.source = "Referencia manual"
        self.group_radius: float | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        title = QLabel("PERÍMETRO HORIZONTAL")
        title.setObjectName("step")
        layout.addWidget(title)
        intro = QLabel("Cobertura horizontal conservadora de 128 bloques, alineada a chunks.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        form = QHBoxLayout()
        form.setSpacing(8)
        self.reference_x = self._coordinate()
        self.reference_z = self._coordinate()
        form.addWidget(QLabel("X"))
        form.addWidget(self.reference_x, 1)
        form.addWidget(QLabel("Z"))
        form.addWidget(self.reference_z, 1)
        self.calculate_button = QPushButton("Calcular límites")
        self.calculate_button.clicked.connect(self.calculate)
        form.addWidget(self.calculate_button)
        layout.addLayout(form)
        self.summary = QLabel("Introduce una referencia o usa una ubicación/grupo de los resultados.")
        self.summary.setObjectName("empty")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.boundaries = QTableWidget(0, 4)
        self.boundaries.setHorizontalHeaderLabels(["Dirección", "Chunks extra", "Límite de bloque", "Chunk límite"])
        self.boundaries.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.boundaries.verticalHeader().hide()
        self.boundaries.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.boundaries.setAlternatingRowColors(True)
        self.boundaries.setMinimumHeight(170)
        layout.addWidget(self.boundaries)
        self.limits = QLabel("")
        self.limits.setWordWrap(True)
        layout.addWidget(self.limits)
        note = QLabel(
            "Chunks extra: desde el chunk de referencia, sin contar ese chunk. Todos los límites son inclusivos.\n"
            "No calcula profundidad ni bloques que retirar. No implica vaciar todo el rectángulo: se deben conservar las granjas "
            "y controlar las apariciones ajenas. El punto AFK y la eficacia siguen pendientes de validar."
        )
        note.setObjectName("notice")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.copy_button = QPushButton("Copiar perímetro y coordenadas")
        self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(self.copy)
        layout.addWidget(self.copy_button)
        layout.addStretch()
        self.reference_x.valueChanged.connect(self.reference_changed)
        self.reference_z.valueChanged.connect(self.reference_changed)

    @staticmethod
    def _coordinate() -> QDoubleSpinBox:
        field = QDoubleSpinBox()
        field.setDecimals(3)
        field.setRange(-WORLD_LIMIT, WORLD_LIMIT)
        field.lineEdit().setTextMargins(8, 0, 8, 0)
        return field

    def reference_changed(self) -> None:
        self.plan = None
        self.source = "Referencia manual"
        self.group_radius = None
        self.boundaries.setRowCount(0)
        self.limits.clear()
        self.copy_button.setEnabled(False)
        self.summary.setText("Referencia modificada. Pulsa Calcular límites para actualizar el perímetro.")

    def use_reference(self, x: float, z: float, source: str, group_radius: float | None = None) -> None:
        self.reference_x.setValue(x)
        self.reference_z.setValue(z)
        self.source = source
        self.group_radius = group_radius
        self.calculate()

    def invalidate_imported_reference(self) -> None:
        if self.source != "Referencia manual":
            self.reference_changed()

    def calculate(self) -> None:
        self.plan = None
        self.copy_button.setEnabled(False)
        self.boundaries.setRowCount(0)
        self.limits.clear()
        try:
            plan = calculate_perimeter(self.reference_x.value(), self.reference_z.value())
        except ValueError as error:
            self.summary.setText(str(error))
            return
        self.plan = plan
        cx, cz = math.floor(plan.center_x/16), math.floor(plan.center_z/16)
        warning = ""
        if self.group_radius is not None and self.group_radius > SPAWN_RADIUS:
            warning = "\nEste grupo supera 128 bloques de radio. El perímetro no resuelve su separación ni activa todas las granjas."
        self.summary.setText(
            f"{self.source.split(' · Seed')[0]} · Chunk de referencia: ({cx}, {cz}).\n"
            f"Rectángulo de {plan.width_chunks} × {plan.depth_chunks} chunks: {plan.total_chunks} en total."
            + warning
        )
        self.boundaries.setRowCount(4)
        for row, boundary in enumerate(plan.directions):
            values = (f"{boundary.direction} ({boundary.axis})", str(boundary.additional_chunks),
                      f"{boundary.axis[-1]} = {boundary.block}", str(boundary.chunk))
            for column, value in enumerate(values):
                self.boundaries.setItem(row, column, QTableWidgetItem(value))
        self.limits.setText(
            f"Bloques X: {plan.min_x} a {plan.max_x} · Z: {plan.min_z} a {plan.max_z}\n"
            f"Chunks X: {plan.min_chunk_x} a {plan.max_chunk_x} · Z: {plan.min_chunk_z} a {plan.max_chunk_z}\n"
            f"Disco sin alinear: X [{plan.center_x-plan.radius:.3f}, {plan.center_x+plan.radius:.3f}], "
            f"Z [{plan.center_z-plan.radius:.3f}, {plan.center_z+plan.radius:.3f}]"
        )
        self.copy_button.setEnabled(True)

    def copy(self) -> None:
        if self.plan is not None:
            text = self.plan.as_text() + f"\nOrigen de la referencia: {self.source}"
            if self.group_radius is not None and self.group_radius > SPAWN_RADIUS:
                text += "\nEl grupo supera 128 bloques de radio; este perímetro no activa todas sus granjas."
            QApplication.clipboard().setText(text)
