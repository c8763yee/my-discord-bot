# https://github.com/akarsh1995/leetcode-graphql-queries for more queries
with open("queries/profile_page.graphql", "r") as f:
    LEETCODE_USER_QUERY: str = f.read()


THUMBNAIL_URL: str = "https://leetcode.com/static/images/LeetCode_Sharing.png"
API_URL: str = "https://leetcode.com/graphql"
REQUEST_BODY: dict[str, str | dict[str, str | int]] = {
    "query": LEETCODE_USER_QUERY,
    "operationName": "",
    "variables": {
        "username": "",
        "year": "",
        "month": "",
        "limit": 1,
    },
}
