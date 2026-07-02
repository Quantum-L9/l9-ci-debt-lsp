import { ExtensionContext, window, commands } from 'vscode';
import { LanguageClient } from 'vscode-languageclient/node';

/**
 * applyQuickFix is called by the VS Code code-action provider when the user
 * selects an L9 quick-fix suggestion. The actual workspace edit is computed
 * server-side and returned as a CodeAction with an embedded WorkspaceEdit,
 * so this command exists primarily as a named entry point for keybindings
 * and command-palette access.
 */
export function registerApplyQuickFix(
  context: ExtensionContext,
  _client: LanguageClient
): void {
  context.subscriptions.push(
    commands.registerCommand(
      'l9CiDebt.applyQuickFix',
      async (ruleId?: string, documentUri?: string) => {
        if (!ruleId || !documentUri) {
          // No arguments: inform user to use the lightbulb code-action menu
          window.showInformationMessage(
            'L9: Place cursor on a diagnostic and use the lightbulb (⌘.) to apply a quick fix.'
          );
          return;
        }
        // Execution path when invoked programmatically from a CodeAction
        // The WorkspaceEdit is already embedded in the CodeAction returned
        // by code_actions.py — VS Code applies it automatically.
        // This handler is a no-op for that path.
      }
    )
  );
}
