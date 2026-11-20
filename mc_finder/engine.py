"""First real engine: biome-validated swamp-hut predictions for Java 26.3.

Each search owns its native context. No Qt, network calls, or generated chunks.
"""

import ctypes
import platform
from pathlib import Path

from .domain import Dimension, SearchMode, SearchRequest, StructureLocation
from .services import Cancelled, EngineNotAvailableError, Progress, SearchCancelledError

MAX_RADIUS = 50_000
WORLD_LIMIT = 29_999_984
HUT = "minecraft:swamp_hut"


class CubiomesEngine:
    def __init__(self, library_path: Path | None = None):
        self.library_path = library_path or Path(__file__).parent / "_native" / "finder.dll"

    def _load(self):
        if platform.system() != "Windows" or ctypes.sizeof(ctypes.c_void_p) != 8:
            raise EngineNotAvailableError("Este primer motor requiere Windows de 64 bits.")
        if not self.library_path.is_file():
            raise EngineNotAvailableError("Falta el motor local. Consulta scripts/build_engine.py en README.md.")
        try:
            library = ctypes.CDLL(str(self.library_path.resolve()))
            library.finder_abi.argtypes = []
            library.finder_abi.restype = ctypes.c_int
            if library.finder_abi() != 1:
                raise EngineNotAvailableError("La versión del motor no es compatible con esta aplicación.")
            library.finder_region_blocks.argtypes = []
            library.finder_region_blocks.restype = ctypes.c_int
            library.finder_create.argtypes = [ctypes.c_int64]
            library.finder_create.restype = ctypes.c_void_p
            library.finder_free.argtypes = [ctypes.c_void_p]
            library.finder_free.restype = None
            library.finder_hut.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                          ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
            library.finder_hut.restype = ctypes.c_int
        except (OSError, AttributeError) as error:
            raise EngineNotAvailableError(f"No se pudo cargar el motor local: {error}") from error
        return library

    def search(self, request: SearchRequest, *, progress: Progress | None = None,
               cancelled: Cancelled | None = None) -> list[StructureLocation]:
        request.validate()
        if request.dimension != Dimension.OVERWORLD or request.structure_id != HUT:
            raise ValueError("Esta etapa busca cabañas de brujas del Overworld. Las demás estructuras llegarán después.")
        if request.mode == SearchMode.GROUP:
            raise ValueError("La búsqueda de agrupaciones estará disponible en una próxima etapa.")
        if request.search_radius > MAX_RADIUS:
            raise ValueError("En esta etapa el radio máximo es de 50.000 bloques.")
        if abs(request.origin_x) > WORLD_LIMIT or abs(request.origin_z) > WORLD_LIMIT:
            raise ValueError("El punto de referencia debe estar dentro del borde del mundo.")

        library = self._load()
        size = library.finder_region_blocks()
        if size != 512:
            raise EngineNotAvailableError("La configuración de cabañas del motor no coincide con la esperada.")
        radius = request.search_radius
        # Floor division is essential for negative Minecraft coordinates.
        min_rx = max(-WORLD_LIMIT, request.origin_x - radius) // size
        max_rx = min(WORLD_LIMIT, request.origin_x + radius) // size
        min_rz = max(-WORLD_LIMIT, request.origin_z - radius) // size
        max_rz = min(WORLD_LIMIT, request.origin_z + radius) // size
        total = (max_rx - min_rx + 1) * (max_rz - min_rz + 1)
        context = library.finder_create(request.seed)
        if not context:
            raise EngineNotAvailableError("No se pudo reservar memoria para el motor.")
        found: list[StructureLocation] = []
        try:
            if progress:
                progress(0, total)
            done = 0
            last_percent = -1
            for rx in range(min_rx, max_rx + 1):
                for rz in range(min_rz, max_rz + 1):
                    if cancelled and cancelled():
                        raise SearchCancelledError("Búsqueda cancelada. No se muestran resultados incompletos.")
                    x, z = ctypes.c_int(), ctypes.c_int()
                    result = library.finder_hut(context, rx, rz, ctypes.byref(x), ctypes.byref(z))
                    if result < 0:
                        raise EngineNotAvailableError("El motor rechazó una consulta de región.")
                    if result and abs(x.value) <= WORLD_LIMIT and abs(z.value) <= WORLD_LIMIT:
                        dx, dz = x.value - request.origin_x, z.value - request.origin_z
                        if dx * dx + dz * dz <= radius * radius:
                            found.append(StructureLocation(HUT, Dimension.OVERWORLD, x.value, z.value))
                    done += 1
                    percent = done * 100 // total
                    if progress and percent != last_percent:
                        progress(done, total)
                        last_percent = percent
            if cancelled and cancelled():
                raise SearchCancelledError("Búsqueda cancelada. No se muestran resultados incompletos.")
        finally:
            library.finder_free(context)
        found.sort(key=lambda p: ((p.x-request.origin_x)**2 + (p.z-request.origin_z)**2, p.x, p.z))
        return found[:1] if request.mode == SearchMode.NEAREST else found
