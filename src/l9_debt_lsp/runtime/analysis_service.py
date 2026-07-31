from __future__ import annotations

from pathlib import Path

from l9_debt_lsp.analysis.models import PackContext
from l9_debt_lsp.analysis.null_sdk import (
    UnavailableAnalysisSession,
)
from l9_debt_lsp.analysis.runtime import (
    IncrementalAnalysisRuntime,
)
from l9_debt_lsp.packs.activation import ActivationManager
from l9_debt_lsp.packs.paths import StatePaths


def load_active_pack_context(
    *,
    paths: StatePaths,
    schema_root: Path,
) -> PackContext:
    manager = ActivationManager(
        paths=paths,
        schema_root=schema_root,
    )
    pointer = manager.load_active()
    if pointer is None:
        raise RuntimeError("no active defense pack is configured")
    return PackContext(
        pack_id=pointer.pack_id,
        pack_version=pointer.pack_version,
        corpus_snapshot=pointer.corpus_snapshot,
        compiler_version=pointer.compiler_version,
        taxonomy_version=pointer.taxonomy_version,
        sdk_contract_version=pointer.sdk_contract_version,
    )


def build_default_runtime() -> IncrementalAnalysisRuntime:
    return IncrementalAnalysisRuntime(UnavailableAnalysisSession())
