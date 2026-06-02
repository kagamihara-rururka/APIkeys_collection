from __future__ import annotations

import unittest

from api_launcher.dataset_adapters import (
    adapters_for_provider,
    dataset_adapter_registry_entries,
    dataset_adapter_report,
)
from api_launcher.models import Provider


class DatasetAdapterRegistryTests(unittest.TestCase):
    def test_dataset_adapter_report_lists_current_deep_adapter_scope(self) -> None:
        report = dataset_adapter_report()

        self.assertEqual(3, report["dataset_adapter_count"])
        self.assertEqual(
            ["gebco_topography", "hyg_star_catalog", "yfinance_market_data"],
            report["adapter_ids"],
        )
        self.assertEqual(
            "provider_specific_dataset_adapter_not_source_crawler_handler",
            report["source_type_scope"],
        )
        self.assertIn("do not imply", report["coverage_boundary"])
        self.assertIn("yahoo_finance_yfinance", report["provider_ids"])

    def test_registry_entries_expose_module_class_and_boundary(self) -> None:
        entries = {entry.adapter_id: entry for entry in dataset_adapter_registry_entries()}

        self.assertEqual("api_launcher.adapters.gebco", entries["gebco_topography"].module)
        self.assertEqual("GEBCOTopographyAdapter", entries["gebco_topography"].adapter_class)
        self.assertEqual(
            "metadata_and_versioned_download_contract",
            entries["gebco_topography"].delivery_boundary,
        )
        self.assertEqual(("netcdf", "opendap"), entries["gebco_topography"].supported_formats)
        self.assertEqual("implemented_bounded_with_terms_review", entries["yfinance_market_data"].status)

    def test_adapters_for_provider_still_filters_by_provider_id(self) -> None:
        provider = Provider(
            provider_id="hyg_database",
            name="HYG",
            owner="Astronexus",
            categories=("astronomy",),
            geographic_scope="global",
            docs_url="https://example.test/hyg",
        )

        adapters = adapters_for_provider(provider)

        self.assertEqual(1, len(adapters))
        self.assertEqual("hyg_database", adapters[0].provider_id)


if __name__ == "__main__":
    unittest.main()
