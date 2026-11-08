# VinoGuessr — 共通エージェント規則

共通規則の正本: `vinoguessr/.github/AGENTS.md`。各リポジトリにはこの規則の実効的なコピーと固有の検証コマンドを配置する。リンクだけで規則が継承されると判断しない。

## 目的・アーキテクチャ

ワインのブラインドテイスティングを、イベントの作成・出題・回答・採点・シーズンレーティングで楽しめるサービスを開発する。ユーザー・イベント・問題・回答・採点などの業務データはVinoGuessr API / PostgreSQLを正本とし、外部サービスを正本にしない。

API: Swift 6 / Hummingbird / PostgreSQL / PostgresNIO / Valkey / Atlas / OpenAPI。Apple: SwiftUI、iOS・iPadOS・macOS 27.0以上。Web: Swift / Hummingbird。基盤: Terraform / Google Cloud Run / Cloudflare（DNS・Images・Email）/ Docker / OpenTelemetry。最新安定版OS・ブラウザを対象とし、不要な後方互換分岐を追加しない。

ログインはPasskey / WebAuthnとメールのワンタイムコードで行う。セッションはAPIが発行するトークンで扱い、クライアントが送る利用者IDやイベント参加状態を信用しない。画像はCloudflare Images、イベント参加証はApple Walletパスで提供する。

## 実装フローと役割

1. Issue、受け入れ条件、Sub-issues、Dependencies、既存PRとADRを読み、重複とブロッカーを確認する。
2. 実装計画を作る。Coding Agentが実装している間は、独立したReview Agentを必ず並行起動する。別コンテキストのレビューを用い、実装者自身の再読だけで代用しない。
3. 認証（Passkey・メールのワンタイムコード・トークン）・個人情報・イベントの参加権限・採点結果の改ざん防止・Apple Walletパスの署名を変更する場合はSecurity Review Agentも並行起動する。Bug Triage Agentは再現・重複確認、Tool Review AgentはMCP・Skills・CIの権限と実行安全性を確認する。
4. 指摘を修正し、実際にビルド・テスト・必要な動作検証を実行する。AIレビューのみで合格にしない。バグは重複を調べて必要ならIssueを作成し、回帰テストを追加する。
5. 再レビュー後、GitHub Actionsの成功を確認し、PRに実装内容・検証・レビュー結果・未解決事項を記録する。未実行チェックを成功と表現しない。

並行エージェントが利用できない場合はその制約を記録し、レビュー条件を満たすまでマージしない。レビューは自動でGitHubの承認票になるわけではない。

## コーディング・テスト

既存構成を尊重し、小さいIssue単位の変更にする。Swiftの並行性はSwift 6の検査を有効にし、無根拠な`@unchecked Sendable`やエラー握り潰しを避ける。公開APIはOpenAPIで契約を明示し、生成物を手編集しない。DB変更はAtlasのバージョン管理されたforward-only migrationと統合テストを伴う。

APIは`swift build` / `swift test`とPostgreSQL・Valkeyを使う統合テスト、Atlas migrationの検証、Webは`swift build` / `swift test`、Appleは対象Xcodeでbuild/testと必要なSimulator動作確認、Terraformはfmt / init -backend=false / validateを実行する。コード未配置の基盤PRは構造検査だけを実行し、アプリ検証済みと記録しない。

`.github`リポジトリで共通基盤を変更するときの検証は`python scripts/validate_repository.py`（Python 3.11以上、`scripts/validation-requirements.txt`を使用）、`python -m unittest discover -s scripts -p 'test_*.py'`、`actionlint`。他のリポジトリでは末尾の固有指針とREADMEにある実在する検証手順を使う。Reusable Workflowsは呼出先の実コード・lockfile・テストが存在してから有効化する。

## 記述の責務

- **コードには How**：実装方法をコードの構造・名前・処理で表現する。
- **テストコードには What**：期待する振る舞いと保証する結果を示す。
- **コミットログには Why**：変更が必要な理由と解決する問題を記録する。
- **コードコメントには Why not**：代替案を採用しない理由と必要な制約を説明する。

## ワークアラウンドの追跡

不具合・制約を暫定的に回避する実装や運用を導入した場合は、関連Issueの重複を確認し、既存Issueへ追記するか、無ければ追跡Issueを作成する。恒久的な設計や妥当な設定を、根拠なく暫定対処と扱わない。

追跡Issueには導入理由、影響範囲、該当コード・PR、恒久対応案、解消・削除条件、上流Issue/PR（該当する場合）、再確認の契機、回帰検証を記録する。必要なコード箇所にはWhy notコメントで制約とIssue参照を残し、導入PRからも追跡Issueを参照する。

導入PRでは追跡Issueを自動closeする記法を使わず参照する。恒久対応または回避策が不要になったことを、解消条件と回帰検証で確認してから追跡Issueを閉じる。

## セキュリティ

Secrets、トークン、個人情報、実利用者データをコード・ログ・Issue・PRに残さない。認証情報の値を出力しない。Passkeyはchallenge・origin・RP IDの対応を検証し、ワンタイムコードとトークン発行には試行回数制限をかける。イベントの参加権限と回答・採点の書き込みは信頼できるセッションからAPIで検証し、採点結果をクライアントの値で確定しない。Apple Walletパスの署名鍵・証明書（`.p12`・`.p8`など）をリポジトリに置かない。

課金リソースの作成・本番デプロイ・`terraform apply`・広いIAM付与は明示承認を得る。OpenTelemetryにPII・認証情報を含めない。Workflowは最小permissions、外部Actionsは完全なcommit SHA固定。共通Reusable WorkflowのSHAはdefault branch履歴上に保持されたcommitを使い、未merge branchのSHAを使わない。checkoutの資格情報を永続化しない。PRの未信頼コードを`pull_request_target`で実行しない。

## MCP・Skills

開始時に実際に利用可能なMCP・Skills・CLIを確認する。GitHub CLI、PostgreSQL・Atlas、Xcode MCP・Simulator・SwiftUI Expert・Swift Build、Terraform・gcloudを目的に応じて使う。公式導入方法と利用条件を検証してからローカル導入する。システム設定・認証・権限を無断で拡大しない。接続できないものは代替コマンドと未検証項目を記録する。インストール済みと利用済みを区別する。

## GitHub運用とドキュメント

`codex/`ブランチとPRを使い、`main`へ直接pushしない。既存変更・リポジトリ・ライセンスを上書きしない。必要なGitHub Issues/Projectsへの更新以外の他者宛メッセージは明示指示がない限り送信しない。Issueは横断Projectへ追加し、受け入れ条件と実際の依存関係を記録する。秘密の脆弱性は公開Issueで扱わずSECURITY.mdに従う。

PRには関連Issue、何が変わるか、実行したチェックと結果、独立Review/Security Reviewの結果、既知の制限を記録する。required checksをskipで満たしたように装わない。Releasesはテスト済みcommitと変更点を持ち、Environmentsは開発・検証・本番の承認境界を分ける。Packagesは配布の必要が生じたときだけ使う。

重要な設計変更は`vinoguessr-docs`のADRに背景・決定・代替案・影響を残し、Wikiに索引を反映する。繰り返すバグや重要なレビュー指摘は必要に応じてこの規則と各repoのAGENTS.mdを更新する。共通規則の更新は他repoへの追従PRを作り、適用元のcommitを明示する。

## コードレビューとマージ条件

1. PRの自動Codexレビューを確認する。指摘ごとに根拠を確認し、必要なコード修正・回帰テストを行う。
2. 各レビューthreadに、修正内容・commit・検証結果を返信する。対応不要と判断した場合も理由を説明し、未解決事項を隠さない。
3. 対応後にPRへ正確に `@codex review` とコメントし、新しいレビューを依頼する。最新commitに対するレビュー結果を待つ。
4. 新しい指摘があれば同じ処理を繰り返す。GitHubのCodexが指摘なしと示し、未対応の指摘がなく、必須CIが成功した後だけマージする。
5. レビュー未着・連携未設定・実行失敗は指摘なしと見なさない。原因と依頼URLを記録し、PRを開いたままにする。

**Codexの利用上限（トークン不足）でレビューを得られない場合に限り、Claude Codeの独立レビューで代替できる。** 代替するときは次を守る。

- 実装したエージェントとは別のコンテキストで、Claude Codeの`reviewer`エージェント（`.claude/agents/reviewer.md`）を最新commitに対して起動する。手順3のSecurity Review対象の変更では`security-reviewer`も起動する。
- Codexが使えなかった根拠（上限の表示・依頼したコメントのURL）、レビューしたcommit、指摘と対応をPRに記録する。
- 指摘を修正したら、最新commitに対して再度レビューし、指摘がなくなり必須CIが成功してからマージする。

このGitHub上のレビューは、実装中の独立Review Agent並行起動と実ビルド・テストに追加する確認である。レビュー依頼だけで成功扱いにしない。自動返信・同じ依頼の連投を避け、レビューroundと対象commitをPRへ記録する。
