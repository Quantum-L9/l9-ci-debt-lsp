# PR3 LSP Runbook

## Apply pack

```bash
cd /Users/ib-mac/Downloads/ci_trio_pr3_lsp_pack
bash apply_pr3_lsp_pack.sh /Users/ib-mac/Downloads/l9-ci-trio/l9-ci-debt-lsp
```

## Open PR

```bash
cd /Users/ib-mac/Downloads/l9-ci-trio/l9-ci-debt-lsp
git push -u origin wire/lsp-consume-compiled-rules
gh pr create --repo Quantum-L9/l9-ci-debt-lsp --base main --head wire/lsp-consume-compiled-rules --title "feat: consume intelligence compiled rules in LSP" --body-file PR_BODY.md
```

## Review loop

Accept immediately:

- CI permission failures
- validator/schema mismatches
- path/case mismatches
- security/secret leakage
- Linux or GitHub Actions failures

Reject or defer:

- style-only comments
- speculative architecture expansion
- cross-repo coupling
- PR_Repair, LLM-Router, SDK/Core, VSCE, npm publish, marketplace work

## Merge gate

Merge only after:

- local validation commands pass or CI equivalent passes
- Copilot actionable comments are resolved
- PR remains scoped to LSP consuming compiled Intelligence rules
