# pyproject-template

This is a template for Python project repositories, intended for use by team members.

このテンプレートを使用する方法の詳細は、tutorialフォルダを参照してください。
なお、本リポジトリは`Require a pull request`を有効にしているため、`pull-request-manual`を参照しながら開発を行ってください。

tutorial

- `tutorial\manual.md` : このテンプレートを使用する際のマニュアル
- `tutorial\pull-request-manual.md` : 開発を行う際のマニュアル
- `tutorial\vscode-setup.md` : VScodeの拡張機能の設定
- `tutorial\env-setup.md` : pythonの仮想環境などの環境構築マニュアル

## 実行結果・ログの保存先

アプリケーションを `python run.py` で実行すると、設定ファイルの内容と実行環境を含むログが自動的に保存されます。

- 保存先: `Paths.output_folder/session_YYYYMMDD_HHMMSS_xxxxxx/`
- セッションフォルダー直下に、周縁減光補正・強調・抽出の各画像を保存
- サマリー画像と `.log`・`.json` の実行ログも同じ階層に保存
- セッション内に用途別のサブフォルダーは作成しません

ログには実行開始・終了時刻、処理時間、実行スクリプトと引数、作業ディレクトリ、OS・CPUアーキテクチャ、Python情報、主要依存パッケージのバージョン、実際に使用した設定、検出数、解析中のデバッグ情報を記録します。標準出力への解析情報の出力は行わず、`sunspot` ロガー経由でセッション `.log` ファイルに集約します。処理に失敗した場合は、例外の種類・メッセージ・スタックトレースも記録します。設定キーおよびコマンドライン引数内の `password`、`token`、`secret`、`api-key` などに該当する値はマスキングします。環境変数の値は記録しません。1回の実行で生成される画像・サマリー・ログはすべて同じセッションフォルダー直下に保存され、セッション内にサブフォルダーは作成されません。マスク処理では、選択した各 ROI の座標 `(x, y, width, height)`、画像サイズ、範囲のピクセル面積、画像全体に占める割合、領域ごとの重複候補数、マスク適用前後の候補数、除外した候補ラベルをイベントとして追記します。


### 黒点統計 CSV と最終確認画面

各セッションフォルダーに `sunspot_statistics.csv` と `sunspot_exclusion_list.csv` を出力します。`sunspot_statistics.csv` にはマスク適用後に残った黒点のラベル、重心座標、外接矩形の左上座標・幅・高さ、画素面積を記録します。`sunspot_exclusion_list.csv` にはマスクで除外された黒点について同じ幾何情報に加え、除外元のマスク番号と各マスクの座標・大きさを記録します。複数のマスクに重なった黒点は、該当するすべてのマスクを記録します。座標は画像左上を原点とした0始まりのピクセル座標です。

最終解析画像の対話的な確認は `Display.show_final_image: true` で有効化でき、PyQt ダイアログで表示します。
