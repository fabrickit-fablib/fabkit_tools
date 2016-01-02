# coding: utf-8

from fabkit import env, filer, run
from fablib.base import SimpleBase
from fablib import git
from fablib.python import Python


class UserFabkit(SimpleBase):
    def __init__(self):
        self.packages = {
            'CentOS Linux 7.*': [
                'httpd',
            ],
            'Ubuntu 14.*': [
                'apache2'
            ]
        }

        self.services = {
            'CentOS Linux 7.*': [
                'httpd',
            ],
            'Ubuntu 14.*': [
                'apache2'
            ]
        }

    def setup(self):
        self.install_packages()

        repo = '/home/{0}/fabkit-repo'.format(env.user)
        filer.mkdir(repo, use_sudo=False)
        git.setup()
        git.sync('https://github.com/fabrickit/fabkit.git',
                 dest='{0}/fabfile'.format(repo))

        python = Python('/opt/fabkit')
        python.setup()
        python.install(
            requirements='{0}/fabfile/requirements.txt'.format(repo))

        run('cd {0} && /opt/fabkit/bin/fab -l'.format(repo))
