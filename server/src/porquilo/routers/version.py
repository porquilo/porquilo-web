from importlib.metadata import PackageNotFoundError, version

from fastapi import APIRouter

# Fallback for editable installs without build-backend metadata (e.g. pip install -e .
# with a plain pyproject.toml and no hatchling/flit build step). importlib.metadata
# needs the *.dist-info directory to be present; editable installs may omit it.
VERSION = "0.1.0"

try:
    VERSION = version("porquilo")
except PackageNotFoundError:
    pass

router = APIRouter()


@router.get("/api/version")
def get_version():
    return {"version": VERSION}
