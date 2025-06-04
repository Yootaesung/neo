class FastMCP:
    def __init__(self, name, dependencies=None):
        self.name = name
        self.dependencies = dependencies or []

    def tools(self):
        def decorator(func):
            return func
        return decorator

    def resource(self, path):
        def decorator(func):
            return func
        return decorator

    def prompts(self):
        def decorator(func):
            return func
        return decorator