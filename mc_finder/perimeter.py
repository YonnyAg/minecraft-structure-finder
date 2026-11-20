"""Conservative horizontal coverage, independent of terrain and AFK solving."""

import math
from dataclasses import dataclass

SPAWN_RADIUS = 128
WORLD_LIMIT = 29_999_984


@dataclass(frozen=True)
class DirectionBoundary:
    direction: str
    axis: str
    additional_chunks: int
    block: int
    chunk: int


@dataclass(frozen=True)
class Perimeter:
    center_x: float
    center_z: float
    radius: int
    min_chunk_x: int
    max_chunk_x: int
    min_chunk_z: int
    max_chunk_z: int

    @property
    def min_x(self) -> int:
        return self.min_chunk_x * 16

    @property
    def max_x(self) -> int:
        return (self.max_chunk_x + 1) * 16 - 1

    @property
    def min_z(self) -> int:
        return self.min_chunk_z * 16

    @property
    def max_z(self) -> int:
        return (self.max_chunk_z + 1) * 16 - 1

    @property
    def width_chunks(self) -> int:
        return self.max_chunk_x - self.min_chunk_x + 1

    @property
    def depth_chunks(self) -> int:
        return self.max_chunk_z - self.min_chunk_z + 1

    @property
    def total_chunks(self) -> int:
        return self.width_chunks * self.depth_chunks

    @property
    def directions(self) -> tuple[DirectionBoundary, ...]:
        cx, cz = math.floor(self.center_x / 16), math.floor(self.center_z / 16)
        return (
            DirectionBoundary("Norte", "−Z", cz-self.min_chunk_z, self.min_z, self.min_chunk_z),
            DirectionBoundary("Sur", "+Z", self.max_chunk_z-cz, self.max_z, self.max_chunk_z),
            DirectionBoundary("Oeste", "−X", cx-self.min_chunk_x, self.min_x, self.min_chunk_x),
            DirectionBoundary("Este", "+X", self.max_chunk_x-cx, self.max_x, self.max_chunk_x),
        )

    def as_text(self) -> str:
        lines = [
            "Perímetro horizontal de referencia (no punto AFK validado)",
            f"Centro X: {self.center_x:.3f}, Z: {self.center_z:.3f}; radio: {self.radius} bloques",
            f"Rectángulo: {self.width_chunks} × {self.depth_chunks} chunks = {self.total_chunks} chunks",
            f"Proyección del disco: X [{self.center_x-self.radius:.3f}, {self.center_x+self.radius:.3f}], "
            f"Z [{self.center_z-self.radius:.3f}, {self.center_z+self.radius:.3f}]",
            f"Límites de bloques INCLUSIVOS: X [{self.min_x}, {self.max_x}], Z [{self.min_z}, {self.max_z}]",
            f"Chunks X [{self.min_chunk_x}, {self.max_chunk_x}], Z [{self.min_chunk_z}, {self.max_chunk_z}]",
            "Desde el chunk de referencia, sin contar ese chunk en cada dirección:",
        ]
        lines.extend(f"{d.direction} ({d.axis}): {d.additional_chunks} chunks adicionales; "
                     f"límite {d.axis[-1]} = {d.block}; chunk {d.chunk}" for d in self.directions)
        lines.append("Cobertura horizontal conservadora; no indica profundidad ni garantiza rendimiento. "
                     "No implica vaciar todos los bloques. Conservar las plataformas de las granjas.")
        return "\n".join(lines)


def calculate_perimeter(center_x: float, center_z: float, radius: int = SPAWN_RADIUS) -> Perimeter:
    """Cover the disk's bounding square with whole chunks.

    Floor both inclusive block limits, then floor-divide by 16. This deliberately
    includes the positive boundary block even when it lies exactly at an integer
    edge, rather than risking an under-sized excavation reference.
    """
    if not math.isfinite(center_x) or not math.isfinite(center_z):
        raise ValueError("Introduce coordenadas finitas para la referencia.")
    if not isinstance(radius, int) or radius <= 0:
        raise ValueError("El radio debe ser un entero positivo.")
    if abs(center_x)+radius > WORLD_LIMIT or abs(center_z)+radius > WORLD_LIMIT:
        raise ValueError("El perímetro sobrepasa el borde del mundo. Mueve la referencia hacia el interior.")
    plan = Perimeter(center_x, center_z, radius,
                     math.floor(center_x-radius)//16, math.floor(center_x+radius)//16,
                     math.floor(center_z-radius)//16, math.floor(center_z+radius)//16)
    if min(plan.min_x, plan.min_z) < -WORLD_LIMIT or max(plan.max_x, plan.max_z) > WORLD_LIMIT:
        raise ValueError("El rectángulo de chunks sobrepasa el borde del mundo. Mueve la referencia hacia el interior.")
    return plan
