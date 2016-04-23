# coding: utf-8

from fabkit import task, parallel, serial
from fablib.fabkit_tools import FabClient


@task
@serial
def setup0_local():
    fabclient = FabClient()
    fabclient.create_tar()


@task
@parallel
def setup1():
    fabclient = FabClient()
    fabclient.setup()
