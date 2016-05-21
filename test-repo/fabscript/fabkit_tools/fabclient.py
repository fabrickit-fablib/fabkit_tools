# coding: utf-8

from fabkit import task, parallel
from fablib.fabkit_tools import FabClient


@task
@parallel
def setup():
    fabclient = FabClient()
    fabclient.setup()
    return {'status': 1}
