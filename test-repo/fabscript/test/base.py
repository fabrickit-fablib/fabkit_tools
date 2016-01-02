# coding: utf-8

from fabkit import task
from fablib.fabkit_tools.user_fabkit import UserFabkit


@task
def setup():
    userfabkit = UserFabkit()
    userfabkit.setup()
