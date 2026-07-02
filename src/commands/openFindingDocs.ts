import { ExtensionContext, commands, env, Uri, window } from 'vscode';
import { LanguageClient } from 'vscode-languageclient/node';

/**
 * Map rule IDs to their canonical documentation anchors in the resolver repo.
 * Source of truth: cryptoxdog/l9-ci-debt-resolver/references/classification-rules.md
 */
const RULE_DOC_ANCHORS: Record<string, string> = {
  'CI-IMPORT-001':
    'https://github.com/cryptoxdog/l9-ci-debt-resolver/blob/main/references/classification-rules.md#p-001-pythonpath-missing-in-ci-job',
  'CI-DEPS-001':
    'https://github.com/cryptoxdog/l9-ci-debt-resolver/blob/main/references/classification-rules.md#p-002-runtime-dependency-missing-from-pyprojecttoml',
  'CI-DEPS-002':
    'https://github.com/cryptoxdog/l9-ci-debt-resolver/blob/main/references/classification-rules.md#p-003-ci-job-missing-install-step',
  'API-DRIFT-001':
    'https://github.com/cryptoxdog/l9-ci-debt-resolver/blob/main/references/classification-rules.md#p-004-source-file-missing-exported-symbol',
  DOCTRINE:
    'https://github.com/cryptoxdog/l9-ci-debt-resolver/blob/main/references/classification-rules.md#doctrine-violation-response',
};

export function registerOpenFindingDocs(
  context: ExtensionContext,
  _client: LanguageClient
): void {
  context.subscriptions.push(
    commands.registerCommand(
      'l9CiDebt.openFindingDocs',
      async (ruleId?: string) => {
        if (!ruleId) {
          const picked = await window.showQuickPick(
            Object.keys(RULE_DOC_ANCHORS),
            { placeHolder: 'Select a rule to open its documentation' }
          );
          if (!picked) return;
          ruleId = picked;
        }

        const url = RULE_DOC_ANCHORS[ruleId];
        if (!url) {
          window.showWarningMessage(
            `L9: No documentation registered for rule ${ruleId}.`
          );
          return;
        }

        await env.openExternal(Uri.parse(url));
      }
    )
  );
}
