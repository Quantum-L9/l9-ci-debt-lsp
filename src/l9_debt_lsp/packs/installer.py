from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from l9_debt_lsp.contracts.compatibility import (
    evaluate_compatibility,
)
from l9_debt_lsp.contracts.descriptor import (
    descriptor_from_defense_pack,
)

from .archive import extract_archive_safely
from .contents import (
    load_and_validate_defense_pack,
    load_checksums,
    validate_identity_consistency,
    validate_required_members,
    verify_member_checksums,
)
from .errors import (
    PackCompatibilityFailure,
    PackError,
)
from .jsonio import load_json
from .manifest import (
    load_and_validate_manifest,
    verify_archive_reference,
)
from .models import InstalledPack
from .paths import StatePaths
from .quarantine import QuarantineStore
from .retirement import RetirementRegistry
from .signature import verify_archive_digest
from .store import PackStore
from .trust import TrustRegistry


class PackInstaller:
    def __init__(
        self,
        *,
        paths: StatePaths,
        schema_root: Path,
    ) -> None:
        self.paths = paths
        self.schema_root = schema_root
        self.trust = TrustRegistry(
            paths.trusted_keys,
            schema_root / "trusted-key-registry.schema.json",
        )
        self.retirement = RetirementRegistry(
            paths.retired_packs,
            schema_root / "retired-pack-registry.schema.json",
        )
        self.store = PackStore(
            packs_root=paths.packs,
            staging_root=paths.staging,
        )
        self.quarantine = QuarantineStore(paths.quarantine)

    def install(
        self,
        *,
        manifest_path: Path,
        archive_path: Path,
        platform_identity: str | None = None,
    ) -> InstalledPack:
        self.paths.initialize()
        try:
            manifest = load_and_validate_manifest(
                manifest_path=manifest_path,
                schema_path=(self.schema_root / "publication-manifest.schema.json"),
            )
            archive_sha256 = verify_archive_reference(
                manifest=manifest,
                archive_path=archive_path,
            )
            trusted_key = self.trust.require_verification_key(
                key_id=manifest["signer_key_id"],
                embedded_public_key=manifest["public_key"],
            )
            verify_archive_digest(
                archive_sha256=archive_sha256,
                signature_base64=manifest["signature"],
                public_key_base64=trusted_key.public_key,
            )
            extraction_root = Path(
                tempfile.mkdtemp(
                    prefix=".extract-",
                    dir=self.paths.staging,
                )
            )
            extraction_root.rmdir()
            try:
                extract_archive_safely(
                    archive_path,
                    extraction_root,
                )
                validate_required_members(extraction_root)
                checksums = load_checksums(extraction_root)
                verified_hashes = verify_member_checksums(
                    extraction_root,
                    checksums,
                )
                defense_pack = load_and_validate_defense_pack(
                    root=extraction_root,
                    schema_path=(
                        self.schema_root / "defense-pack-consumer.schema.json"
                    ),
                )
                validate_identity_consistency(
                    manifest=manifest,
                    defense_pack=defense_pack,
                )
                compatibility = load_json(extraction_root / "compatibility.json")
                descriptor = descriptor_from_defense_pack(defense_pack)
                compatibility_result = evaluate_compatibility(
                    descriptor=descriptor,
                    compatibility=compatibility,
                    platform_identity=platform_identity,
                )
                if compatibility_result.status != "compatible":
                    raise PackCompatibilityFailure(
                        "; ".join(compatibility_result.limitations)
                    )
                self.retirement.require_not_retired(
                    pack_id=defense_pack["pack_id"],
                    pack_version=defense_pack["version"],
                )
                return self.store.install(
                    extracted_root=extraction_root,
                    manifest=manifest,
                    defense_pack=defense_pack,
                    manifest_path=manifest_path,
                    archive_sha256=archive_sha256,
                    signer_key_id=trusted_key.key_id,
                    content_hashes=verified_hashes,
                    limitations=list(compatibility_result.limitations),
                )
            finally:
                shutil.rmtree(
                    extraction_root,
                    ignore_errors=True,
                )
        except PackError as error:
            self.quarantine.record(
                reason_code=type(error).__name__,
                reason=str(error),
                manifest_path=manifest_path,
                archive_path=archive_path,
            )
            raise
        except Exception as error:
            self.quarantine.record(
                reason_code="unexpected_installation_failure",
                reason=str(error),
                manifest_path=manifest_path,
                archive_path=archive_path,
            )
            raise
