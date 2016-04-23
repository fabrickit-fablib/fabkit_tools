# coding: utf-8

from fabkit import task, parallel
from fablib.fabkit_tools import FabServer


@task
@parallel
def setup():
    fabserver = FabServer()
    fabserver.setup()
