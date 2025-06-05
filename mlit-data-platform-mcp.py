"""
MLIT DATA PLATFORM MCP Server
"""

import os
import aiohttp
import asyncio
import json
import logging
from typing import Optional, Dict, Any, List

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
import mcp.types as types

# 環境変数からAPIキーを取得（デフォルト値は開発用）
END_POINT = "https://www.mlit-data.jp/api/v1/"
API_KEY = os.getenv("MLIT_API_KEY", "aXk6a-d10rH5rd-9Yq4_2EYiwFkah7U~")

server = Server("MLIT-DATA-PLATFORM-mcp")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 最小限のフィールドセット定義
MINIMAL_SEARCH_FIELDS = """
    id
    title
    lat
    lon
    dataset_id
"""

BASIC_SEARCH_FIELDS = """
    id
    title
    lat
    lon
    year
    dataset_id
    catalog_id
"""

DETAILED_DATA_FIELDS = """
    id
    title
    lat
    lon
    year
    theme
    metadata
    dataset_id
    catalog_id
    hasThumbnail
"""

async def post_query(query_contents: str, query_name: str) -> List[Dict[str, Any]]:
    """
    GraphQLクエリを実行する - 最適化版
    
    Args:
        query_contents: GraphQLクエリ文字列
        query_name: レスポンスから取得するデータのキー名
    
    Returns:
        クエリ結果のリスト
    """
    headers = {
        "Content-type": "application/json",
        "apikey": API_KEY,
        "Accept-Encoding": "gzip, deflate"  # 圧縮を有効化
    }
    
    data = {"query": query_contents}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                END_POINT,
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=30),
                compress=True  # リクエスト圧縮を有効化
            ) as response:
                response.raise_for_status()
                result_data = await response.json()
                
                if "data" not in result_data:
                    logger.error("Unexpected response structure: missing 'data' field")
                    return []
                    
                if query_name not in result_data["data"]:
                    logger.error(f"Query name '{query_name}' not found in response")
                    return []
                    
                result = result_data["data"][query_name]
                return result if result else []
                
    except aiohttp.ClientError as e:
        logger.error(f"HTTP request error: {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return []
    except KeyError as e:
        logger.error(f"Key error in response: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []

def build_search_query(
    term: str = "",
    first: int = 1,
    size: int = 50,  # デフォルトサイズを削減
    sort_attribute_name: str = "",
    sort_order: str = "",
    location_filter: Optional[str] = None,
    attribute_filter: Optional[str] = None,
    fields: str = BASIC_SEARCH_FIELDS,  # 取得フィールドを指定可能に
    minimal: bool = False  # 最小限のフィールドのみ取得オプション
) -> str:
    """
    検索用GraphQLクエリを構築する - 最適化版
    """
    # パラメータの検証と最適化
    if not isinstance(first, int) or first < 1:
        first = 1
    if not isinstance(size, int) or size < 1:
        size = 50
    if size > 500:  # 上限を500に制限
        size = 500
    
    # 最小限モードの場合は基本フィールドのみ
    if minimal:
        fields = MINIMAL_SEARCH_FIELDS
    
    # エスケープ処理と空文字チェック
    query_parts = []
    
    # termが空でない場合のみ追加
    if term and term.strip():
        escaped_term = term.replace('"', '\\"')
        query_parts.append(f'term: "{escaped_term}"')
    
    query_parts.extend([
        f'first: {first}',
        f'size: {size}'
    ])
    
    # その他のパラメータも空文字チェック
    if sort_attribute_name and sort_attribute_name.strip():
        escaped_sort_attr = sort_attribute_name.replace('"', '\\"')
        query_parts.append(f'sortAttributeName: "{escaped_sort_attr}"')
    if sort_order and sort_order.strip():
        escaped_sort_order = sort_order.replace('"', '\\"')
        query_parts.append(f'sortOrder: "{escaped_sort_order}"')
    if location_filter:
        query_parts.append(location_filter)
    if attribute_filter:
        query_parts.append(attribute_filter)
    
    query = f"""
        query {{
            search({', '.join(query_parts)}) {{
                searchResults {{
                    {fields}
                }}
            }}
        }}
    """
    
    return query

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    利用可能なツールのリストを返す - 最適化版
    """
    return [
        types.Tool(
            name="search",
            description="基本検索を実行します（最適化版）",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "検索キーワード"},
                    "first": {"type": "integer", "description": "開始位置", "default": 1},
                    "size": {"type": "integer", "description": "取得件数（最大500）", "default": 50},
                    "sort_attribute_name": {"type": "string", "description": "ソート属性名"},
                    "sort_order": {"type": "string", "description": "ソート順序"},
                    "minimal": {"type": "boolean", "description": "最小限のフィールドのみ取得", "default": False}
                }
            }
        ),
        types.Tool(
            name="search_by_location_rectangle",
            description="矩形範囲での検索を実行します（最適化版）",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "検索キーワード"},
                    "first": {"type": "integer", "description": "開始位置", "default": 1},
                    "size": {"type": "integer", "description": "取得件数（最大500）", "default": 50},
                    "sort_attribute_name": {"type": "string", "description": "ソート属性名"},
                    "sort_order": {"type": "string", "description": "ソート順序"},
                    "prefecture_code": {"type": "string", "description": "都道府県コード"},
                    "location_rectangle_top_left_lat": {"type": "number", "description": "左上緯度"},
                    "location_rectangle_top_left_lon": {"type": "number", "description": "左上経度"},
                    "location_rectangle_bottom_right_lat": {"type": "number", "description": "右下緯度"},
                    "location_rectangle_bottom_right_lon": {"type": "number", "description": "右下経度"},
                    "minimal": {"type": "boolean", "description": "最小限のフィールドのみ取得", "default": False}
                },
                "required": ["location_rectangle_top_left_lat", "location_rectangle_top_left_lon", 
                           "location_rectangle_bottom_right_lat", "location_rectangle_bottom_right_lon"]
            }
        ),
        types.Tool(
            name="search_by_location_point_distance",
            description="地点距離での検索を実行します（最適化版）",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "検索キーワード"},
                    "first": {"type": "integer", "description": "開始位置", "default": 1},
                    "size": {"type": "integer", "description": "取得件数（最大500）", "default": 50},
                    "sort_attribute_name": {"type": "string", "description": "ソート属性名"},
                    "sort_order": {"type": "string", "description": "ソート順序"},
                    "prefecture_code": {"type": "string", "description": "都道府県コード"},
                    "location_lat": {"type": "number", "description": "緯度"},
                    "location_lon": {"type": "number", "description": "経度"},
                    "location_distance": {"type": "number", "description": "距離"},
                    "minimal": {"type": "boolean", "description": "最小限のフィールドのみ取得", "default": False}
                },
                "required": ["location_lat", "location_lon", "location_distance"]
            }
        ),
        types.Tool(
            name="search_by_attribute",
            description="属性による検索を実行します（最適化版）",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "検索キーワード"},
                    "first": {"type": "integer", "description": "開始位置", "default": 1},
                    "size": {"type": "integer", "description": "取得件数（最大500）", "default": 50},
                    "sort_attribute_name": {"type": "string", "description": "ソート属性名"},
                    "sort_order": {"type": "string", "description": "ソート順序"},
                    "prefecture_code": {"type": "string", "description": "都道府県コード"},
                    "municipality_code": {"type": "string", "description": "市区町村コード"},
                    "address": {"type": "string", "description": "住所"},                    
                    "catalog_id": {"type": "string", "description": "カタログID"},
                    "dataset_id": {"type": "string", "description": "データセットID"},
                    "minimal": {"type": "boolean", "description": "最小限のフィールドのみ取得", "default": False}
                }
            }
        ),
        types.Tool(
            name="get_data_summary",
            description="データの概要情報のみを取得します（軽量版）",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "string", "description": "データセットID"},
                    "data_id": {"type": "string", "description": "データID"}
                },
                "required": ["dataset_id", "data_id"]
            }
        ),
        types.Tool(
            name="get_data",
            description="データの詳細情報を取得します",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "string", "description": "データセットID"},
                    "data_id": {"type": "string", "description": "データID"}
                },
                "required": ["dataset_id", "data_id"]
            }
        ),
        types.Tool(
            name="get_data_catalog_summary",
            description="データカタログの概要のみを取得します（軽量版）",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="get_prefecture_data",
            description="都道府県データを取得します",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="get_municipality_data",
            description="市区町村データを取得します",
            inputSchema={
                "type": "object",
                "properties": {
                    "pref_code": {"type": "string", "description": "都道府県コード"}
                },
                "required": ["pref_code"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """
    ツール呼び出しのハンドラー - 最適化版
    """
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    
    try:
        result = ""
        
        if name == "search":
            result = await search(**arguments)
        elif name == "search_by_location_rectangle":
            result = await search_by_location_rectangle(**arguments)
        elif name == "search_by_location_point_distance":
            result = await search_by_location_point_distance(**arguments)
        elif name == "search_by_attribute":
            result = await search_by_attribute(**arguments)
        elif name == "get_data_summary":
            result = await get_data_summary(**arguments)
        elif name == "get_data":
            result = await get_data(**arguments)
        elif name == "get_data_catalog_summary":
            result = await get_data_catalog_summary()
        elif name == "get_prefecture_data":
            result = await get_prefecture_data()
        elif name == "get_municipality_data":
            result = await get_municipality_data(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        # 結果が文字列であることを確認
        if not isinstance(result, str):
            logger.warning(f"Result is not string, converting: {type(result)}")
            result = str(result)
        
        # レスポンスサイズを制限（1MB制限）
        if len(result.encode('utf-8')) > 1024 * 1024:
            logger.warning(f"Response size too large, truncating")
            result = result[:1024*1024//2] + "\n... [Response truncated due to size limit]"
        
        logger.info(f"Tool {name} completed successfully")
        return [types.TextContent(type="text", text=result)]
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        error_msg = f"Error executing {name}: {str(e)}"
        return [types.TextContent(type="text", text=error_msg)]

async def search(
    term: str = "",
    first: int = 1,
    size: int = 50,
    sort_attribute_name: str = "",
    sort_order: str = "",
    minimal: bool = False
) -> str:
    """基本検索 - 最適化版（termの空文字チェック追加）"""
    graph_ql_query = build_search_query(
        term=term,
        first=first,
        size=size,
        sort_attribute_name=sort_attribute_name,
        sort_order=sort_order,
        minimal=minimal
    )
    
    result = await post_query(graph_ql_query, 'search')
    
    # コンパクトなJSON出力（インデントなし）
    return json.dumps(result, ensure_ascii=False, separators=(',', ':'))

async def search_by_location_rectangle(
    term: str = "",
    first: int = 1,
    size: int = 50,
    sort_attribute_name: str = "",
    sort_order: str = "",
    prefecture_code: str = "",
    location_rectangle_top_left_lat: float = 0,
    location_rectangle_top_left_lon: float = 0,
    location_rectangle_bottom_right_lat: float = 0,
    location_rectangle_bottom_right_lon: float = 0,
    minimal: bool = False
) -> str:
    # 有効な条件のみを収集
    conditions = []
    
    # 各属性をチェックして、空でない場合のみ条件に追加    
    if prefecture_code and prefecture_code.strip():
        escaped_prefecture = prefecture_code.replace('"', '\\"')
        conditions.append(f'{{attributeName: "DPF:prefecture_code", is: "{escaped_prefecture}" }}')

    # 条件がある場合のみattribute_filterを作成
    attribute_filter = None
    if conditions:
        if len(conditions) == 1:
            # 条件が1つの場合はANDを使わない
            attribute_filter = f"""
                attributeFilter: {{
                    {conditions[0]}
                }}
            """
        else:
            # 複数の条件がある場合はANDを使用
            conditions_str = ',\n                '.join(conditions)
            attribute_filter = f"""
                attributeFilter: {{
                    AND: [
                        {conditions_str}
                    ]
                }}
            """

    """矩形範囲での検索 - 最適化版（termの空文字チェック追加）"""
    
    # 座標の妥当性チェック
    if not (-90 <= location_rectangle_top_left_lat <= 90):
        raise ValueError("Invalid top left latitude value")
    if not (-180 <= location_rectangle_top_left_lon <= 180):
        raise ValueError("Invalid top left longitude value")
    if not (-90 <= location_rectangle_bottom_right_lat <= 90):
        raise ValueError("Invalid bottom right latitude value")
    if not (-180 <= location_rectangle_bottom_right_lon <= 180):
        raise ValueError("Invalid bottom right longitude value")
    
    location_filter = f"""
        locationFilter: {{
            rectangle: {{
                topLeft: {{
                    lat: {location_rectangle_top_left_lat},
                    lon: {location_rectangle_top_left_lon}
                }},
                bottomRight: {{
                    lat: {location_rectangle_bottom_right_lat},
                    lon: {location_rectangle_bottom_right_lon}
                }}
            }}
        }}
    """
    
    graph_ql_query = build_search_query(
        term=term,
        first=first,
        size=size,
        sort_attribute_name=sort_attribute_name,
        sort_order=sort_order,
        attribute_filter=attribute_filter,
        location_filter=location_filter,
        minimal=minimal
    )
    
    result = await post_query(graph_ql_query, 'search')
    return json.dumps(result, ensure_ascii=False, separators=(',', ':'))

async def search_by_location_point_distance(
    term: str = "",
    first: int = 1,
    size: int = 50,
    sort_attribute_name: str = "",
    sort_order: str = "",
    location_lat: float = 0,
    location_lon: float = 0,
    location_distance: float = 0,
    minimal: bool = False
) -> str:
    # 有効な条件のみを収集
    conditions = []
    
    # 各属性をチェックして、空でない場合のみ条件に追加    
    if prefecture_code and prefecture_code.strip():
        escaped_prefecture = prefecture_code.replace('"', '\\"')
        conditions.append(f'{{attributeName: "DPF:prefecture_code", is: "{escaped_prefecture}" }}')

    # 条件がある場合のみattribute_filterを作成
    attribute_filter = None
    if conditions:
        if len(conditions) == 1:
            # 条件が1つの場合はANDを使わない
            attribute_filter = f"""
                attributeFilter: {{
                    {conditions[0]}
                }}
            """
        else:
            # 複数の条件がある場合はANDを使用
            conditions_str = ',\n                '.join(conditions)
            attribute_filter = f"""
                attributeFilter: {{
                    AND: [
                        {conditions_str}
                    ]
                }}
            """

    """地点付近での検索 - 最適化版（termの空文字チェック追加）"""
    
    # 座標の妥当性チェック
    if not (-90 <= location_lat <= 90):
        raise ValueError("Invalid latitude value")
    if not (-180 <= location_lon <= 180):
        raise ValueError("Invalid longitude value")
    
    location_filter = f"""
        locationFilter: {{
            geoDistance: {{
                lat: {location_lat},
                lon: {location_lon},
                distance: {location_distance}
            }}
        }}
    """
    
    graph_ql_query = build_search_query(
        term=term,
        first=first,
        size=size,
        sort_attribute_name=sort_attribute_name,
        sort_order=sort_order,
        attribute_filter=attribute_filter,
        location_filter=location_filter,
        minimal=minimal
    )
    
    result = await post_query(graph_ql_query, 'search')
    return json.dumps(result, ensure_ascii=False, separators=(',', ':'))

async def search_by_attribute(
    term: str = "",
    first: int = 1,
    size: int = 50,
    sort_attribute_name: str = "",
    sort_order: str = "",
    prefecture_code: str = "",
    municipality_code: str = "",
    address: str = "",
    catalog_id: str = "",
    dataset_id: str = "",
    minimal: bool = False
) -> str:
    """属性による検索 - 最適化版（termの空文字チェック追加）"""
    
    # 有効な条件のみを収集
    conditions = []
    
    # 各属性をチェックして、空でない場合のみ条件に追加    
    if prefecture_code and prefecture_code.strip():
        escaped_prefecture = prefecture_code.replace('"', '\\"')
        conditions.append(f'{{attributeName: "DPF:prefecture_code", is: "{escaped_prefecture}" }}')
    
    if municipality_code and municipality_code.strip():
        escaped_municipality = municipality_code.replace('"', '\\"')
        conditions.append(f'{{attributeName: "DPF:municipality_code", is: "{escaped_municipality}" }}')
    
    if address and address.strip():
        escaped_address = address.replace('"', '\\"')
        conditions.append(f'{{attributeName: "DPF:address", is: "{escaped_address}" }}')
    
    if catalog_id and catalog_id.strip():
        escaped_catalog = catalog_id.replace('"', '\\"')
        conditions.append(f'{{attributeName: "DPF:catalog_id", is: "{escaped_catalog}" }}')
    
    if dataset_id and dataset_id.strip():
        escaped_dataset = dataset_id.replace('"', '\\"')
        conditions.append(f'{{attributeName: "DPF:dataset_id", is: "{escaped_dataset}" }}')
    
    # 条件がある場合のみattribute_filterを作成
    attribute_filter = None
    if conditions:
        if len(conditions) == 1:
            # 条件が1つの場合はANDを使わない
            attribute_filter = f"""
                attributeFilter: {{
                    {conditions[0]}
                }}
            """
        else:
            # 複数の条件がある場合はANDを使用
            conditions_str = ',\n                '.join(conditions)
            attribute_filter = f"""
                attributeFilter: {{
                    AND: [
                        {conditions_str}
                    ]
                }}
            """
    
    graph_ql_query = build_search_query(
        term=term,
        first=first,
        size=size,
        sort_attribute_name=sort_attribute_name,
        sort_order=sort_order,
        attribute_filter=attribute_filter,
        minimal=minimal
    )
    
    result = await post_query(graph_ql_query, 'search')
    return json.dumps(result, ensure_ascii=False, separators=(',', ':'))

async def get_data_summary(
    dataset_id: str = "",
    data_id: str = ""
) -> str:
    """データ概要取得 - 軽量版"""
    
    # エスケープ処理
    dataset_id = dataset_id.replace('"', '\\"')
    data_id = data_id.replace('"', '\\"')
    
    # 最小限のフィールドのみ取得
    graph_ql_query = f"""
        query {{
            data(
                dataSetID: "{dataset_id}",
                dataID: "{data_id}"
            ) {{
                totalNumber
                getDataResults{{
                    id
                    title
                    lat
                    lon
                    year
                    dataset_id
                    catalog_id
                }}
            }}
        }}
    """
    
    result = await post_query(graph_ql_query, 'data')
    return json.dumps(result, ensure_ascii=False, separators=(',', ':'))

async def get_data(
    dataset_id: str = "",
    data_id: str = ""
) -> str:
    """データ取得 - 詳細版"""
    
    # エスケープ処理
    dataset_id = dataset_id.replace('"', '\\"')
    data_id = data_id.replace('"', '\\"')
    
    graph_ql_query = f"""
        query {{
            data(
                dataSetID: "{dataset_id}",
                dataID: "{data_id}"
            ) {{
                totalNumber
                getDataResults{{
                    {DETAILED_DATA_FIELDS}
                }}
            }}
        }}
    """
    
    result = await post_query(graph_ql_query, 'data')
    return json.dumps(result, ensure_ascii=False, separators=(',', ':'))

async def get_data_catalog_summary() -> str:
    """データカタログ概要取得 - 軽量版"""
    graph_ql_query = """
        query {
            dataCatalog(IDs: null) {
                id
                title
            }
        }
    """
    result = await post_query(graph_ql_query, 'dataCatalog')
    return json.dumps(result, ensure_ascii=False, separators=(',', ':'))

async def get_prefecture_data() -> str:
    """都道府県データ取得"""
    graph_ql_query = """
        query {
            prefecture {
                code
                name
            }
        }
    """
    result = await post_query(graph_ql_query, 'prefecture')
    return json.dumps(result, ensure_ascii=False, separators=(',', ':'))

async def get_municipality_data(pref_code: str = "") -> str:
    """市区町村データ取得"""
    
    # エスケープ処理
    pref_code = pref_code.replace('"', '\\"')
    
    graph_ql_query = f"""
        query {{
            municipalities(
                prefCodes: ["{pref_code}"]
            ) {{
                code
                prefecture_code
                name
            }}
        }}
    """
    result = await post_query(graph_ql_query, 'municipalities')
    return json.dumps(result, ensure_ascii=False, separators=(',', ':'))

async def main():
    """MCPサーバーのメイン関数"""
    # 標準入出力を使用してMCPプロトコルで通信
    import sys
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, 
            write_stream, 
            InitializationOptions(
                server_name="MLIT-DATA-PLATFORM-mcp",
                server_version="1.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
