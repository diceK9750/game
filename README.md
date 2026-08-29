# NUMBER RUSH

Pythonと[Pyxel](https://github.com/kitao/pyxel)で作った、反射神経を測る数字タップゲームです。
3×3にランダム配置された数字を、1から9まで順番にクリックまたはタップしてください。

## ブラウザで遊ぶ

公開ページ: https://dicek9750.github.io/game/

1. `START` をクリックまたはタップすると計測が始まります。
2. 1から9まで順番に押します。
3. 9を押すとクリアタイムが表示されます。
4. `PLAY AGAIN` を押すと、数字を並べ替えてもう一度遊べます。

間違ったマスを押すと、そのマスと案内メッセージが赤く表示されます。PCではマウス、スマートフォンではタッチで操作できます。

> 初回表示ではPyxelのWebランタイムを読み込むため、ゲーム開始まで少し時間がかかる場合があります。

## ローカルで起動する

### ブラウザ版（Pythonのインストール不要）

HTMLからPythonファイルを読み込むため、`index.html` を直接ダブルクリックするのではなく、ローカルWebサーバーを使います。

Python 3がインストール済みの場合、リポジトリのフォルダーで次を実行します。

```powershell
python -m http.server 8000
```

その後、ブラウザで http://localhost:8000/ を開いてください。ゲーム本体はブラウザ内で実行されるため、ローカルへのPyxelインストールは不要です。

### デスクトップ版

Python 3.11以降をインストールし、次を実行します。

```powershell
python -m pip install -r requirements.txt
python game.py
```

## GitHub Pagesへの公開

`.github/workflows/pages.yml` が、`main` ブランチへのpush時に自動でGitHub Pagesへ公開します。
初回だけ、GitHubリポジトリの **Settings → Pages → Build and deployment → Source** で **GitHub Actions** を選択してください。

## ファイル構成

- `game.py` — Pyxelで描画・入力・ゲーム進行を行うゲーム本体
- `game_logic.py` — 配置、正誤判定、タイム計測を担う独立したロジック
- `index.html` — Pyxel Webを読み込み、PC・スマートフォン向けに表示するページ
- `requirements.txt` — デスクトップ実行用のPyxelバージョン
- `tests/test_game_logic.py` — ゲーム進行の自動テスト
- `.github/workflows/pages.yml` — GitHub Pagesの自動公開設定

## テスト

ゲームロジックのテストには外部ライブラリは不要です。

```powershell
python -m unittest discover -s tests -v
```

## 技術メモ

- ブラウザ版はPyxel 2.9.8のWebランタイムをCDNから読み込みます。
- タイムはフレーム数ではなく単調増加時計で計測するため、描画の遅れが結果に混ざりにくい構成です。
- ゲーム盤は360×540の論理解像度で描画し、ブラウザ側で画面幅に合わせて縮小します。
