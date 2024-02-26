from __future__ import annotations

from typing import TYPE_CHECKING

from rattr.models.ir import FileIr
from rattr.models.util._serialisation_helpers import make_json_converter
from rattr.models.util._types import FileName, ImportIrs, OutputIrs

if TYPE_CHECKING:
    from typing import Any, TypeVar

    T = TypeVar("T")


__json_converter = make_json_converter()


def serialise(model: Any, **kwargs) -> str:
    return __json_converter.dumps(model, **kwargs)


def deserialise(json: str, *, type: type[T], **kwargs) -> T:
    return __json_converter.loads(json, cl=type, **kwargs)


def serialise_irs(
    *,
    target_name: FileName,
    target_ir: FileIr,
    imports_ir: ImportIrs,
) -> str:
    return serialise(
        OutputIrs(
            import_irs=imports_ir,
            target_ir={"filename": target_name, "ir": target_ir},
        ),
        indent=4,
    )
