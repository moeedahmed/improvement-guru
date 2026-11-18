"""Runtime path helpers for source and installed layouts."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import site
import sys


SOURCE_ROOT = Path(__file__).resolve().parents[1]
INSTALLED_DATA_ROOT = Path(sys.prefix) / "improvement-guru"


def data_path(*parts: str) -> Path:
    """Return a data path from source checkout or installed package data."""

    if not parts:
        return SOURCE_ROOT

    for part in parts:
        if not isinstance(part, str):
            raise TypeError("data path components must be strings")

        components = (PurePosixPath(part), PureWindowsPath(part))
        if any(component.anchor for component in components):
            raise ValueError("data path components must be relative")
        if any(".." in component.parts for component in components):
            raise ValueError("data path components must not contain '..'")

    for root in (SOURCE_ROOT, INSTALLED_DATA_ROOT):
        candidate = _existing_data_path(root, *parts)
        if candidate is not None:
            return candidate

    try:
        user_site = Path(site.getusersitepackages()).resolve()
    except (OSError, RuntimeError):
        imported_from_user_site = False
    else:
        imported_from_user_site = SOURCE_ROOT.is_relative_to(user_site)

    user_base = site.getuserbase() if site.ENABLE_USER_SITE or imported_from_user_site else None
    if user_base:
        candidate = _existing_data_path(Path(user_base) / "improvement-guru", *parts)
        if candidate is not None:
            return candidate
    return SOURCE_ROOT.joinpath(*parts)


def _existing_data_path(root: Path, *parts: str) -> Path | None:
    candidate = root.joinpath(*parts)
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError("data path escapes its data root")
    return candidate if candidate.exists() else None
