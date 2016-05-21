# coding: utf-8

from fabkit import task, parallel, sudo, Editor, Service, serial
from fablib.fabkit_tools import FabPackage


@task
@parallel
def setup():
    sudo('setenforce 0')
    Editor('/etc/selinux/config').s('SELINUX=enforcing', 'SELINUX=disable')

    Service('firewalld').stop().disable()

    return {'status': 1}


@task
@serial
def setup_package0():
    fabpackage = FabPackage()
    fabpackage.create_tar()
    return {'status': 1}


@task
@parallel
def setup_package1():
    fabpackage = FabPackage()
    fabpackage.setup()
    return {'status': 1}
