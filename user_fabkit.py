# coding: utf-8

import re
from fabkit import env, filer, run, sudo
from fablib.base import SimpleBase
from fablib import git
from fablib.python import Python


class UserFabkit(SimpleBase):
    def __init__(self):
        self.packages = {
            'CentOS Linux 7.*': [
                'epel-release',
                'httpd',
                'mod_wsgi',
                'redis',
                'nodejs',
                'npm',
            ],
            'Ubuntu 14.*': [
                'apache2',
                'libapache2-mod-wsgi',
                'redis-server',
                'nodejs',
                'npm',
            ]
        }

        self.services = {
            'CentOS Linux 7.*': [
                'httpd',
                'redis',
            ],
            'Ubuntu 14.*': [
                'apache2',
                'redis-server',
            ]
        }

    def setup(self):
        self.install_packages()
        self.start_services().enable_services()

        repo = '/home/{0}/fabkit-repo'.format(env.user)
        filer.mkdir(repo, use_sudo=False)
        git.setup()
        git.sync('https://github.com/fabrickit/fabkit.git',
                 dest='{0}/fabfile'.format(repo))

        python = Python('/opt/fabkit')
        python.setup()
        python.install(
            requirements='{0}/fabfile/requirements.txt'.format(repo))

        run('cd {0} && /opt/fabkit/bin/fab genconfig:fabfile.ini &&'
            ' sed -i "/^\[web\]/,/^\[/s/#hostname =.*/hostname = */g" fabfile.ini'.format(repo))

        data = {
            'port': 8080,
            'repo': repo,
            'user': env.user,
            'group': env.user,
            'python_path': python.get_site_packages(),
            'processes': 5,
            'threads': 1,
        }

        run('cd {0}/fabfile/core/webapp/ &&'
            ' /opt/fabkit/bin/python manage.py migrate &&'
            ' echo "from django.contrib.auth.models import User;'
            '       User.objects.create_superuser(\'admin\', \'admin@localhost\', \'admin\')"'
            '       | /opt/fabkit/bin/python manage.py shell &&'
            ' /opt/fabkit/bin/python manage.py collectstatic --noinput'.format(repo))

        sudo('chmod 755 /home/{0}'.format(env.user))

        if re.match('CentOS .*', env.node['os']):
            log_prefix = '/var/log/httpd/{0}'.format(env.user)
            data['error_log'] = '{0}-error.log'.format(log_prefix)
            data['custom_log'] = '{0}-access.log'.format(log_prefix)

            if filer.template(src='httpd.conf',
                              dest='/etc/httpd/conf.d/{0}_httpd.conf'.format(env.user),
                              data=data):
                self.handlers['restart_httpd'] = True

        elif re.match('Ubuntu .*', env.node['os']):
            log_prefix = '/var/log/apache2/{0}'.format(env.user)
            data['error_log'] = '{0}-error.log'.format(log_prefix)
            data['custom_log'] = '{0}-access.log'.format(log_prefix)

            if filer.template(src='httpd.conf',
                              dest='/etc/apache2/sites-enabled/{0}_httpd.conf'.format(env.user),
                              data=data):
                self.handlers['restart_apache2'] = True

        self.exec_handlers()

        # install
        sudo('npm install -g coffee-script'.format(repo))
        run('cd {0}/fabfile/core/webapp && npm install'.format(repo))

        # install node packages for develop
        sudo('npm install -g grunt-cli'.format(repo))
        run('cd {0}/fabfile/core/webapp/node_chat && npm install'.format(repo))
