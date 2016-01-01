# coding: utf-8

from fabkit import env, filer, sudo
from fablib.base import SimpleBase


class UserFabkit(SimpleBase):
    def __init__(self):
        pass

    def init_before(self):
        pass

    def init_after(self):
        pass

    def setup(self):
        print 'setup'
