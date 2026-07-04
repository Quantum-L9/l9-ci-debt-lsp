import * as path from 'path';
import * as cp from 'child_process';
import { ExtensionContext, window, workspace, ProgressLocation, commands } from 'vscode';
import { LanguageClient } from 'vscode-languageclient/node';

export function registerRefreshCorpus(
  context: ExtensionContext,
  client: LanguageClient
): void {
  context.subscriptions.push(
    commands.registerCommand('l9CiDebt.refreshCorpus', async () => {
      const config = workspace.getConfiguration('l9CiDebt');
      const intelligenceOutputs = config.get<string>('intelligenceOutputsPath');

      if (!intelligenceOutputs) {
        window.showWarningMessage(
          'L9: Set l9CiDebt.intelligenceOutputsPath to enable rule refresh.'
        );
        return;
      }

      const rulesPath: string =
        config.get<string>('rulesPath') ||
        context.asAbsolutePath(path.join('rules', 'compiled_rules.json'));

      // Keep the lock beside the rules file so a custom rulesPath stays consistent.
      const lockPath = path.join(
        path.dirname(rulesPath),
        `${path.basename(rulesPath, '.json')}.lock.json`
      );

      const refreshScript = context.asAbsolutePath(
        path.join('server', 'refresh_rules.py')
      );

      await window.withProgress(
        {
          location: ProgressLocation.Notification,
          title: 'L9: Refreshing CI-debt rules from Intelligence...',
          cancellable: false,
        },
        () =>
          new Promise<void>((resolve, reject) => {
            const child = cp.spawn(
              'python',
              [
                refreshScript,
                '--intelligence-outputs',
                intelligenceOutputs,
                '--rules-out',
                rulesPath,
                '--lock-out',
                lockPath,
                '--expected-schema-version',
                '1.0',
                '--expected-artifact-name',
                'ci-debt-intelligence-compiled-rules',
              ],
              { shell: false }
            );

            let stdout = '';
            let stderr = '';
            child.stdout.on('data', chunk => {
              stdout += chunk.toString();
            });
            child.stderr.on('data', chunk => {
              stderr += chunk.toString();
            });
            child.on('error', err => {
              window.showErrorMessage(`L9 rule refresh failed: ${err.message}`);
              reject(err);
            });
            child.on('close', code => {
              if (code !== 0) {
                const message = stderr || stdout || `refresh_rules.py exited with ${code}`;
                window.showErrorMessage(`L9 rule refresh failed: ${message}`);
                reject(new Error(message));
                return;
              }
              client.sendNotification('l9/rulesRefreshed', { rulesPath, lockPath });
              window.showInformationMessage('L9: CI-debt rules refreshed and validated.');
              resolve();
            });
          })
      );
    })
  );
}
