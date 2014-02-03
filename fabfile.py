import os
from contextlib import contextmanager
from fabric.api import cd, env, prefix, run, settings, sudo, task
from fabric.contrib.files import exists


class V(object):

    @property
    def home(self):
        home = os.path.split(env.get('VIRTUAL_ENV', ''))[0]
        return home or ('/home/%s/.virtualenvs' % env.user)

    @property
    def name(self):
        name = os.path.split(env.get('VIRTUAL_ENV', ''))[1]
        return name or 'crosscompute'

    @property
    def path(self):
        return os.path.join(self.home, self.name)


class F(object):

    @property
    def userFolder(self):
        return os.path.join('/home', env.user)

    @property
    def documentFolder(self):
        return os.path.join(self.userFolder, 'Documents')

    @property
    def notebookFolder(self):
        return os.path.join(self.documentFolder, NOTEBOOK_REPOSITORY_NAME)

    @property
    def profileFolder(self):
        return os.path.join(
            self.userFolder,
            '.ipython',
            'profile_%s' % IPYTHON_PROFILE_NAME)

    @property
    def securityFolder(self):
        return os.path.join(self.profileFolder, 'security')

    @property
    def logPath(self):
        return os.path.join(self.profileFolder, 'log', 'server.log')


v = V()
f = F()
NOTEBOOK_REPOSITORY_NAME = 'crosscompute-tutorials'
IPYTHON_PROFILE_NAME = 'server'
IPYTHON_NOTEBOOK_CONFIG_PY = """
# Custom configuration
c.NotebookApp.certfile = u'%(certificatePath)s'
c.NotebookApp.open_browser = False
c.NotebookApp.password = u'%(ipythonPassword)s'
c.NotebookApp.port = 8888
c.NotebookApp.port_retries = 0
c.IPKernelApp.pylab = u'inline'"""
CRT_PREFIX = '; '.join([
    'source $VIRTUAL_ENV/bin/activate',
    'export LD_LIBRARY_PATH=$VIRTUAL_ENV/lib',
    'export NODE_PATH=$VIRTUAL_ENV/lib/node_modules',
])
SERVER_CRT = """\
VIRTUAL_ENV="%(virtualenv.path)s"
* * * * * %(crtPrefix)s; cd %(notebookFolder)s; ipython notebook --profile=%(profileName)s >> %(logPath)s 2>&1"""
PROXY_CRT = """\
VIRTUAL_ENV="%(virtualenv.path)s"
* * * * * %(crtPrefix)s; cd /root; node proxy.js >> proxy.log 2>&1"""
RC_LOCAL = """\
#!/bin/sh
cd %(notebookFolder)s; git fetch --all; git reset --hard origin/master"""
SSHD_CONFIG = """
PermitRootLogin without-password
PasswordAuthentication no
UseDNS no"""


@contextmanager
def virtualenvwrapper():
    commandLines = [
        'export WORKON_HOME=%s' % v.home,
        'source /usr/bin/virtualenvwrapper.sh',
    ]
    with prefix('; '.join(commandLines)):
        yield


@contextmanager
def virtualenv():
    with virtualenvwrapper():
        with prefix('workon ' + v.name):
            yield


@task(default=True)
def install():
    'Install scientific computing environment'
    install_base()
    install_ipython()
    install_pyramid()
    install_textual()
    install_numerical()
    install_computational()
    install_spatial()
    install_node()


@task
def install_base():
    'Install base applications and packages'
    d = {
        'virtualenv.home': v.home,
        'virtualenv.path': v.path,
        'user': env.user,
    }
    # Install terminal utilities
    sudo('yum -y install vim-enhanced tmux git wget tar unzip fabric python-virtualenvwrapper aiksaurus')
    sudo('mkdir -p %(virtualenv.path)s/opt' % d)
    sudo('chown -R %(user)s %(virtualenv.home)s' % d)
    sudo('chgrp -R %(user)s %(virtualenv.home)s' % d)
    with virtualenvwrapper():
        run('mkvirtualenv --system-site-packages %s' % v.name)

    # Install scripts
    def customize(repository_path):
        run(r"sed -i 's/WORKON_HOME=$HOME\/.virtualenvs/WORKON_HOME=%s/' .bashrc" % v.home.replace('/', '\/'))
        run('./setup %s' % v.name)
        sudo('./setup %s' % v.name)
    download('https://github.com/invisibleroads/scripts.git', customize=customize)
    # Install graphical utilities
    sudo('yum -y install libgnome nautilus-open-terminal vim-X11 xcalib')
    # Install compilers
    sudo('yum -y install gcc gcc-c++ gcc-gfortran make swig hg svn')
    # Clean up
    sudo('yum -y remove aisleriot gnome-games')
    sudo('yum -y update')
    # Install packages
    sudo('yum -y install python-coverage python-nose python-flake8')


@task
def install_ipython():
    'Install IPython computing environment'
    sudo('yum -y install ipython python-ipdb zeromq-devel')
    with virtualenv():
        run('pip install --upgrade pyzmq tornado')
        run('pip install --upgrade ipython')
        run('pip install --upgrade ipdb')
        run('ipython -c "from IPython.external.mathjax import install_mathjax; install_mathjax()"')


@task
def install_pyramid():
    'Install Pyramid web framework'
    sudo('yum -y install postgresql postgresql-devel postgresql-server python-psycopg2 python-sqlalchemy redis')
    sudo('yum -y install python-formencode python-simplejson python-sphinx python-transaction python-waitress python-webtest')
    with virtualenv():
        run('pip install --upgrade archiveIO dogpile.cache imapIO pyramid pyramid_debugtoolbar pyramid_mailer pyramid_tm python-openid velruse whenIO zope.sqlalchemy rq')


@task
def install_textual():
    sudo('yum -y install python-beautifulsoup4')


@task
def install_numerical():
    'Install numerical packages'
    sudo('yum -y install Cython GraphicsMagick blosc-devel hdf5 hdf5-devel')
    sudo('yum -y install numpy scipy python-matplotlib python-pandas sympy h5py pydot python-psutil')
    install_package('https://github.com/PyTables/PyTables.git', yum_install='bzip2-devel lzo-devel zlib-devel', pip_install='numexpr')
    install_package('https://github.com/certik/line_profiler.git')
    with virtualenv():
        run('pip install --upgrade memory_profiler objgraph')


@task
def install_computational():
    'Install computational packages'
    sudo('yum -y install python-scikit-learn python-networkx graphviz-python python-Bottleneck')
    install_package('http://pyamg.googlecode.com/svn/trunk', 'pyamg', yum_install='suitesparse-devel')
    install_package('https://github.com/Theano/Theano.git')
    install_package('https://github.com/lisa-lab/pylearn2.git')
    with virtualenv():
        run('pip install --upgrade openpyxl xlrd xlwt patsy')
        run('pip install --upgrade statsmodels')


@task
def install_spatial():
    'Install spatial packages'
    sudo('yum -y install proj proj-devel proj4-epsg proj4-nad')
    sudo('yum -y install geos geos-devel geos-python')
    sudo('yum -y install gdal gdal-devel gdal-python python-shapely')
    sudo('yum -y install python-basemap python-basemap-data python-basemap-data-hires python-basemap-examples')
    sudo('yum -y install python-geojson')
    with virtualenv():
        run('pip install --upgrade geometryIO')


@task
def install_node():
    'Install node.js server'
    install_library('http://nodejs.org/dist/v0.10.25/node-v0.10.25.tar.gz', 'node', yum_install='openssl-devel')
    with virtualenv():
        run('npm install -g commander expresso http-proxy node-inspector requirejs should socket.io uglify-js')
    run('rm -Rf tmp')


@task
def clear_history():
    'Clear history and logs'
    sudo('yum -y update')
    shred = lambda path: sudo('shred %s -fuz' % path)
    with settings(warn_only=True):
        shred(os.path.join(f.userFolder, '.bash_history'))
        shred(os.path.join(f.profileFolder, 'history.sqlite'))
        shred(f.logPath)
        shred('/root/.bash_history')
        shred('/root/proxy.log')
    sudo('history -c')
    run('history -c')


@task
def configure_ipython_notebook():
    'Configure IPython Notebook server'
    print 'Please specify a password for your IPython server'
    from IPython.lib import passwd
    ipythonPassword = passwd()
    # Set paths
    certificatePath = os.path.join(f.securityFolder, 'ssl.pem')
    profilePath = os.path.join(f.profileFolder, 'ipython_notebook_config.py')
    userCrontabPath = os.path.join(f.profileFolder, 'server.crt')
    run('rm -Rf %s %s' % (f.profileFolder, f.notebookFolder))
    # Prepare dictionary
    d = {
        'certificatePath': certificatePath,
        'ipythonPassword': ipythonPassword,
        'virtualenv.path': v.path,
        'crtPrefix': CRT_PREFIX,
        'notebookFolder': f.notebookFolder,
        'profileName': IPYTHON_PROFILE_NAME,
        'logPath': f.logPath,
    }
    # Download documents
    run('mkdir -p %s' % f.documentFolder)
    with cd(f.documentFolder):
        run('git clone --depth=1 https://github.com/invisibleroads/%s.git' % NOTEBOOK_REPOSITORY_NAME)
    # Create profile
    with virtualenv():
        run('ipython profile create %s' % IPYTHON_PROFILE_NAME)
    # Generate certificate
    with cd(f.securityFolder):
        run('openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout ssl.pem -out ssl.pem')
    # Configure server
    upload_text(profilePath, IPYTHON_NOTEBOOK_CONFIG_PY % d, append=True)
    # Add crontab
    upload_text(userCrontabPath, SERVER_CRT % d)
    run('crontab %s' % userCrontabPath)
    # Setup proxy
    configure_proxy()
    # Open ports
    upload_file('/etc/sysconfig/iptables', sourcePath='iptables', su=True)
    # Update notebooks on boot
    upload_text('/etc/rc.d/rc.local', RC_LOCAL % d, su=True)
    sudo('chmod 755 /etc/rc.d/rc.local')
    # Clear history
    clear_history()


@task
def configure_proxy():
    d = {
        'virtualenv.path': v.path,
        'crtPrefix': CRT_PREFIX,
    }
    rootCrontabPath = '/root/proxy.crt'
    sudo('cd /root; openssl req -new -newkey rsa:2048 -x509 -days 365 -nodes -out proxy.pem -keyout proxy.key')
    upload_file('/root/proxy.js', sourcePath='proxy.js', su=True)
    upload_text(rootCrontabPath, PROXY_CRT % d, su=True)
    sudo('crontab %s' % rootCrontabPath)


@task
def prepare_image(stripPrivileges=False):
    # Use only public key authentication
    upload_text('/etc/ssh/sshd_config', SSHD_CONFIG, append=True, su=True)
    # Remove passwords
    sudo('passwd -l %s' % env.user)
    sudo('passwd -l root')
    # Clear history
    clear_history()
    # Clear sensitive information
    sudo('shred %s -fuz' % ' '.join([
        '/etc/ssh/ssh_host_key',
        '/etc/ssh/ssh_host_key.pub',
        '/etc/ssh/ssh_host_dsa_key',
        '/etc/ssh/ssh_host_dsa_key.pub',
        '/etc/ssh/ssh_host_rsa_key',
        '/etc/ssh/ssh_host_rsa_key.pub',
    ]))
    removeAuthorizedKeys = 'find /root /home -name authorized_keys | xargs shred -fuz'
    removeSudoerPrivileges = r"sed -i '/^%(user)s[[:space:]]*ALL/d' /etc/sudoers" % env
    commands = [removeAuthorizedKeys]
    if stripPrivileges:
        commands.append(removeSudoerPrivileges)
    sudo('; '.join(commands))


@task
def prepare_workshop():
    d = {'notebookFolder': f.notebookFolder}
    # Make notebooks read-only and owned by root
    sudo('chown -R root %(notebookFolder)s' % d)
    sudo('chgrp -R root %(notebookFolder)s' % d)
    # Make files readable
    sudo('find %(notebookFolder)s -type f -exec chmod 644 {} \;' % d)
    # Make folders executable
    sudo('find %(notebookFolder)s -type d -exec chmod 755 {} \;' % d)
    # Strip privileges
    prepare_image(stripPrivileges=True)


def install_package(repository_url, repository_name='', yum_install='', customize=None, pip_install='', setup='', setup_env=''):
    repository_path = download(repository_url, repository_name, yum_install, customize)
    d = dict(path=v.path)
    setup = setup % d
    setup_env = setup_env % d
    with virtualenv():
        if pip_install:
            run('pip install --upgrade ' + pip_install)
        with cd(repository_path):
            run('||'.join([
                '%s python setup.py %s develop' % (setup_env, setup),
                '%s python setup.py %s install' % (setup_env, setup)]))


def install_library(
        repository_url, repository_name='',
        yum_install='', customize=None, configure=''):
    repository_path = download(repository_url, repository_name, yum_install, customize)
    configure = configure % dict(path=v.path)
    with virtualenv():
        with cd(repository_path):
            run('./configure --prefix=%s %s' % (v.path, configure))
            run('make install')


def download(repository_url, repository_name='', yum_install='', customize=None):
    if yum_install:
        sudo('yum -y install ' + yum_install)
    if not repository_name:
        repository_name = os.path.splitext(os.path.basename(repository_url))[0].split()[-1]
    clone, pull = get_download_commands(repository_url, repository_name)
    repository_path = os.path.join(v.path, 'opt', repository_name)
    with cd('%s/opt' % v.path):
        if not exists(repository_path):
            run(clone)
    with cd(repository_path):
        pull and run(pull)
        customize and customize(repository_path)
    return repository_path


def get_download_commands(repository_url, repository_name):
    d = dict(url=repository_url, name=repository_name)
    if repository_url.endswith('.git'):
        clone = 'git clone --depth=1 %(url)s %(name)s' % d
        pull = 'git checkout master; git pull --depth=1'
    elif repository_url.endswith('.tar.gz'):
        downloaded_name = os.path.basename(repository_url)
        extracted_name = downloaded_name.replace('.tar.gz', '')
        clone = 'wget %s; tar xzf %s; mv %s %s' % (
            repository_url, downloaded_name, extracted_name, repository_name)
        pull = ''
    elif repository_url.endswith('.tar.bz2'):
        downloaded_name = os.path.basename(repository_url)
        extracted_name = downloaded_name.replace('.tar.bz2', '')
        clone = 'wget %s; tar xjf %s; mv %s %s' % (
            repository_url, downloaded_name, extracted_name, repository_name)
        pull = ''
    else:
        clone = 'svn checkout %(url)s %(name)s' % d
        pull = 'svn upgrade; svn update'
    return clone, pull


def upload_file(targetPath, sourcePath, **kw):
    text = open(sourcePath, 'rt').read()
    upload_text(targetPath, text, **kw)


def upload_text(targetPath, text, append=False, su=False):
    'Note that this will not expand bash variables'
    text = text.replace('\n', '\\n')       # Replace newlines
    text = text.replace('\'', '\'"\'"\'')  # Escape single quotes
    command = sudo if su else run
    command("echo -e '%s' %s %s" % (text, '>>' if append else '>', targetPath))
