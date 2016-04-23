# coding: utf-8

from fabkit import filer, sudo, env, local, scp
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
        self.python.setup()

        var_dir = '{0}/var'.format(data['prefix'])
        repo = '{0}/fabkit-repo-client'.format(var_dir)
        filer.mkdir(var_dir, owner=data['owner'])
        filer.mkdir(repo, owner=data['owner'])

        # git.setup()
        # git.sync('https://github.com/fabrickit/fabkit.git',
        #          dest='{0}/fabfile'.format(repo), user=data['user'])
        sudo('rm -rf /tmp/fabfile*')
        sudo('rm -rf {0}/fabfile'.format(repo))
        scp('/tmp/fabfile.tar.gz', '/tmp/fabfile.tar.gz')
        sudo('cd /tmp/ && tar xzf /tmp/fabfile.tar.gz '
             '&& cp -r fabfile {0}/fabfile'.format(repo))

        sudo('{0}/bin/pip install -r {1}/fabfile/requirements.txt'.format(data['prefix'], repo))

        data['repo'] = repo
        filer.template('{0}/fabfile.ini'.format(repo), data=data)
        filer.template('{0}/bin/fabclient'.format(data['prefix']),
                       src='fabric.sh', data=data, mode='755')

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

        sudo('systemctl daemon-reload')

        self.start_services().enable_services()

        sudo('/opt/fabkit/bin/fabclient -l')

    def create_tar(self):
        if env.host == env.hosts[0]:
            local(
                'rm -rf /tmp/fabfile && '
                'cp -r {0} /tmp/fabfile && '
                'find /tmp/fabfile -name .git | xargs rm -rf && '
                'cd /tmp/ && tar cfz fabfile.tar.gz fabfile'.format(CONF._fabfile_dir)
            )
