import * as vscode from "vscode";
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
  TransportKind,
} from "vscode-languageclient/node";
let client: LanguageClient | undefined;
export async function activate(
  context: vscode.ExtensionContext,
): Promise<void> {
  const configuration = vscode.workspace.getConfiguration(
    "l9CiDebt",
  );
  const pythonPath = configuration.get<string>(
    "server.pythonPath",
    "python3",
  );
  const serverModule = configuration.get<string>(
    "server.module",
    "l9_debt_lsp.server",
  );
  const serverOptions: ServerOptions = {
    command: pythonPath,
    args: ["-m", serverModule],
    transport: TransportKind.stdio,
  };
  const clientOptions: LanguageClientOptions = {
    documentSelector: [
      { scheme: "file", language: "python" },
      { scheme: "file", language: "yaml" },
      { scheme: "file", language: "toml" },
    ],
    synchronize: {
      configurationSection: "l9CiDebt",
    },
  };
  client = new LanguageClient(
    "l9CiDebt",
    "L9 CI Debt",
    serverOptions,
    clientOptions,
  );
  context.subscriptions.push(
    vscode.commands.registerCommand(
      "l9CiDebt.showServerCapabilities",
      async () => {
        if (client === undefined) {
          await vscode.window.showErrorMessage(
            "L9 CI Debt language server is not running.",
          );
          return;
        }
        const capabilities = await client.sendRequest(
          "l9/serverCapabilities",
          {},
        );
        const document = await vscode.workspace.openTextDocument({
          language: "json",
          content: JSON.stringify(capabilities, null, 2),
        });
        await vscode.window.showTextDocument(document);
      },
    ),
  );
  await client.start();
}
export async function deactivate(): Promise<void> {
  if (client !== undefined) {
    await client.stop();
    client = undefined;
  }
}
