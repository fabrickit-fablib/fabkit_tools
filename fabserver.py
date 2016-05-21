# coding: utf-8

import re
from fabkit import filer, sudo, env
from fablib.base import SimpleBase
from oslo_config import cfg
from fablib.python import Python

CONF = cfg.CONF


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
                'fabnode',
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

        var_dir = CONF.client.package_var_dir
        common_repo = '{0}/fabkit-repo-common'.format(var_dir)
        server_repo = '{0}/fabkit-repo-server'.format(var_dir)
        filer.template('{0}/fabfile.ini'.format(server_repo), data=data)

        sudo('rm -rf {0}/fabfile && '
             'cp -r {1}/fabfile {0}/fabfile && '
             'chown -R {2}:{3} {0}/fabfile'.format(
                 server_repo, common_repo, data['user'], data['group']))

        if re.match('CentOS .*', env.node['os']):
            log_prefix = '/var/log/httpd/{0}'.format(env.user)
            data.update({
                'repo': server_repo,
                'python_path': self.python.get_site_packages(),
                'error_log': 'fabkit-error.log'.format(log_prefix),
                'custom_log': 'fabkit-access.log'.format(log_prefix),
            })

            if filer.template(src='httpd.conf',
                              dest='/etc/httpd/conf.d/fabkit_httpd.conf'.format(env.user),
                              data=data):
                self.handlers['restart_httpd'] = True

        self.exec_handlers()

        if env.host == env.hosts[0]:
            sudo("cd /opt/fabkit/var/fabkit-repo-server/fabfile/core/webapp && "
                 "/opt/fabkit/bin/python manage.py migrate --noinput")

            sudo("cd /opt/fabkit/var/fabkit-repo-server/fabfile/core/webapp && "
                 "echo \"from django.contrib.auth.models import User;"
                 "User.objects.create_superuser('admin', 'admin@example.com', 'admin')\""
                 " | /opt/fabkit/bin/python manage.py shell")

        self.start_services().enable_services()

        self.restart_services()

        sudo('/opt/fabkit/bin/fabserver -l')
