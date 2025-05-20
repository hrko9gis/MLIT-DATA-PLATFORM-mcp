"""
MLIT DATA PLATFORM MCP Server
"""

import requests
import asyncio
import json

from mcp.server import FastMCP

END_POINT = "https://www.mlit-data.jp/api/v1/"
API_KEY = "aXk6a-d10rH5rd-9Yq4_2EYiwFkah7U~"

mcp = FastMCP("MLIT-DATA-PLATFORM-mcp")

async def post_query(queryContents, queryName):
    request = {
        "url": END_POINT,
        "method": "post",
        "headers": {
            "Content-type": "application/json",
            "apikey": API_KEY
        },
        "data": {"query": queryContents}
    }

    try:
        response = requests.post(request["url"], headers=request["headers"], json=request["data"])
        response.raise_for_status()
        result = response.json()["data"][queryName]
    except Exception as error:
        print(f"Error data: {error}")
        result = []

    return result

@mcp.tool()
def search(
    term: str = "",
    first: int = 1,
    size: int = 100,
    sortAttributeName: str = "",
    sortOrder: str = "",
    locationRectangleTopLeftLat: float = 0,
    locationRectangleTopLeftLon: float = 0,
    locationRectangleBottomRightLat: float = 0,
    locationRectangleBottomRightLon: float = 0
) -> str:
    graph_ql_query = """
        query {
            search(
                term: "%s",
                first: %d,
                size: %d,
                sortAttributeName: "%s",
                sortOrder: "%s",
                locationFilter: {
                    rectangle: {
                        topLeft: {
                            lat: %f,
                            lon: %f
                         },
                         bottomRight: {
                            lat: %f,
                            lon: %f
                         }
                    }
                }
            ) 
            {
                searchResults {
                    id
                    title
                    metadata
                }
            }
        }
    """ % (term,first,size,sortAttributeName,sortOrder,locationRectangleTopLeftLat,locationRectangleTopLeftLon,locationRectangleBottomRightLat,locationRectangleBottomRightLon)
    result = asyncio.run(post_query(graph_ql_query, 'search'))
    return result

@mcp.tool()
def getData(
    dataSetID: str = "",
    dataID: str = ""
) -> str:
    graph_ql_query = """
        query {
            data(
                dataSetID: "%s",
                dataID: "%s"
            ) 
            {
                totalNumber
                getDataResults{
                    id
                    title
                }
            }
        }
    """ % (dataSetID,dataSetID)
    result = asyncio.run(post_query(graph_ql_query, 'data'))
    return result

@mcp.tool()
def getDataCatalog() :
    graph_ql_query = """
        query {
            dataCatalog(IDs: null) {
                id
                title
            }
        }
    """
    result = asyncio.run(post_query(graph_ql_query, 'dataCatalog'))
    return result

@mcp.tool()
def getPrefectureData() :
    graph_ql_query = """
        query {
            prefecture {
                code
                name
            }
        }
    """
    result = asyncio.run(post_query(graph_ql_query, 'prefecture'))
    return result

@mcp.tool()
def getMunicipalityData(
    prefCode: str = ""
) -> str:
    graph_ql_query = """
        query {
            municipalities(
                prefCodes: ["%s"]
            ) 
            {
                code
                prefecture_code
                name
            }
        }
    """ % (prefCode)
    result = asyncio.run(post_query(graph_ql_query, 'municipalities'))
    return result

if __name__ == "__main__":
    mcp.run()
