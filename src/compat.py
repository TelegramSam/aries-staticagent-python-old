""" Python compatibility """

import sys
import asyncio

def fail_incompatible():
    """ Fail and print compatibility info """
    print('This agent does not support Python versions < 3.5')
    sys.exit(1)

if not hasattr(sys.version_info, 'major'):
    fail_incompatible()

if sys.version_info.major < 3:
    fail_incompatible()

if sys.version_info.minor < 5:
    fail_incompatible()

if sys.version_info.major >= 3 and sys.version_info.minor >= 7:
    def create_task(*args, **kwargs):
        """ >= 3.7 Task Scheduling """
        return asyncio.create_task(*args, **kwargs)
else:
    def create_task(*args, **kwargs):
        """ < 3.7 Task Scheduling """
        return asyncio.ensure_future(*args, **kwargs)
