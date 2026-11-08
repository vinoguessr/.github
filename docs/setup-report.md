# VinoGuessr 開発基盤の構築記録

[sauna-studio](https://github.com/sauna-studio/.github) と同じ構成への移行を記録します。完了した項目だけを完了として書き、未実施・未検証の項目は残件に書きます。

## 方針

- リポジトリ: `vinoguessr-api` / `vinoguessr-app` / `vinoguessr-web` に、`.github` / `vinoguessr-docs` / `vinoguessr-infrastructure` を追加する
- エージェント: Codexを前提にし、Codexの利用上限でレビューを得られないときだけClaude Codeのレビューで代替する
- Web: 技術スタックはSwift / Hummingbirdのまま変えない
- Google Cloud: 新しいプロジェクト `vinoguessr` は、この基盤とinfrastructureリポジトリを整えた後にIssueとPRの流れで構築する

## sauna-studio との違い

- 既存コードのある `vinoguessr-api` / `vinoguessr-web` には独自のCI（`ci.yml`）があるため、共通のRepository policy検査は `.github/workflows/repository.yml` から呼び出す
- ADRは `vinoguessr-docs` だけに置き、`.github` には複製しない
- Claude Codeの代替レビュー用に `CLAUDE.md` と `.claude/agents/` を各リポジトリへ配置する
- 管理者向けアプリ・Web、automationリポジトリは作らない

## 完了

まだありません。

## 残件

- `.github` / `vinoguessr-docs` / `vinoguessr-infrastructure` の作成
- 共通ファイルを各リポジトリへ配布するPR
- `bootstrap/provision.py` による Project・設定・Ruleset の適用
- Terraformをinfrastructureリポジトリへ移す
- Google Cloud プロジェクト `vinoguessr` の構築
