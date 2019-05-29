def route_def(routes, msg_type):
    """ Route definition decorator """
    def _route_def(func):
        routes[msg_type] = func
    return _route_def

class Module:
    pass
