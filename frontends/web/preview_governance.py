"""Governance status payloads for the local Web Preview.

This module is deliberately read-only and static. It summarizes the current
Core governance evidence for a browser UIUX review surface, but it must not run
checkpoint scripts, validators, tests, git, or any subprocess on request.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class GovernanceDocRef:
    doc_id: str
    label: str
    path: str
    role: str


ASSETCARD_GOVERNANCE_DOCS: tuple[GovernanceDocRef, ...] = (
    GovernanceDocRef(
        "governance_checkpoint_index",
        "治理索引",
        "docs/ASSETCARD_GOVERNANCE_CHECKPOINT_INDEX.zh-TW.md",
        "彙整 AssetCard/export-query/redaction 文件與可執行證據命令。",
    ),
    GovernanceDocRef(
        "governance_command_design",
        "Checkpoint wrapper 設計",
        "docs/ASSETCARD_GOVERNANCE_CHECKPOINT_COMMAND_DESIGN.zh-TW.md",
        "說明 wrapper JSON 欄位、runner 邊界與 fan-out 防護。",
    ),
    GovernanceDocRef(
        "governance_usage_failure_index",
        "使用與失敗狀態索引",
        "docs/ASSETCARD_GOVERNANCE_CHECKPOINT_USAGE_FAILURE_INDEX.zh-TW.md",
        "說明 wrapper / validator / meta-test 的使用方式與 stop conditions。",
    ),
    GovernanceDocRef(
        "export_query_adr_draft",
        "Export/query ADR 草案",
        "docs/ASSETCARD_EXPORT_QUERY_CONTRACT_ADR_DRAFT.zh-TW.md",
        "描述未來 reference projection/envelope 的草案語言，不是 API 實作。",
    ),
    GovernanceDocRef(
        "preimplementation_gate",
        "Preimplementation gate",
        "docs/ASSETCARD_EXPORT_QUERY_PREIMPLEMENTATION_GATE.zh-TW.md",
        "定義未來實作前必須通過的 redaction / negative test / stop condition。",
    ),
    GovernanceDocRef(
        "touchpoint_negative_matrix",
        "Touchpoint / negative matrix",
        "docs/ASSETCARD_EXPORT_QUERY_TOUCHPOINT_NEGATIVE_TEST_MATRIX.zh-TW.md",
        "盤點未來可能碰到的 Core touchpoints 與負向測試矩陣。",
    ),
    GovernanceDocRef(
        "redaction_fixture_matrix",
        "Redaction fixture matrix",
        "docs/ASSETCARD_EXPORT_QUERY_REDACTION_FIXTURE_MATRIX.zh-TW.md",
        "列出未來 redaction 正反例 fixture 案例；目前仍是文件矩陣。",
    ),
    GovernanceDocRef(
        "redaction_fixture_packet_design",
        "Redaction fixture packet design",
        "docs/ASSETCARD_REDACTION_FIXTURE_PACKET_DESIGN.zh-TW.md",
        "定義未來 fixture packet 欄位與 diagnostics vocabulary；目前不執行。",
    ),
)


def web_assetcard_governance_checkpoints() -> dict[str, object]:
    """Return display-ready Core governance status for the Web Preview.

    The payload mirrors the current governance lane without revalidating it at
    request time. Agents should run the documented CLI/scripts for evidence;
    the Web Preview only visualizes the known contract boundaries.
    """

    docs = [governance_doc_payload(ref) for ref in ASSETCARD_GOVERNANCE_DOCS]
    missing_docs = [item["path"] for item in docs if not item["present"]]
    return {
        "schema": "web_assetcard_governance_checkpoints.v1",
        "surface": "web_preview",
        "purpose": "uiux_review",
        "source_of_truth": "GitHub commits, tests, smoke, CLI JSON, UI behavior, and diffs.",
        "not_source_of_truth": "Web Preview is a browser UIUX review surface, not a product Web app.",
        "core_gate_status": "partial",
        "core_gate_label": "Core readiness: partial",
        "checkpoint_status": "passed" if not missing_docs else "needs_review",
        "checkpoint_label": "治理 checkpoint 可掃描" if not missing_docs else "治理文件路徑待確認",
        "summary_cards": [
            {
                "label": "Core readiness",
                "value": "partial",
                "tone": "warning",
                "detail": "目前只能說 Core evidence 更清楚；不能升格成完成或可整合。",
            },
            {
                "label": "Wrapper",
                "value": "leaf evidence only",
                "tone": "success",
                "detail": "checkpoint wrapper 聚合 leaf evidence，不呼叫 validator、tests、git 或 subprocess fan-out。",
            },
            {
                "label": "Validator",
                "value": "boundary flags",
                "tone": "success",
                "detail": "validator 檢查 JSON、partial gate、missing docs 與 false-safety 欄位。",
            },
            {
                "label": "Meta-test",
                "value": "negative mutation",
                "tone": "neutral",
                "detail": "meta-test 測 JSON purity、負向 mutation 與 validator 行為，不由 checkpoint 反向呼叫。",
            },
        ],
        "false_safety_flags": [
            {"flag": "export_query_api_exists", "expected": False, "label": "Export/query API 尚未建立"},
            {"flag": "json_fixture_driver_exists", "expected": False, "label": "JSON fixture driver 尚未建立"},
            {"flag": "cross_repo_integration", "expected": False, "label": "未授權跨 repo 實作"},
            {"flag": "payload_exposure", "expected": False, "label": "不得暴露 payload"},
            {"flag": "private_path_exposure", "expected": False, "label": "不得暴露私有本機路徑"},
            {"flag": "odoriba_consumption_claim", "expected": False, "label": "不得宣稱 Odoriba 可消費 Core cards"},
        ],
        "runner_separation": [
            {
                "layer": "checkpoint",
                "label": "Checkpoint wrapper",
                "responsibility": "聚合 Core gate、docs presence、false-safety flags 與 fan-out counters。",
                "must_not_do": "不得呼叫 tests、validator、fixture packets、export/query paths 或下游 repo。",
            },
            {
                "layer": "validator",
                "label": "Validator",
                "responsibility": "驗證 checkpoint JSON、boundary flags、partial gate 與 missing-doc state。",
                "must_not_do": "不得呼叫 pytest/unittest 或製造 checkpoint -> validator -> test loop。",
            },
            {
                "layer": "meta_test",
                "label": "Meta-test",
                "responsibility": "測 JSON purity、負向 in-memory mutation、source-level recursion guard。",
                "must_not_do": "不得被 checkpoint 或 validator scripts 呼叫。",
            },
        ],
        "stop_conditions": [
            "需要新增 export/query API。",
            "需要改 DB/schema/lifecycle/readiness behavior。",
            "需要 expose payload 或 private local path。",
            "需要 import c_2/c_3/c_4 或 downstream runtime code。",
            "需要宣稱 requester 可以消費 Core cards。",
            "Core gate 不再是 partial。",
        ],
        "docs": docs,
        "missing_docs": missing_docs,
        "safety_note": "No readiness, no integration, no downstream consumption authorization.",
    }


def governance_doc_payload(ref: GovernanceDocRef) -> dict[str, object]:
    path = REPO_ROOT / ref.path
    return {
        "doc_id": ref.doc_id,
        "label": ref.label,
        "path": ref.path,
        "role": ref.role,
        "present": path.exists(),
    }
