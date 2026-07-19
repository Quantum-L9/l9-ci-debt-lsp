from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from .packs.activation import ActivationManager
from .packs.installer import PackInstaller
from .packs.paths import StatePaths, default_state_root
from .packs.store import PackStore
from .runtime.capabilities import phase_capabilities
from .telemetry.paths import TelemetryPaths
from .telemetry.service import TelemetryService


def schema_root() -> Path:
    return Path("schemas/lsp").resolve()


def state_paths(value: Path | None) -> StatePaths:
    return StatePaths((value or default_state_root()).expanduser().resolve())


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="l9-debt-lsp-contracts")
    root.add_argument(
        "--state-root",
        type=Path,
        default=None,
    )
    commands = root.add_subparsers(
        dest="command",
        required=True,
    )
    commands.add_parser("capabilities")
    install = commands.add_parser("install-pack")
    install.add_argument(
        "--manifest",
        type=Path,
        required=True,
    )
    install.add_argument(
        "--archive",
        type=Path,
        required=True,
    )
    install.add_argument("--platform")
    activate = commands.add_parser("activate-pack")
    activate.add_argument("--pack-id", required=True)
    commands.add_parser("rollback-pack")
    commands.add_parser("active-pack")
    commands.add_parser("recover-state")
    commands.add_parser("telemetry-health")
    commands.add_parser("telemetry-deliver")
    commands.add_parser("telemetry-delete-all")
    verify = commands.add_parser("verify-installed-pack")
    verify.add_argument("--pack-id", required=True)
    return root


def emit(value: object) -> None:
    print(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    paths = state_paths(arguments.state_root)
    schemas = schema_root()
    if arguments.command == "capabilities":
        emit(phase_capabilities())
        return 0
    if arguments.command == "install-pack":
        installed = PackInstaller(
            paths=paths,
            schema_root=schemas,
        ).install(
            manifest_path=arguments.manifest.resolve(),
            archive_path=arguments.archive.resolve(),
            platform_identity=arguments.platform,
        )
        emit(installed.as_dict())
        return 0
    manager = ActivationManager(
        paths=paths,
        schema_root=schemas,
    )
    if arguments.command == "activate-pack":
        pointer = manager.activate(arguments.pack_id)
        emit(pointer.as_dict())
        return 0
    if arguments.command == "rollback-pack":
        pointer = manager.rollback()
        emit(pointer.as_dict())
        return 0
    if arguments.command == "active-pack":
        active = manager.load_active()
        emit(
            active.as_dict()
            if active is not None
            else {
                "schema_version": ("l9.pack-activation-pointer/v1"),
                "status": "none",
            }
        )
        return 0
    if arguments.command == "recover-state":
        emit(manager.recover())
        return 0

    if arguments.command in {
        "telemetry-health",
        "telemetry-deliver",
        "telemetry-delete-all",
    }:
        service = TelemetryService(
            paths=TelemetryPaths(paths),
            schema_root=schemas,
            client_name="cli",
            client_version="1",
            lsp_version="0.6.0",
        )
        if arguments.command == "telemetry-health":
            emit(service.health())
            return 0
        if arguments.command == "telemetry-deliver":
            import asyncio

            emit(asyncio.run(service.deliver_once()))
            return 0
        service.delete_all()
        emit(
            {
                "schema_version": "l9.telemetry-delete-result/v1",
                "status": "deleted",
            }
        )
        return 0
    if arguments.command == "verify-installed-pack":
        store = PackStore(
            packs_root=paths.packs,
            staging_root=paths.staging,
        )
        installed = store.verify_integrity(arguments.pack_id)
        emit(installed.as_dict())
        return 0
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
