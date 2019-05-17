import functools

class NoHooksFoundException(Exception):
    pass

def run_hooks(hooks, hook_name, func, *args, **kwargs):
    """ Run hooks for func with hook_name.
        Parameters of pre hooks are the same as the called function.
        Parameters of post hooks are the same as the called function with the
        return values of the called function or the previous hook appended to
        the end.
    """
    if 'pre_' + hook_name in hooks:
        for hook_fn in hooks['pre_' + hook_name]:
            hook_fn(*args, **kwargs)

    return_value = func(*args, **kwargs)

    if 'post_' + hook_name in hooks:
        for hook_fn in hooks['post_' + hook_name]:
            return_value = hook_fn(*args, return_value, **kwargs)

    return return_value


def self_hook_point():
    """ Define a function with pre and post hooks inside of a class.
        This will pull `hooks` from the first argument (self).

        Hooks are looked up at runtime.

        Hooks can be defined statically or at runtime. See
        tests/test_hooks::test_object_hooks for an example.
    """
    def self_hook_point_dec(func):
        hook_name = func.__name__

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            if not args or not hasattr(args[0], 'hooks'):
                raise NoHooksFoundException

            hooks = args[0].hooks
            return run_hooks(hooks, hook_name, func, *args, **kwargs)

        return wrapped

    return self_hook_point_dec

def hook_point(hooks):
    """ Define a function with pre and post hooks given a hooks dictionary. """
    def hook_point_dec(func):
        hook_name = func.__name__

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            return run_hooks(hooks, hook_name, func, *args, **kwargs)
        return wrapped
    return hook_point_dec


def hook(hooks, hook_name):
    """ Register hook for a function. """
    if hasattr(hooks, 'hooks'):
        hooks = hooks.hooks

    if not isinstance(hooks, dict):
        raise NoHooksFoundException

    def hook_dec(func):
        if hook_name in hooks:
            hooks[hook_name].append(func)
        else:
            hooks[hook_name] = [func]

    return hook_dec
