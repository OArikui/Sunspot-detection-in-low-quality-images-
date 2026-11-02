# pyproject-template

This is a template for Python project repositories, intended for use by team members.

このテンプレートを使用する方法の詳細は、tutorialフォルダを参照してください。
なお、本リポジトリは`Require a pull request`を有効にしているため、`pull-request-manual`を参照しながら開発を行ってください。

tutorial

- `tutorial\manual.md` : このテンプレートを使用する際のマニュアル
- `tutorial\pull-request-manual.md` : 開発を行う際のマニュアル
- `tutorial\vscode-setup.md` : VScodeの拡張機能の設定
- `tutorial\env-setup.md` : pythonの仮想環境などの環境構築マニュアル

## 実行ログ

アプリケーションを `python run.py` で実行すると、設定ファイルの内容と実行環境を含むログが自動的に保存されます。

- 保存先: `results/logs/`（`Paths.output_folder` の直下）
- `run_YYYYMMDD_HHMMSS_xxxxxx.log`: 人が確認しやすいテキスト形式
- `run_YYYYMMDD_HHMMSS_xxxxxx.json`: 後から解析しやすい JSON 形式

ログには実行開始・終了時刻、処理時間、実行スクリプトと引数、作業ディレクトリ、OS・CPUアーキテクチャ、Python情報、主要依存パッケージのバージョン、実際に使用した設定、検出数を記録します。処理に失敗した場合は、例外の種類・メッセージ・スタックトレースも記録します。設定キーおよびコマンドライン引数内の `password`、`token`、`secret`、`api-key` などに該当する値はマスキングします。環境変数の値は記録しません。
