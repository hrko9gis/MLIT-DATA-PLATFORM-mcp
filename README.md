# 国土交通データプラットフォーム MCP サーバー

国土交通省の国土交通データプラットフォームAPIを利用して、国土交通データを検索できるMCP（Model Context Protocol）サーバーです。

## 機能

- 条件を設定したデータの検索、取得
- データIDを元にデータを取得
- データカタログ、データセット情報の取得
- 都道府県コードとコードに対応する都道府県名の一覧の取得
- 市区町村コードとコードに対応する市区町村名の一覧の取得

## 利用可能なツール
#### 1. search

キーワードを指定してデータを検索、取得する

#### 2. search_by_location_rectangle

キーワードと緯度経度で範囲を指定してデータを検索、取得する

#### 3. search_by_location_point_distance

キーワードと中心の緯度経度、半径距離（メートル）を指定してデータを検索、取得する

#### 4. search_by_attribute

キーワードと属性情報を指定してデータを検索、取得する

#### 5. get_data_summary

データIDを指定してデータの概要情報のみを取得する

#### 6. get_data

データIDを指定してデータの詳細情報を取得する

#### 7. get_data_catalog

データカタログ、データセット情報を取得する

#### 8. get_prefecture_data

国土交通DPFで利用する都道府県コードとコードに対応する都道府県名の一覧を取得する

#### 9. get_municipality_data

国土交通DPFで利用する市区町村コードとコードに対応する市区町村名の一覧を取得する

## 依存関係

pip install aiohttp mcp

## 使い方（自分の環境で動作した手順）

ローカルにクローンして使用する場合：

```bash
# リポジトリをクローン
git clone https://github.com/hrko9gis/MLIT-DATA-PLATFORM-mcp.git
cd MLIT-DATA-PLATFORM-mcp

# Python仮想環境を使用
uv venv
.venv\Scripts\activate
pip install aiohttp mcp
```

## Claude Desktop での使用（パスが通っていれば、こちらで問題なく動作する見込み）

Claude Desktop でMCPサーバーを追加して利用することができます。

1. Claude Desktop で設定画面を開きます

2. このMCPサーバーを追加します
```json
{
    "mcpServers": {
        "MLIT-DATA-PLATFORM-mcp": {
            "command": "uv",
            "args": [
                "--directory",
                "＜mlit-data-platform-mcp.pyが存在するディレクトリを絶対パスで指定＞",
                "run",
                "mlit-data-platform-mcp.py"
            ]
        }
    }
}
```

3. 保存します

4. 接続します

## Claude Desktop での使用（自分の環境で動作した設定）
Claude Desktop でMCPサーバーを追加して利用することができます。

1. Claude Desktop で設定画面を開きます

2. このMCPサーバーを追加します
```json
{
    "mcpServers": {
        "MLIT-DATA-PLATFORM-mcp": {
            "command": "＜MLIT-DATA-PLATFORM-mcpのディレクトリを絶対パスで指定＞\\venv\\Scripts\\python.exe",
            "args": ["＜MLIT-DATA-PLATFORM-mcpのディレクトリを絶対パスで指定＞\\mlit-data-platform-mcp.py"]
        }
    }
}
```

3. 保存します

4. 接続します

## 必要な依存関係

pip install aiohttp mcp

## APIキー

- 国土交通データプラットフォーム利用者向けAPIキー（[API利用方法](https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApiApplication)を参照）

## ライセンス

MIT

## 謝辞

このプロジェクトは、国土交通省の国土交通データプラットフォームAPIを利用しています。APIの提供に感謝いたします。
