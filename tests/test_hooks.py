from collections import namedtuple
from hooks import hook, hook_point, self_hook_point


def test_hooks():
    hooks = {}

    @hook_point(hooks)
    def testing(a, b):
        assert a == 'one'
        assert b == 'two'
        return 1

    @hook(hooks, 'pre_testing')
    def pre_hook(a, b):
        assert a == 'one'
        assert b == 'two'

    @hook(hooks, 'post_testing')
    def post_hook(a, b, ret):
        assert ret == 1
        return 2

    @hook(hooks, 'post_testing')
    def post_hook2(a, b, ret2):
        assert ret2 == 2
        return 3

    assert testing('one', 'two') == 3

def test_object_hooks():
    class Hookable:
        hooks = {}
        def __init__(self):
            self.hooks = Hookable.hooks.copy()

        @hook(hooks, 'pre_testing')
        def pre_hook(self, a, b):
            assert a == 'one'
            assert b == 'two'


        @hook(hooks, 'post_testing')
        def post_hook(self, a, b, ret):
            assert ret == 1
            return 2

        @hook(hooks, 'post_testing')
        def post_hook2(self, a, b, ret2):
            assert ret2 == 2
            return 3

        @self_hook_point()
        def testing(self, a, b):
            assert a == 'one'
            assert b == 'two'
            return 1

        def hook(self, hook_name):
            return hook(self, hook_name)

    hookable = Hookable()

    @hookable.hook('post_testing')
    def post_hook_out_of_object(obj, a, b, ret3):
        assert ret3 == 3
        return 4

    assert hookable.testing('one', 'two') == 4
