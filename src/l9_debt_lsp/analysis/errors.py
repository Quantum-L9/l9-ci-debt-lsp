from __future__ import annotations


class AnalysisError(RuntimeError):
    """Base incremental-analysis failure."""


class WorkspaceNotFoundError(AnalysisError):
    """The requested workspace session does not exist."""


class WorkspaceClosedError(AnalysisError):
    """The workspace is closed."""


class DocumentNotFoundError(AnalysisError):
    """The requested document overlay does not exist."""


class DocumentVersionError(AnalysisError):
    """A document update is not strictly newer."""


class DocumentLimitError(AnalysisError):
    """A document or workspace resource limit was exceeded."""


class AnalysisCancelledError(AnalysisError):
    """The analysis request was cancelled."""


class AnalysisTimeoutError(AnalysisError):
    """The analysis request exceeded the runtime timeout."""


class StaleAnalysisResultError(AnalysisError):
    """The result no longer matches current runtime state."""


class SDKAdapterError(AnalysisError):
    """The public SDK analysis adapter failed."""
