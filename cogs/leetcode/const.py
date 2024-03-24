# https://github.com/akarsh1995/leetcode-graphql-queries for more queries
THUMBNAIL_URL: str = "https://leetcode.com/static/images/LeetCode_Sharing.png"
API_URL: str = "https://leetcode.com/graphql"
REQUEST_BODY: dict[str, str | dict[str, str | int]] = {
    "query": "",
    "operationName": "",
    "variables": {
        "username": "",
        "year": "",
        "month": "",
        "limit": 1,
    },
}
