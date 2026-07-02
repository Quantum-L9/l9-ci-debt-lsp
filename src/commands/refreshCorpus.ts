import * as path from 'path';
import * as cp from 'child_process';
import { ExtensionContext, window, workspace, ProgressLocation } from 'vscode';
import { LanguageClient } from 'vscode-languageclient/node';

export function registerRefreshCorpus(
  context: ExtensionContext,
  client: LanguageClient
): void {
  context.subscriptions.push(
    workspace
      .getConfiguration
      ? require('vscode').commands.registerCommand(
          'l9CiDebt.refreshCorpus',
          async () => {
            const config = workspace.getConfiguration('l9CiDebt');
            const intelligenceOutputs = config.get<string>(
              'intelligenceOutputsPath'
            );

            if (!intelligenceOutputs) {
              window.showWarningMessage(
                'L9: Set l9CiDebt.intelligenceOutputsPath to enable corpus refresh.'
              );
              return;
            }

            const rulesPath: string =
              config.get<string>('rulesPath') ||
              context.asAbsolutePath(
                path.join('rules', 'compiled_rules.json')
              );

            const compilerScript = context.asAbsolutePath(
              path.join('server', 'corpus_compiler.py')
            );

            await window.withProgress(
              {
                location: ProgressLocation.Notification,
                title: 'L9: Refreshing CI-debt rules...',
                cancellable: false,
              },
              () =>
                new Promise<void>((resolve, reject) => {
                  cp.exec(
                    `python "${compilerScript}" --intelligence-outputs "${intelligenceOutputs}" --out "${rulesPath}"`,
                    (err, stdout, stderr) => {
                      if (err) {
                        window.showErrorMessage(
                          `L9 corpus refresh failed: ${stderr || err.message}`
                        );
                        reject(err);
                      } else {
                        // Notify server to reload rules
                        client.sendNotification('l9/rulesRefreshed', {
                          rulesPath,
                        });
                        window.showInformationMessage(
                          'L9: CI-debt rules refreshed successfully.'
                        );
                        resolve();
                      }
                    }
                  );
                })
            );
          }
        )
      : require('vscode').commands.registerCommand(
          'l9CiDebt.refreshCorpus',
          () => {}
        )
  );
}
