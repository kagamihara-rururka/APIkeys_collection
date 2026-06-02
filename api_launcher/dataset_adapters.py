from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from api_launcher.adapters import (
    DatasetAdapter,
    GEBCOTopographyAdapter,
    HYGStarCatalogAdapter,
    YFinanceMarketDataAdapter,
)
from api_launcher.models import Provider


DATASET_ADAPTERS: tuple[DatasetAdapter, ...] = (
    GEBCOTopographyAdapter(),
    HYGStarCatalogAdapter(),
    YFinanceMarketDataAdapter(),
)


@dataclass(frozen=True)
class DatasetAdapterRegistryEntry:
    adapter_id: str
    provider_id: str
    adapter_class: str
    module: str
    discovery_method: str
    scope: str
    delivery_boundary: str
    supported_formats: tuple[str, ...]
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "provider_id": self.provider_id,
            "adapter_class": self.adapter_class,
            "module": self.module,
            "discovery_method": self.discovery_method,
            "scope": self.scope,
            "delivery_boundary": self.delivery_boundary,
            "supported_formats": list(self.supported_formats),
            "status": self.status,
        }


_ADAPTER_METADATA_BY_CLASS: dict[str, dict[str, Any]] = {
    "GEBCOTopographyAdapter": {
        "adapter_id": "gebco_topography",
        "scope": "global_bathymetry_topography_dataset",
        "delivery_boundary": "metadata_and_versioned_download_contract",
        "supported_formats": ("netcdf", "opendap"),
        "status": "implemented_bounded",
    },
    "HYGStarCatalogAdapter": {
        "adapter_id": "hyg_star_catalog",
        "scope": "star_catalog_csv_dataset",
        "delivery_boundary": "metadata_and_direct_csv_gz_contract",
        "supported_formats": ("csv", "csv.gz"),
        "status": "implemented_bounded",
    },
    "YFinanceMarketDataAdapter": {
        "adapter_id": "yfinance_market_data",
        "scope": "user_requested_market_timeseries",
        "delivery_boundary": "explicit_user_fetch_then_csv_import_contract",
        "supported_formats": ("csv", "ohlcv"),
        "status": "implemented_bounded_with_terms_review",
    },
}


def _entry_for_adapter(adapter: DatasetAdapter) -> DatasetAdapterRegistryEntry:
    adapter_class = type(adapter).__name__
    metadata = _ADAPTER_METADATA_BY_CLASS.get(adapter_class, {})
    return DatasetAdapterRegistryEntry(
        adapter_id=str(metadata.get("adapter_id") or adapter_class),
        provider_id=adapter.provider_id,
        adapter_class=adapter_class,
        module=type(adapter).__module__,
        discovery_method="discover",
        scope=str(metadata.get("scope") or "provider_specific_dataset_metadata"),
        delivery_boundary=str(metadata.get("delivery_boundary") or "adapter_specific_discovery_only"),
        supported_formats=tuple(str(item) for item in metadata.get("supported_formats", ())),
        status=str(metadata.get("status") or "registered"),
    )


def dataset_adapter_registry_entries() -> tuple[DatasetAdapterRegistryEntry, ...]:
    """Return the provider-specific deep adapter inventory.

    This is intentionally separate from source crawler handler coverage.  A
    source handler can discover candidates for many source types, while these
    adapters describe the small set of provider-specific dataset records that
    already have explicit adapter ownership.
    """

    return tuple(_entry_for_adapter(adapter) for adapter in DATASET_ADAPTERS)


def dataset_adapter_report() -> dict[str, Any]:
    entries = dataset_adapter_registry_entries()
    return {
        "registry_owner": "api_launcher.dataset_adapters.DATASET_ADAPTERS",
        "dataset_adapter_count": len(entries),
        "adapter_ids": [entry.adapter_id for entry in entries],
        "provider_ids": [entry.provider_id for entry in entries],
        "registered_adapters": [entry.to_dict() for entry in entries],
        "source_type_scope": "provider_specific_dataset_adapter_not_source_crawler_handler",
        "coverage_boundary": (
            "These adapters cover explicit provider-specific dataset records. "
            "They do not imply that every supported source crawler type has a "
            "deep provider adapter, curated importer, or renderer bridge."
        ),
        "next_action": "add_deep_adapters_only_when_they_close_real_download_import_paths",
    }


def adapters_for_provider(provider: Provider) -> list[DatasetAdapter]:
    # 目前用明確 registry；新增 adapter 時先確認它服務 MVP 的 discovery/plan 路徑。
    return [adapter for adapter in DATASET_ADAPTERS if adapter.provider_id == provider.provider_id]
