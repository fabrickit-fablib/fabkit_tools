# coding: utf-8

import os
from fabkit import filer, sudo, env, local, scp, Package
from fablib.base import SimpleBase
# from fablib import git
from fablib.python import Python
from oslo_config import cfg

CONF = cfg.CONF


class FabPackage(SimpleBase):
    def __init__(self):
        self.data_key = 'fabkit_tools'
        self.data = {
            'user': 'nobody',
            'group': 'nobody',
            'task_patterns': 'local.*,check.*',
            'use_package': False,
            'package_name': 'fabkit',
        }

        self.services = [
            'fabagent',
            'fabagent-central',
        ]

        self.packages = {
            'CentOS Linux 7.*': [
                'epel-release',
                'nodejs',
                'npm',
            ],
            'Ubuntu 14.*': [
                'nodejs',
                'npm',
            ]
        }

    def init_before(self):
        self.python = Python(CONF.client.package_prefix)

    def init_after(self):
        self.data['owner'] = '{0}:{1}'.format(self.data['user'], self.data['group'])
        self.data['host'] = env.host
        self.data['prefix'] = CONF.client.package_prefix

    def setup(self):
        data = self.init()

        var_dir = CONF.client.package_var_dir
        tmp_dir = os.path.join(var_dir, 'tmp')
        log_dir = '/var/log/fabkit'
        common_repo = '{0}/fabkit-repo-common'.format(var_dir)
        client_repo = '{0}/fabkit-repo-client'.format(var_dir)
        server_repo = '{0}/fabkit-repo-server'.format(var_dir)

        if data['use_package']:
            Package(data['package_name']).install()
            return

        self.install_packages()
        self.python.setup()
        filer.mkdir(var_dir, owner=data['owner'])
        filer.mkdir(log_dir, owner=data['owner'])
        filer.mkdir(tmp_dir, owner=data['owner'], mode='777')

        filer.mkdir(common_repo, owner=data['owner'])
        filer.mkdir(client_repo, owner=data['owner'])
        filer.mkdir(server_repo, owner=data['owner'])

        sudo('rm -rf {0}/fabfile*'.format(tmp_dir))
        fabfile_tar_gz = os.path.join(tmp_dir, 'fabfile.tar.gz')
        scp('/tmp/fabfile.tar.gz', fabfile_tar_gz)

        sudo('rm -rf {0}/fabfile'.format(common_repo))
        sudo('cd {0} && tar xzf {1} && '
             'cp -r fabfile {2}/fabfile'.format(
                 tmp_dir, fabfile_tar_gz, common_repo))

        sudo('{0}/bin/pip install -r {1}/fabfile/requirements.txt'.format(
             CONF.client.package_prefix, common_repo))

        data['repo'] = client_repo
        filer.template('{0}/bin/fabclient'.format(CONF.client.package_prefix),
                       src='fabric.sh', data=data, mode='755')

        data['repo'] = server_repo
        filer.template('{0}/bin/fabserver'.format(CONF.client.package_prefix),
                       src='fabric.sh', data=data, mode='755')

        filer.template('{0}/bin/fabnode'.format(CONF.client.package_prefix),
                       src='fabnode.sh', data=data, mode='755')

        filer.template('/etc/systemd/system/fabagent.service',
                       src='systemd.service', data={
                           'description': 'fabagent',
                           'exec': '/opt/fabkit/bin/fabclient agent',
                           'user': 'root',
                       })

        filer.template('/etc/systemd/system/fabagent-central.service',
                       src='systemd.service', data={
                           'description': 'fabagent',
                           'exec': '/opt/fabkit/bin/fabclient agent_central',
                           'user': 'root',
                       })

        filer.template('/etc/systemd/system/fabnode.service',
                       src='systemd.service', data={
                           'description': 'fabnode',
                           'exec': '/opt/fabkit/bin/fabnode',  # noqa
                           'user': 'root',
                       })

        sudo('systemctl daemon-reload')

        sudo('npm install -g coffee-script')
        sudo('cd {0}/fabfile/core/webapp/fabnode && '
             'npm install'.format(common_repo))

    def create_tar(self):
        if env.host == env.hosts[0]:
            local(
                'rm -rf /tmp/fabfile && '
                'cp -r {0} /tmp/fabfile && '
                'find /tmp/fabfile -name .git | xargs rm -rf && '
                'cd /tmp/ && tar cfz fabfile.tar.gz fabfile'.format(CONF._fabfile_dir)
            )
