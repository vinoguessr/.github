@AGENTS.md

## Claude Code

このファイルはClaude CodeにAGENTS.mdを読み込ませるためのものです。規則の正本はAGENTS.mdで、ここに規則を重複して書きません。

Claude Codeは主に、Codexの利用上限（トークン不足）でGitHub上のレビューを得られないときの代替レビューに使います。代替レビューは、実装したエージェントとは別のコンテキストで`.claude/agents/reviewer.md`を起動し、Security Review対象の変更では`.claude/agents/security-reviewer.md`も起動します。Codexが使えなかった根拠・レビューしたcommit・指摘と対応をPRに記録します。
