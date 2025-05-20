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

#### 3. search_by_attribute

キーワードと属性情報を指定してデータを検索、取得する

#### 4. get_data

 データIDを指定してデータの内容を取得する

#### 5. get_data_catalog

データカタログ、データセット情報を取得する

#### 6. get_prefecture_data

国土交通DPFで利用する都道府県コードとコードに対応する都道府県名の一覧を取得する

#### 7. get_municipality_data

国土交通DPFで利用する市区町村コードとコードに対応する市区町村名の一覧を取得する

## Claude Desktop での使用

Claude Desktop でMCPサーバーを追加して利用することができます。

1. Claude Desktop で設定画面を開きます

2. このMCPサーバーを追加します
```json
{
    "mcpServers": {
        "MLIT-DATA-PLATFORM-mcp": {
            "command": "/Users/***/.local/bin/uv",
            "args": [
                "--directory",
                "＜mlit-data-platform-mcp.pyが存在するディレクトリを絶対パスで指定＞"
                "run",
                "mlit-data-platform-mcp.py"
            ]
        }
    }
}
```

3. MCPのサーバーURLに http://localhost:3000 を入力します

4. 保存します

5. 接続します

## ライセンス

MIT

## 謝辞

このプロジェクトは、国土交通省の国土交通データプラットフォームAPIを利用しています。APIの提供に感謝いたします。
