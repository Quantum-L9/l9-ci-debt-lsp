import * as path from 'path';
import * as fs from 'fs';
import {
  ExtensionContext,
  window,
  workspace,
  commands,
  Uri,
  env,
} from 'vscode';
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
  TransportKind,
} from 'vscode-languageclient/node';

import { registerStatusBar } from './views/statusBar';
import { registerRefreshCorpus } from './commands/refreshCorpus';
import { registerApplyQuickFix } from './commands/applyQuickFix';
import { registerOpenFindingDocs } from './commands/openFindingDocs';

let client: LanguageClient | undefined;

export async function activate(context: ExtensionContext): Promise<void> {
  const config = workspace.getConfiguration('l9CiDebt');

  // Resolve server.py path — prefer user config, fall back to bundled
  const serverPath: string =
    config.get<string>('serverPath') ||
    context.asAbsolutePath(path.join('server', 'server.py'));

  if (!fs.existsSync(serverPath)) {
    window.showErrorMessage(
      `L9 CI-Debt LSP: server.py not found at ${serverPath}. Set l9CiDebt.serverPath.`
    );
    return;
  }

  // Resolve compiled_rules.json
  const rulesPath: string =
    config.get<string>('rulesPath') ||
    context.asAbsolutePath(path.join('rules', 'compiled_rules.json'));

  const serverOptions: ServerOptions = {
    command: 'python',
    args: [serverPath, '--rules', rulesPath],
    transport: TransportKind.stdio,
  };

  const clientOptions: LanguageClientOptions = {
    documentSelector: [
      { scheme: 'file', language: 'yaml' },
      { scheme: 'file', language: 'python' },
      { scheme: 'file', language: 'toml' },
    ],
    synchronize: {
      fileEvents: workspace.createFileSystemWatcher(
        '**/{*.yml,*.yaml,*.py,pyproject.toml}'
      ),
    },
    outputChannelName: 'L9 CI-Debt LSP',
  };

  client = new LanguageClient(
    'l9CiDebtLsp',
    'L9 CI-Debt LSP',
    serverOptions,
    clientOptions
  );

  // Register commands
  registerRefreshCorpus(context, client);
  registerApplyQuickFix(context, client);
  registerOpenFindingDocs(context, client);

  // Register status bar
  registerStatusBar(context, client);

  await client.start();
}

export async function deactivate(): Promise<void> {
  if (client) {
    await client.stop();
  }
}
