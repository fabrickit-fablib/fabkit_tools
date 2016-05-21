# coding: utf-8

from fabkit import filer, sudo, env
from fablib.base import SimpleBase
# from fablib import git
from fablib.python import Python
from oslo_config import cfg

CONF = cfg.CONF


class FabClient(SimpleBase):
    def __init__(self):
        self.data_key = 'fabkit_tools'
        self.data = {
            'user': 'nobody',
            'group': 'nobody',
            'prefix': '/opt/fabkit',
            'task_patterns': 'local.*,check.*',
        }

        self.services = [
            'fabagent',
            'fabagent-central',
        ]

    def init_before(self):
        self.python = Python(self.data['prefix'])

    def init_after(self):
        self.data['owner'] = '{0}:{1}'.format(self.data['user'], self.data['group'])
        self.data['host'] = env.host

    def setup(self):
        data = self.init()

        var_dir = CONF.client.package_var_dir
        common_repo = '{0}/fabkit-repo-common'.format(var_dir)
        client_repo = '{0}/fabkit-repo-client'.format(var_dir)
        filer.template('{0}/fabfile.ini'.format(client_repo), data=data)

        sudo('rm -rf {0}/fabfile && '
             'cp -r {1}/fabfile {0}/fabfile && '
             'chown -R {2}:{3} {0}/fabfile'.format(
                 client_repo, common_repo, data['user'], data['group']))

        if env.host == env.hosts[0]:
            sudo('/opt/fabkit/bin/fabclient sync_db')

        self.start_services().enable_services()

        self.restart_services()

        sudo('/opt/fabkit/bin/fabclient -l')
