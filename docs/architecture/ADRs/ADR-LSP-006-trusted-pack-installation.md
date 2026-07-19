# ADR-LSP-006: Defense packs are untrusted until fully verified
- Status: Accepted
- Phase: LSP-P1
## Decision
Downloaded defense-pack artifacts are treated as hostile input.
Installation requires:
1. manifest schema validation;
2. trusted signer resolution;
3. archive SHA-256 validation;
4. Ed25519 signature verification;
5. bounded archive inspection;
6. safe extraction;
7. member checksum verification;
8. defense-pack schema validation;
9. compatibility validation;
10. retirement validation.
No failed artifact can modify active or previous-known-good state.
