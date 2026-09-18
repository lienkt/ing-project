"""All source JSON reading/validation stays here, separate from Dataset."""

import json
from pathlib import Path
from pydantic import Field
from app.schemas.campaign import Schema
from app.schemas.automation import SourceDefinition

CATALOG_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "sources"


class SourceFile(Schema):
    sources: list[SourceDefinition] = Field(min_length=1)


class CatalogError(ValueError):
    pass


def load_sources(directory: Path | None = None) -> list[SourceDefinition]:
    result = []
    identities = set()
    for path in sorted((directory or CATALOG_DIRECTORY).glob("*.json")):
        try:
            document = SourceFile.model_validate(json.loads(path.read_text()))
            for source in document.sources:
                if source.source_id in identities:
                    raise ValueError(f"Duplicate source_id: {source.source_id}")
                identities.add(source.source_id)
                result.append(source)
        except (ValueError, OSError) as exc:
            raise CatalogError(f"Invalid source catalog {path.name}: {exc}") from exc
    if not result:
        raise CatalogError("Source catalog is empty or its directory is missing")
    return result


def filter_sources(sources, bank=None, product_category=None):
    return [
        s
        for s in sources
        if (not bank or s.bank.casefold() == bank.casefold())
        and (not product_category or s.product_category == product_category)
    ]


def find_source(sources, source_id):
    return next((source for source in sources if source.source_id == source_id), None)


def banks(sources):
    return sorted({source.bank for source in sources})
