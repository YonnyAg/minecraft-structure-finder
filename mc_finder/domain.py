"""Parámetros independientes de Qt y del motor de generación."""

from dataclasses import dataclass
from enum import Enum


class Dimension(str, Enum):
    OVERWORLD = "overworld"
    NETHER = "the_nether"
    END = "the_end"


class SearchMode(str, Enum):
    NEAREST = "nearest"
    AREA = "area"
    GROUP = "group"


@dataclass(frozen=True)
class Structure:
    id: str
    label: str
    dimension: Dimension


# Catálogo previsto. La interfaz habilita solo los tipos ya implementados.
STRUCTURES = (
    Structure("minecraft:swamp_hut", "Cabaña de bruja", Dimension.OVERWORLD),
    Structure("minecraft:village", "Aldea", Dimension.OVERWORLD),
    Structure("minecraft:monument", "Monumento oceánico", Dimension.OVERWORLD),
    Structure("minecraft:mansion", "Mansión del bosque", Dimension.OVERWORLD),
    Structure("minecraft:ancient_city", "Ciudad antigua", Dimension.OVERWORLD),
    Structure("minecraft:trial_chambers", "Cámaras de pruebas", Dimension.OVERWORLD),
    Structure("minecraft:fortress", "Fortaleza del Nether", Dimension.NETHER),
    Structure("minecraft:bastion_remnant", "Bastión", Dimension.NETHER),
    Structure("minecraft:end_city", "Ciudad del End", Dimension.END),
)


@dataclass(frozen=True)
class SearchRequest:
    seed: int
    version: str
    dimension: Dimension
    structure_id: str
    mode: SearchMode
    origin_x: int
    origin_z: int
    search_radius: int
    minimum_count: int = 4
    group_radius: int = 200

    def validate(self) -> None:
        if not -(2**63) <= self.seed < 2**63:
            raise ValueError("La seed debe estar entre −9223372036854775808 y 9223372036854775807.")
        if self.version != "26.3":
            raise ValueError("Esta interfaz está preparada para Java 26.3.")
        if not any(s.id == self.structure_id and s.dimension == self.dimension for s in STRUCTURES):
            raise ValueError("Selecciona una estructura de la dimensión elegida.")
        if self.search_radius <= 0:
            raise ValueError("El radio de exploración debe ser mayor que cero.")
        if self.mode == SearchMode.GROUP and (self.minimum_count < 2 or self.group_radius <= 0):
            raise ValueError("Un grupo necesita al menos dos estructuras y un radio mayor que cero.")


@dataclass(frozen=True)
class StructureLocation:
    """Contrato inicial para resultados futuros; las coordenadas Y son opcionales."""

    structure_id: str
    dimension: Dimension
    x: int
    z: int
    y: int | None = None


@dataclass(frozen=True)
class StructureGroup:
    """A maximal set fitting one horizontal circle; not an AFK certification."""

    members: tuple[StructureLocation, ...]
    center_x: float
    center_z: float
    radius: float
