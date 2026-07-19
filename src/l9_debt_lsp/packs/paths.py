from __future__ import annotations
import os
import platform
from dataclasses import dataclass
from pathlib import Path
def default_state_root() -> Path:
    override = os.environ.get("L9_DEBT_LSP_STATE_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    system = platform.system().lower()
    if system == "windows":
        base = os.environ.get("LOCALAPPDATA")
        if not base:
            base = str(Path.home() / "AppData/Local")
        return (Path(base) / "L9/debt-lsp").resolve()
    if system == "darwin":
        return (
            Path.home()
            / "Library/Application Support/L9/debt-lsp"
        ).resolve()
    xdg_state = os.environ.get("XDG_STATE_HOME")
    if xdg_state:
        return (Path(xdg_state) / "l9/debt-lsp").resolve()
    return (
        Path.home() / ".local/state/l9/debt-lsp"
    ).resolve()
@dataclass(frozen=True)
class StatePaths:
    root: Path
    @property
    def packs(self) -> Path:
        return self.root / "packs"
    @property
    def staging(self) -> Path:
        return self.root / "staging"
    @property
    def quarantine(self) -> Path:
        return self.root / "quarantine"
    @property
    def trust(self) -> Path:
        return self.root / "trust"
    @property
    def trusted_keys(self) -> Path:
        return self.trust / "trusted-keys.json"
    @property
    def activation(self) -> Path:
        return self.root / "activation"
    @property
    def active(self) -> Path:
        return self.activation / "active.json"
    @property
    def previous(self) -> Path:
        return self.activation / "previous-known-good.json"
    @property
    def activation_history(self) -> Path:
        return self.activation / "activation-history.jsonl"
    @property
    def retirement(self) -> Path:
        return self.root / "retirement"
    @property
    def retired_packs(self) -> Path:
        return self.retirement / "retired-packs.json"
    def initialize(self) -> None:
        for directory in (
            self.root,
            self.packs,
            self.staging,
            self.quarantine,
            self.trust,
            self.activation,
            self.retirement,
        ):
            directory.mkdir(parents=True, exist_ok=True)
            directory.chmod(0o700)
