from __future__ import annotations

from enum import StrEnum

from .function_resolver import FunctionResolutionError, locate_function_source


class DataParadigm(StrEnum):
    CLASSICAL = "classical"
    QUANTUM = "quantum"
