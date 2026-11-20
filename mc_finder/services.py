"""Servicio independiente de Qt para las búsquedas."""

from typing import Callable, Protocol
from dataclasses import replace

from .domain import SearchMode, SearchRequest, StructureLocation, StructureGroup


Progress = Callable[[int, int], None]
Cancelled = Callable[[], bool]


class SearchCancelledError(RuntimeError):
    pass


class SearchEngine(Protocol):
    def search(self, request: SearchRequest, *, progress: Progress | None = None,
               cancelled: Cancelled | None = None) -> list[StructureLocation]: ...


class EngineNotAvailableError(RuntimeError):
    pass


class UnavailableEngine:
    def search(self, request: SearchRequest, **kwargs) -> list[StructureLocation]:
        raise EngineNotAvailableError(
            "El motor de búsqueda todavía no está conectado. No se ha explorado la seed."
        )


class SearchService:
    def __init__(self, engine: SearchEngine | None = None):
        if engine is None:
            from .engine import CubiomesEngine
            engine = CubiomesEngine()
        self.engine = engine

    def prepare(self, request: SearchRequest) -> SearchRequest:
        request.validate()
        return request

    def search(self, request: SearchRequest, *, progress: Progress | None = None,
               cancelled: Cancelled | None = None) -> list[StructureLocation] | list[StructureGroup]:
        request = self.prepare(request)
        if request.mode != SearchMode.GROUP:
            return self.engine.search(request, progress=progress, cancelled=cancelled)
        from .groups import find_groups, MAX_GROUP_RADIUS
        if request.group_radius > MAX_GROUP_RADIUS:
            raise ValueError("El radio máximo de grupo en esta etapa es de 5.000 bloques.")

        def scan_progress(done, total):
            if progress:
                progress(done*75//max(total, 1), 100)

        def group_progress(done, total):
            if progress:
                progress(75+done*25//max(total, 1), 100)

        locations = self.engine.search(replace(request, mode=SearchMode.AREA),
                                       progress=scan_progress, cancelled=cancelled)
        groups = find_groups(locations, request.minimum_count, request.group_radius,
                             request.origin_x, request.origin_z,
                             progress=group_progress, cancelled=cancelled)
        if progress:
            progress(100, 100)
        return groups
