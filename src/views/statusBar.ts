import {
  ExtensionContext,
  StatusBarAlignment,
  StatusBarItem,
  window,
  workspace,
} from 'vscode';
import { LanguageClient, State } from 'vscode-languageclient/node';

let statusBarItem: StatusBarItem | undefined;

export function registerStatusBar(
  context: ExtensionContext,
  client: LanguageClient
): void {
  statusBarItem = window.createStatusBarItem(
    StatusBarAlignment.Right,
    100
  );

  statusBarItem.command = 'l9CiDebt.refreshCorpus';
  updateStatusBar(State.Starting);
  statusBarItem.show();

  client.onDidChangeState((event) => {
    updateStatusBar(event.newState);
  });

  context.subscriptions.push(statusBarItem);
}

function updateStatusBar(state: State): void {
  if (!statusBarItem) return;

  switch (state) {
    case State.Starting:
      statusBarItem.text = '$(sync~spin) L9 CI-Debt';
      statusBarItem.tooltip = 'L9 CI-Debt LSP: starting...';
      break;
    case State.Running:
      statusBarItem.text = '$(shield) L9 CI-Debt';
      statusBarItem.tooltip =
        'L9 CI-Debt LSP: active — click to refresh rules';
      break;
    case State.Stopped:
      statusBarItem.text = '$(warning) L9 CI-Debt';
      statusBarItem.tooltip = 'L9 CI-Debt LSP: stopped';
      break;
    default:
      statusBarItem.text = '$(question) L9 CI-Debt';
      statusBarItem.tooltip = 'L9 CI-Debt LSP: unknown state';
  }
}
