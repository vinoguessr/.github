# VinoGuessr · Organization foundation

ワインのブラインドテイスティングを、イベントの作成・出題・回答・採点・シーズンレーティングで楽しめるサービスです。

このリポジトリは共通開発規則、Organizationプロフィール、Issue Forms、PRテンプレート、Reusable Workflows、Codex・Claude Codeのエージェント定義の正本です。

| Repository | Responsibility |
| --- | --- |
| [vinoguessr-api](https://github.com/vinoguessr/vinoguessr-api) | Swift 6 / Hummingbird / PostgreSQL / PostgresNIO / Valkey / Atlas / OpenAPI |
| [vinoguessr-app](https://github.com/vinoguessr/vinoguessr-app) | 利用者向け SwiftUI / iOS・iPadOS・macOS 27.0以上 |
| [vinoguessr-web](https://github.com/vinoguessr/vinoguessr-web) | 利用者向け Web / Swift・Hummingbird |
| [vinoguessr-infrastructure](https://github.com/vinoguessr/vinoguessr-infrastructure) | Terraform / Google Cloud Run / Cloudflare / OpenTelemetry |
| [vinoguessr-docs](https://github.com/vinoguessr/vinoguessr-docs) | 設計書 / ADR / Wiki |
| [.github](https://github.com/vinoguessr/.github) | 共通設定・テンプレート・Actions |

ログインはPasskeyとメールのワンタイムコードです。ユーザー・イベント・問題・回答・採点の正本はVinoGuessr APIとPostgreSQLです。

開発前に [AGENTS.md](AGENTS.md) と [CONTRIBUTING.md](CONTRIBUTING.md) を読み、Issueの依存関係を満たしてからブランチとPRで変更します。実装中は独立Review Agentを並行起動します。レビューはGitHubのCodexで行い、Codexの利用上限でレビューを得られないときだけClaude Codeのレビューで代替します（[レビュー方針](policies/github-codex-review.md)）。

共通ファイルは自動継承されるとは限りません。`AGENTS.md`・`CLAUDE.md`・CODEOWNERS・CI・ライセンスは各リポジトリに明示配置し、共通規則の改訂時は追従PRで更新します。Reusable Workflowはレビュー済みのコミットSHAを指定して呼び出します。

SwiftUIを実装する`vinoguessr-app`には、[専用指針](policies/swiftui.md)の本文と適用元commitをAGENTSへ明示配置します。この指針は文書だけでUI動作・性能検証を完了扱いにしません。

この構成は [sauna-studio/.github](https://github.com/sauna-studio/.github) を基にしています。

ローカル検証（Python 3.11以上を使用。macOS標準Pythonが古い場合はHomebrew等のPythonを明示指定）:

```sh
python3 -m venv /tmp/vinoguessr-foundation-venv
/tmp/vinoguessr-foundation-venv/bin/pip install -r scripts/validation-requirements.txt
/tmp/vinoguessr-foundation-venv/bin/python scripts/validate_repository.py
/tmp/vinoguessr-foundation-venv/bin/python -m unittest discover -s scripts -p 'test_*.py'
actionlint
```

これは本番デプロイや課金リソース作成を行うリポジトリではありません。GitHub上の設定の適用には [bootstrap/provision.py](bootstrap/provision.py) を使い、結果と未完了事項は [docs/setup-report.md](docs/setup-report.md) に残します。

- [Workflow dependency lockfiles](policies/workflow-lockfiles.md): generated coverage and provenance verification alongside existing SHA pins.
