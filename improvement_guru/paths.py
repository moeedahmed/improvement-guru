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

    roots = [SOURCE_ROOT, INSTALLED_DATA_ROOT]
    imported_from_user_site = SOURCE_ROOT.is_relative_to(Path(site.getusersitepackages()).resolve())
    user_base = site.getuserbase() if site.ENABLE_USER_SITE or imported_from_user_site else None
    if user_base:
        user_data_root = Path(user_base) / "improvement-guru"
        if imported_from_user_site:
            roots.insert(1, user_data_root)
        else:
            roots.append(user_data_root)

    for root in roots:
        candidate = root.joinpath(*parts)
        resolved_root = root.resolve()
        resolved_candidate = candidate.resolve()
        if not resolved_candidate.is_relative_to(resolved_root):
            raise ValueError("data path escapes its data root")
        if candidate.exists():
            return candidate
    return SOURCE_ROOT.joinpath(*parts)
