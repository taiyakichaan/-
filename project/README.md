# 旅行スポットおすすめ — 静的サイト版（Cloudflare Pages 向け）作業フォルダ

改修手順 1〜5（データ移行・正解データ・推薦ロジックの移植・トップ画面と入力画面の HTML 化・結果画面と各ページの移植）の成果物です。
元アプリの画面はすべて静的サイトで動きます（残りは Cloudflare Pages へのアップロード）。

## フォルダ構成
```
site/                 ← Cloudflare Pages にアップロードするフォルダ
  index.html          画面の土台（トップ → 条件設定 → 結果）
  css/vendor/         Gradio 6.31 のテーマ変数・共通 CSS（Apache-2.0。元アプリと同じ見た目の土台）
  css/gr.css          入力欄（スライダー等）の見た目。Gradio の部品と同じ値を静的 HTML 用に書いたもの
  css/app_a.css, app_b.css, mobile.css   app.py の CSS（extra.css を含む）を書き出したもの
  js/app.js           画面の組み立て・画面遷移・入力欄の動き（app.py の ui() / bridge_in() / on_load() / diagnose() を移植）
  js/pages.js         入力で中身が変わるページ: 結果・お気に入り・検索・スポットのホテル（_recommend / fav_page / search_page / hotel_page）
  js/head.js          元の HEAD のスクリプト（お気に入り★・絞り込み・折りたたみ・コピー）。export_ui.py が書き出す
  js/recommend.js     推薦ロジック（Python版 recommend() の数値部分を移植）
  js/plan.js          元の plan.js（そのまま）
  data/               model_*.json / spots_*.json / meta.json / ui.json / ui_<言語>.json / search.json / hotel_terms_*.json ＋ 元の data/*.json
  data/pages/<言語>/  元アプリが作るページの HTML（エリア一覧・エリアのホテル/レンタカー/交通・国全体のページ・イベント/準備は12か月分。計990ファイル）
  images/             元の images/ 252枚（構成そのまま）
  dev/check.html      ブラウザでの照合ページ（公開前に削除してよい）
tools/
  export_data.py      Python版 → site/data/ の推薦用 JSON
  export_ui.py        Python版 → 画面部品（HTML・CSS・文言）。site/css/app_*.css, site/data/ui*.json, site/js/plan.js, head.js
  export_pages.py     Python版 → 各ページの HTML（site/data/pages/）、ホテルのひな形・検索語、検索索引、結果画面用の文言
  make_golden.py      Python版で正解データ tests/golden.json を作る
  load_app.py         app.py を計算用に読み込む共通処理
  app_stable_sort.patch  app.py への修正（下記）
python_patched/app.py パッチ適用済みの app.py
tests/
  golden.json, test_recommend.mjs, test_pyfixed.mjs   推薦ロジックの照合（npm test）
  test_pages.py       結果・お気に入り・検索・ホテルの HTML が Python版と文字単位で同じか（ブラウザで pages.js を実行）
  visual_compare.py   元アプリと静的版の画面をスクリーンショットで比較（30場面）
  test_ui.py          静的版の動作テスト（遷移・戻る/進む・再読み込み・診断・お気に入り・検索・共有リンク など32項目）
```

## 使い方
```bash
# データ・モデル・文言・デザインを更新したら（元アプリのフォルダを指定。パッチ適用済みのもの）
python tools/export_data.py <元アプリ> site
python tools/export_ui.py    <元アプリ> site     # この順番で（export_pages が ui*.json に追記する）
python tools/export_pages.py <元アプリ> site
python tools/make_golden.py  <元アプリ> tests/golden.json 400
npm test        # JS版が Python版と一致するか（全件一致で終了コード0）

# 画面の確認（Playwright と Chrome が必要）
cd site && python -m http.server 8765          # 静的版。別の端末で元アプリも: cd <元アプリ> && PORT=7861 python app.py
python tests/test_pages.py <元アプリ>          # ページの HTML の照合
python tests/visual_compare.py --wait 5        # 見た目の比較（元アプリの描画が遅いことがあるので待ち時間を長めに）
python tests/test_ui.py <元アプリ>             # 動作テスト
```
画像の URL は `/images/...`（サイトのルートからの絶対パス）で書き出しています。カテゴリ画像を CSS 変数（`--ci:url(...)`）経由で
使っているため、相対パスだと CSS ファイル基準で解決されて表示されません。確認はサイトのルートで配信してください。

## 画面の作り方（手順4）
- 固定の HTML 部品（ヘッダーのメニュー、言語切替、使い方、見出し、地図、カテゴリ一覧、背景スライド）は、
  app.py の関数の出力を `export_ui.py` で書き出したものをそのまま表示します（文言・句点の改行も同じ）。
- 入力欄は Gradio と同じ構造・クラス名・インラインスタイルの HTML を `app.js` で作り、app.py の CSS がそのまま効くようにしています。
- 部品の中の `onclick="tjNav('…')"` は、元はサーバーへの通知でした。静的版では `app.js` の `tjNav` が受けて画面を切り替えます。
- 元アプリと同じにした挙動: ブラウザの言語・端末で初期表示 / 言語切替で予算欄をその通貨の初期値へ / 英語のときだけ通貨欄（切替で金額を換算）/
  背景が同じ画面では背景のスライドショーを作り直さない / `<html lang="en">`（元と同じ字形にするため）/ 共有リンク `?m=…&d=…` で結果を表示。

## 結果画面と各ページ（手順5）
- 入力によらず中身が決まるページは、Python版の出力を HTML ファイルとして書き出し、開いたときに読み込みます（data/pages/）。
  エリアページの「今月」の印（ベストシーズンの表）は、書き出した日の月のままにならないよう、ブラウザで今日の月に付け直します。
  イベントカレンダーと旅の準備は「今月」で表示が変わるので、12か月分を書き出して今月のものを読み込みます。
- 結果・お気に入り・検索・スポットのホテルは js/pages.js が Python版と同じ文字列を組み立てます（tests/test_pages.py で文字単位の一致を確認）。
  スポットの行は、書き出したエリアページの HTML から文字列のまま取り出して使います（行の中身は並び順の番号と追加部分以外は同じ）。
  ホテルの検索語は楽天・じゃらん用に EUC-JP で URL 符号化する必要があり、ブラウザではできないため、Python で計算した値を使います（hotel_terms_*.json）。
- 元アプリとの違い（意図的に直したもの）:
  - 結果画面の「この結果のリンクをコピー」は、元アプリでは plan.js の同名の関数 tjCopy に上書きされてエラーになり、動いていませんでした。静的版では動きます。
  - 結果画面で再読み込みすると、元アプリと同じく結果を表示し直します（入力値は sessionStorage に保存）。
- そのままにしたもの:
  - 天気は plan.js がブラウザから Open-Meteo に直接取りに行きます。元アプリにあった「サーバー経由の予備経路」（/gradio_api/run/wx）は
    静的サイトには無いので、その通信は失敗します（直接の取得が成功すれば表示に影響はありません）。
  - スポットごとのホテルページは、今の元アプリでは画面にボタンが無く開けませんが、合図（tjNav('hotel\t地域\tスポット')）は残っているので静的版にも用意しています。
`make_golden.py` は元の app.py を読み込むので、gradio・scikit-learn 1.9.1 などの requirements.txt と同じ環境が必要です。

## Python版 app.py への修正（必須）
`recommend()` の並べ替え4か所に `kind="stable"` を付けました（`tools/app_stable_sort.patch`）。
元の `sort_values()` は不安定ソートのため、**一致度が同点のスポットの並び順が numpy の内部実装任せ**になっていました
（CPU の種類や numpy のバージョンで変わりうる）。今回の826ケースでは全ケースに同点スポットがありました。
修正後は「同点は CSV の行順」で固定され、JS版も同じ規則で並べます。`region_page()` は元から stable です。

## Python版と一致させるための実装上の約束（js/recommend.js）
- スポットの分類（cat/ngen）や重複除外は移植せず、Python版が処理した後の表を JSON に書き出して使う
- POP（定番度）・base（平均的な旅行者）は Python で計算済みの値を使う
- 合計は numpy（pairwise）・pandas groupby（Kahan 補正）と同じ方法、丸めは Python と同じ偶数丸め
- 並べ替えはすべて安定ソート
