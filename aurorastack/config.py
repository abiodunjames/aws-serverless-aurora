# This dict contains path to lambda function mapping.
# "api_path": {"method": "the http method to use", "function":"the corresponding lambda function"}
routes = {
    "posts": [{"method": "GET", "function": "get_posts"}],
}