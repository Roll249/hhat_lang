from __future__ import annotations

from abc import ABC, abstractmethod
from collections import OrderedDict
from collections.abc import Mapping
from typing import Any, Iterator

from hhat_lang.core.data.core import CompositeSymbol, Symbol
from hhat_lang.core.error_handlers.errors import ErrorHandler


class SymbolOrdered(Mapping):
    """
    A special OrderedDict that accepts Symbol as keys but transforms them
    as str to unpack the class. Useful for building data structures such
    as `SingleDS`, `StructDS`, etc.
    """

    _data: OrderedDict[Symbol, Any]

    def __init__(self, data: dict | OrderedDict | None = None):
        self._data = OrderedDict() if data is None else OrderedDict(data)

    def __setitem__(self, key: str | Symbol | CompositeSymbol, value: Any) -> None:
        if isinstance(key, str):
            self._data[Symbol(key)] = value

        elif isinstance(key, (Symbol, CompositeSymbol)):
            self._data[key] = value

        else:
            raise ValueError(
                f"{key} ({type(key)}) is not valid key for data structures."
            )

    def __getitem__(self, key: str | Symbol | CompositeSymbol) -> Any:
        if isinstance(key, str):
            return self._data[Symbol(key)]

        if isinstance(key, (Symbol, CompositeSymbol)):
            return self._data[key]

        raise ValueError(key)

    def __len__(self) -> int:
        return len(self._data)

    def items(self) -> Iterator:
        yield from self._data.items()

    def keys(self) -> Iterator:
        for k in self._data.keys():
            yield k.value

    def values(self) -> Iterator:
        yield from self._data.values()

    def __iter__(self) -> Iterator:
        for k in self._data:
            yield k  # .name

    def __repr__(self) -> str:
        return str(self._data)


class Result(ABC):
    """The `Result` class is meant to be used for instructions execution results"""

    def __init__(self, value: Any):
        self.value = value

    @abstractmethod
    def result(self) -> Any: ...


class Ok(Result):
    """Use `Ok` when an instruction result returns successfully."""

    def result(self) -> Any:
        return self.value


class Error(Result):
    """Use `Error` when an instruction result returns an error (`ErrorHandler`)."""

    def result(self) -> ErrorHandler:
        return self.value
