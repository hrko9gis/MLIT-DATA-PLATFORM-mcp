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

async def post_query(query_contents: str, query_name: str) -> List[Dict[str, Any]]:
    """
    GraphQLクエリを実行する
    
    Args:
        query_contents: GraphQLクエリ文字列
        query_name: レスポンスから取得するデータのキー名
    
    Returns:
        クエリ結果のリスト
    """
    headers = {
        "Content-type": "application/json",
        "apikey": API_KEY
    }
    
    data = {"query": query_contents}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                END_POINT,
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=30)
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
    size: int = 100,
    sort_attribute_name: str = "",
    sort_order: str = "",
    location_filter: Optional[str] = None,
    attribute_filter: Optional[str] = None
) -> str:
    """
    検索用GraphQLクエリを構築する
    """
    # パラメータの検証
    if not isinstance(first, int) or first < 1:
        first = 1
    if not isinstance(size, int) or size < 1 or size > 1000:  # 上限設定
        size = 100
    
    # エスケープ処理
    term = term.replace('"', '\\"')
    sort_attribute_name = sort_attribute_name.replace('"', '\\"')
    sort_order = sort_order.replace('"', '\\"')
    
    query_parts = [
        f'term: "{term}"',
        f'first: {first}',
        f'size: {size}'
    ]
    
    if sort_attribute_name:
        query_parts.append(f'sortAttributeName: "{sort_attribute_name}"')
    if sort_order:
        query_parts.append(f'sortOrder: "{sort_order}"')
    if location_filter:
        query_parts.append(location_filter)
    if attribute_filter:
        query_parts.append(attribute_filter)
    
    query = f"""
        query {{
            search({', '.join(query_parts)}) {{
                searchResults {{
                    id
                    title
                    dataset_id
                    metadata
                    meshes {{
                        title
                        id
                    }}
                }}
            }}
        }}
    """
    
    return query

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    利用可能なツールのリストを返す
    """
    return [
        types.Tool(
            name="search",
            description="基本検索を実行します",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "検索キーワード"},
                    "first": {"type": "integer", "description": "開始位置", "default": 1},
                    "size": {"type": "integer", "description": "取得件数", "default": 100},
                    "sort_attribute_name": {"type": "string", "description": "ソート属性名"},
                    "sort_order": {"type": "string", "description": "ソート順序"}
                }
            }
        ),
        types.Tool(
            name="search_by_location_rectangle",
            description="矩形範囲での検索を実行します",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "検索キーワード"},
                    "first": {"type": "integer", "description": "開始位置", "default": 1},
                    "size": {"type": "integer", "description": "取得件数", "default": 100},
                    "sort_attribute_name": {"type": "string", "description": "ソート属性名"},
                    "sort_order": {"type": "string", "description": "ソート順序"},
                    "location_rectangle_top_left_lat": {"type": "number", "description": "左上緯度"},
                    "location_rectangle_top_left_lon": {"type": "number", "description": "左上経度"},
                    "location_rectangle_bottom_right_lat": {"type": "number", "description": "右下緯度"},
                    "location_rectangle_bottom_right_lon": {"type": "number", "description": "右下経度"}
                },
                "required": ["location_rectangle_top_left_lat", "location_rectangle_top_left_lon", 
                           "location_rectangle_bottom_right_lat", "location_rectangle_bottom_right_lon"]
            }
        ),
        types.Tool(
            name="search_by_location_point_distance",
            description="地点距離での検索を実行します",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "検索キーワード"},
                    "first": {"type": "integer", "description": "開始位置", "default": 1},
                    "size": {"type": "integer", "description": "取得件数", "default": 100},
                    "sort_attribute_name": {"type": "string", "description": "ソート属性名"},
                    "sort_order": {"type": "string", "description": "ソート順序"},
                    "location_lat": {"type": "number", "description": "緯度"},
                    "location_lon": {"type": "number", "description": "経度"},
                    "location_distance": {"type": "number", "description": "距離"}
                },
                "required": ["location_lat", "location_lon", "location_range"]
            }
        ),
        types.Tool(
            name="search_by_attribute",
            description="属性による検索を実行します",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "検索キーワード"},
                    "first": {"type": "integer", "description": "開始位置", "default": 1},
                    "size": {"type": "integer", "description": "取得件数", "default": 100},
                    "sort_attribute_name": {"type": "string", "description": "ソート属性名"},
                    "sort_order": {"type": "string", "description": "ソート順序"},
                    "prefecture_name": {"type": "string", "description": "都道府県名"},
                    "catalog_id": {"type": "string", "description": "カタログID"},
                    "dataset_id": {"type": "string", "description": "データセットID"}
                }
            }
        ),
        types.Tool(
            name="get_data",
            description="データを取得します",
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
            name="get_data_catalog",
            description="データカタログを取得します",
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
    ツール呼び出しのハンドラー
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
        elif name == "get_data":
            result = await get_data(**arguments)
        elif name == "get_data_catalog":
            result = await get_data_catalog()
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
        
        logger.info(f"Tool {name} completed successfully")
        return [types.TextContent(type="text", text=result)]
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        error_msg = f"Error executing {name}: {str(e)}"
        return [types.TextContent(type="text", text=error_msg)]

async def search(
    term: str = "",
    first: int = 1,
    size: int = 100,
    sort_attribute_name: str = "",
    sort_order: str = ""
) -> str:
    """基本検索"""
    graph_ql_query = build_search_query(
        term=term,
        first=first,
        size=size,
        sort_attribute_name=sort_attribute_name,
        sort_order=sort_order
    )
    
    result = await post_query(graph_ql_query, 'search')
    return json.dumps(result, ensure_ascii=False, indent=2)

async def search_by_location_rectangle(
    term: str = "",
    first: int = 1,
    size: int = 100,
    sort_attribute_name: str = "",
    sort_order: str = "",
    location_rectangle_top_left_lat: float = 0,
    location_rectangle_top_left_lon: float = 0,
    location_rectangle_bottom_right_lat: float = 0,
    location_rectangle_bottom_right_lon: float = 0
) -> str:
    """矩形範囲での検索"""
    
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
        location_filter=location_filter
    )
    
    result = await post_query(graph_ql_query, 'search')
    return json.dumps(result, ensure_ascii=False, indent=2)

async def search_by_location_point_distance(
    term: str = "",
    first: int = 1,
    size: int = 100,
    sort_attribute_name: str = "",
    sort_order: str = "",
    location_lat: float = 0,
    location_lon: float = 0,
    location_distance: float = 0
) -> str:
    """地点付近での検索"""
    
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
        location_filter=location_filter
    )
    
    result = await post_query(graph_ql_query, 'search')
    return json.dumps(result, ensure_ascii=False, indent=2)

async def search_by_attribute(
    term: str = "",
    first: int = 1,
    size: int = 100,
    sort_attribute_name: str = "",
    sort_order: str = "",
    prefecture_name: str = "",
    catalog_id: str = "",
    dataset_id: str = ""
) -> str:
    """属性による検索"""
    
    # エスケープ処理
    prefecture_name = prefecture_name.replace('"', '\\"')
    catalog_id = catalog_id.replace('"', '\\"')
    dataset_id = dataset_id.replace('"', '\\"')
    
    attribute_filter = f"""
        attributeFilter: {{
            AND: [
                {{attributeName: "DPF:prefecture_name", is: "{prefecture_name}" }},
                {{attributeName: "DPF:catalog_id", is: "{catalog_id}" }},
                {{attributeName: "DPF:dataset_id", is: "{dataset_id}" }}
            ]
        }}
    """
    
    graph_ql_query = build_search_query(
        term=term,
        first=first,
        size=size,
        sort_attribute_name=sort_attribute_name,
        sort_order=sort_order,
        attribute_filter=attribute_filter
    )
    
    result = await post_query(graph_ql_query, 'search')
    return json.dumps(result, ensure_ascii=False, indent=2)

async def get_data(
    dataset_id: str = "",
    data_id: str = ""
) -> str:
    """データ取得"""
    
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
                    id
                    title
                    lat
                    lon
                    year
                    theme
                    favorite
                    metadata
                    shape
                    highlight
                    dataset_id
                    catalog_id
                    displayOptions
                    hasThumbnail
                }}
            }}
        }}
    """
    
    result = await post_query(graph_ql_query, 'data')
    return json.dumps(result, ensure_ascii=False, indent=2)

async def get_data_catalog() -> str:
    """データカタログ取得"""
    graph_ql_query = """
        query {
            dataCatalog(IDs: null) {
                id
                title
            }
        }
    """
    result = await post_query(graph_ql_query, 'dataCatalog')
    return json.dumps(result, ensure_ascii=False, indent=2)

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
    return json.dumps(result, ensure_ascii=False, indent=2)

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
    return json.dumps(result, ensure_ascii=False, indent=2)

async def main():
    """メイン関数"""
    try:
        # 方法1: stdio_server を使用
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream, 
                write_stream, 
                InitializationOptions(
                    server_name="MLIT-DATA-PLATFORM-mcp",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )
    except ImportError:
        # 方法2: 直接的なstdio実装
        import sys
        from mcp.server import stdio
        
        await server.run_stdio()

if __name__ == "__main__":
    # イベントループを直接実行
    import asyncio
    asyncio.run(main())
