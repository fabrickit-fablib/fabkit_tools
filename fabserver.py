# coding: utf-8

import re
from fabkit import filer, sudo, env, scp
from fablib.base import SimpleBase
from fablib.python import Python


class FabServer(SimpleBase):
    def __init__(self):
        self.data_key = 'fabkit_tools'

        self.data = {
            'port': 8080,
            'user': 'nobody',
            'group': 'nobody',
            'prefix': '/opt/fabkit',
            'task_patterns': 'local.*,check.*',
            'processes': 5,
            'threads': 1,
        }

        self.packages = {
            'CentOS Linux 7.*': [
                'epel-release',
                'httpd',
                'mod_wsgi',
                'nodejs',
                'npm',
            ],
            'Ubuntu 14.*': [
                'apache2',
                'libapache2-mod-wsgi',
                'nodejs',
                'npm',
            ]
        }

        self.services = {
            'CentOS Linux 7.*': [
                'httpd',
            ],
            'Ubuntu 14.*': [
                'apache2',
            ]
        }

    def init_before(self):
        self.python = Python(self.data['prefix'])

    def init_after(self):
        self.data['owner'] = '{0}:{1}'.format(self.data['user'], self.data['group'])
        self.data['host'] = env.host

    def setup(self):
        data = self.init()
        self.install_packages()
        self.start_services().enable_services()

        var_dir = '{0}/var'.format(data['prefix'])
        repo = '{0}/fabkit-repo-server'.format(var_dir)
        filer.mkdir(var_dir, owner=data['owner'])
        filer.mkdir(repo, owner=data['owner'])

        data.update({
            'repo': repo,
            'python_path': self.python.get_site_packages(),
        })

        filer.template('{0}/fabfile.ini'.format(repo), data=data)

        # git.setup()
        # git.sync('https://github.com/fabrickit/fabkit.git',
        #          dest='{0}/fabfile'.format(repo), user=data['user'])
        sudo('rm -rf /tmp/fabfile*')
        sudo('rm -rf {0}/fabfile'.format(repo))
        scp('/tmp/fabfile.tar.gz', '/tmp/fabfile.tar.gz')
        sudo('cd /tmp/ && tar xzf /tmp/fabfile.tar.gz '
             '&& cp -r fabfile {0}/fabfile '
             '&& chown -R {1}:{2} {0}/fabfile'.format(
                 repo, data['user'], data['group']))

        filer.template('{0}/bin/fabserver'.format(data['prefix']),
                       src='fabric.sh', data=data, mode='755')

        if re.match('CentOS .*', env.node['os']):
            log_prefix = '/var/log/httpd/{0}'.format(env.user)
            data['error_log'] = 'fabkit-error.log'.format(log_prefix)
            data['custom_log'] = 'fabkit-access.log'.format(log_prefix)

            if filer.template(src='httpd.conf',
                              dest='/etc/httpd/conf.d/fabkit_httpd.conf'.format(env.user),
                              data=data):
                self.handlers['restart_httpd'] = True

        self.exec_handlers()

        sudo('/opt/fabkit/bin/fabserver -l')

        if env.host == env.hosts[0]:
            sudo('/opt/fabkit/bin/fabserver sync_db')
            sudo("cd /opt/fabkit/var/fabkit-repo-server/fabfile/core/webapp && "
                 "echo \"from django.contrib.auth.models import User;"
                 "User.objects.create_superuser('admin', 'admin@example.com', 'admin')\""
                 " | /opt/fabkit/bin/python manage.py shell")

        sudo('npm install -g coffee-script')
        sudo('cd /opt/fabkit/var/fabkit-repo-server/fabfile/core/webapp/node_modules && '
             'npm install')

        return

        # install
        sudo('cd /opt/fabkit/var/fabkit-repo-server/fabfile/core/webapp/node_modules && '
             'npm install -g coffee-script')
        sudo('cd {0}/fabfile/core/webapp && npm install'.format(repo))

        # install node packages for develop
        sudo('npm install -g grunt-cli'.format(repo))
        sudo('cd {0}/fabfile/core/webapp/node_chat && npm install'.format(repo))
