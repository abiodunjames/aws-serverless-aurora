from utils import execute_statement

# It's important functions use "handler"
def handler(event, context):
    response = execute_statement(f"select * from posts")
    return {"statusCode": 200, "body": response["records"]}


routes = {
    "posts": [
        {"method": "GET", "function": "get_posts"},
        {"method": "POST", "function": "create_posts"},
    ],
}