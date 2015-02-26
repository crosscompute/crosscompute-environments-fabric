import os
from contextlib import contextmanager
from fabric.api import cd, env, prefix, run, settings, sudo, task
from fabric.contrib.files import exists


class V(object):

    @property
    def home(self):
        home = os.path.split(os.getenv('ENV', ''))[0]
        return home or ('/home/%s/.virtualenvs' % env.user)

    @property
    def name(self):
        name = os.path.split(os.getenv('ENV', ''))[1]
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
            self.userFolder, '.ipython', 'profile_%s' % IPYTHON_PROFILE_NAME)

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
        'export VIRTUALENVWRAPPER_PYTHON=`which python27 || which python2.7`',
        'export VIRTUALENVWRAPPER_VIRTUALENV=`which virtualenv-2.7`',
        'export LD_LIBRARY_PATH=%s/lib:/usr/local/lib' % v.path,
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
    # install_node()


@task
def install_base():
    'Install base applications and packages'
    d = {
        'virtualenv.home': v.home,
        'virtualenv.path': v.path,
        'user': env.user,
    }
    print d
    with settings(warn_only=True):
        sudo("sed -i 's/enabled=0/enabled=1/' /etc/yum.repos.d/epel.repo")
    sudo('yum -y install deltarpm')
    sudo('yum -y install tmux git')
    sudo('yum -y install wget tar unzip bzip2 which at')
    sudo('yum -y install python-devel python27-devel python-virtualenvwrapper')
    with settings(warn_only=True):
        sudo('rm -rf /usr/lib/python2.7/site-packages/setuptools*')
    run('wget https://bootstrap.pypa.io/ez_setup.py -O /tmp/ez_setup.py')
    sudo('python2.7 /tmp/ez_setup.py')
    sudo('easy_install-2.7 pip')
    sudo('rm /home/%s/setuptools-*.zip' % env.user)
    sudo('pip2.7 install --upgrade virtualenvwrapper')
    # Install terminal utilities
    sudo('mkdir -p %(virtualenv.path)s/opt' % d)
    sudo('chown -R %(user)s %(virtualenv.home)s' % d)
    sudo('chgrp -R %(user)s %(virtualenv.home)s' % d)
    with virtualenvwrapper():
        run('mkvirtualenv --python /usr/bin/python2.7 --system-site-packages %s' % v.name)
    # Install scripts
    def customize(repository_path):
        run(r"sed -i 's/WORKON_HOME=$HOME\/.virtualenvs/WORKON_HOME=%s/' .bashrc" % v.home.replace('/', '\/'))
        run('./setup %s' % v.name)
        sudo('./setup %s' % v.name)
    download('https://github.com/invisibleroads/scripts.git', customize=customize)
    sudo('yum -y update')
    # Install graphical utilities
    with settings(warn_only=True):
        sudo('yum -y install libgnome nautilus-open-terminal vim-X11 xcalib')
    # Install compilers
    sudo('yum -y install gcc gcc-c++ gcc-gfortran make libtool swig hg svn')
    # Clean up
    with settings(warn_only=True):
        sudo('yum -y install aiksaurus')
        sudo('yum -y remove aisleriot gnome-games')
    # Install packages
    with virtualenv():
        run('pip install --upgrade coverage mock nose flake8')
    sudo('yum -y install vim-enhanced expect')


@task
def install_ipython():
    'Install IPython computing environment'
    def customize_zmq(repository_path):
        run('bash autogen.sh')
    install_library('https://github.com/zeromq/libzmq.git', 'zmq', yum_install='libsodium-devel', customize=customize_zmq, globally=True)
    with virtualenv():
        run('pip install --upgrade pyzmq tornado')
        run('pip install --upgrade ipython')
        run('pip install --upgrade ipdb')
        run('ipython -c "from IPython.external.mathjax import install_mathjax; install_mathjax()"')
    # with cd('%s/opt' % v.path):
        # run('git clone --depth=1 git@github.com:nsonnad/base16-ipython-notebook.git')
        # run('ln -sf %s/opt/base16-ipython-notebook/base16-default-dark.css ~/.ipython/profile_default/static/custom/custom.css' % v.path)


@task
def install_pyramid():
    'Install Pyramid web framework'
    sudo('yum -y install pandoc redis')
    with virtualenv():
        run('pip install --upgrade sqlalchemy formencode simplejson sphinx transaction waitress webtest')
        run('pip install --upgrade dogpile.cache pyramid pypandoc velruse zope.sqlalchemy')
        run('pip install --upgrade archiveIO imapIO pyramid_debugtoolbar pyramid_mailer pyramid_tm python-openid rq voluptuous whenIO')
        run('pip install --upgrade bleach markdown flask')


@task
def install_textual():
    with virtualenv():
        run('pip install --upgrade beautifulsoup4')


@task
def install_numerical():
    'Install numerical packages'
    # def customize_freetype(repository_path):
        # run('bash autogen.sh')
    # install_library('http://download.savannah.gnu.org/releases/freetype/freetype-2.5.3.tar.gz', 'freetype', customize=customize_freetype, globally=True)
    sudo('yum -y install hdf5 hdf5-devel')
    sudo('yum -y install GraphicsMagick libjpeg-devel libpng-devel')
    sudo('yum -y install blas-devel lapack-devel')
    sudo('yum -y install numpy scipy python-matplotlib sympy pydot')
    sudo('yum -y install freetype-devel bzip2-devel lzo-devel zlib-devel')
    packages = [
        'Cython',
        'psutil',
        'numpy',
        'scipy',
        'matplotlib',
        'numexpr',
        'pandas',
        'pillow',
        'h5py',
        'openpyxl',
        'xlrd',
        'xlwt',
        'tables',
        'memory_profiler',
        'objgraph',
    ]
    with virtualenv():
        with settings(warn_only=True):
            for package in packages:
                run('pip install --upgrade %s' % package)
    with settings(warn_only=True):
        install_package('https://github.com/certik/line_profiler.git')


@task
def install_computational():
    'Install computational packages'
    sudo('yum -y install graphviz-python')
    install_package('http://pyamg.googlecode.com/svn/trunk', 'pyamg', yum_install='suitesparse-devel')
    # install_package('https://github.com/Theano/Theano.git')
    # install_package('https://github.com/lisa-lab/pylearn2.git')
    packages = [
        'scikit-learn',
        'networkx',
        'Bottleneck',
        'patsy',
        'statsmodels',
    ]
    with settings(warn_only=True):
        with virtualenv():
            for package in packages:
                run('pip install --upgrade %s' % package)


@task
def install_spatial():
    'Install spatial packages'
    def customize_proj(repository_path):
        fileName = 'proj-datumgrid-1.5.zip'
        if not exists(fileName):
            run('wget http://download.osgeo.org/proj/%s' % fileName)
            run('unzip -o -d %s %s' % (os.path.join(repository_path, 'nad'), fileName))
    install_library('http://download.osgeo.org/proj/proj-4.8.0.tar.gz', 'proj', yum_install='expat-devel', customize=customize_proj, globally=True)
    install_library('http://download.osgeo.org/geos/geos-3.4.2.tar.bz2', 'geos', yum_install='autoconf automake libtool', configure='--enable-python', globally=True)
    install_library('http://download.osgeo.org/gdal/1.11.1/gdal-1.11.1.tar.gz', 'gdal', configure='--with-expat=%(path)s --with-python', globally=True)
    install_library('http://download.osgeo.org/libspatialindex/spatialindex-src-1.8.1.tar.gz', 'spatialindex', globally=True)
    sudo('chown %s %s/lib/python2.7/site-packages/easy-install.pth' % (env.user, v.path))
    sudo('chgrp %s %s/lib/python2.7/site-packages/easy-install.pth' % (env.user, v.path))
    install_package('https://github.com/Toblerity/Shapely.git', 'shapely')
    install_package('http://pysal.googlecode.com/svn/trunk', 'pysal', pip_install='numpydoc rtree')
    install_package('https://github.com/matplotlib/basemap.git')
    with virtualenv():
        run('pip install --upgrade geojson geometryIO fiona rasterio pykdtree utm')


@task
def install_node():
    'Install node.js server'
    install_library('http://nodejs.org/dist/v0.12.0/node-v0.12.0.tar.gz', 'node', yum_install='openssl-devel')
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
        yum_install='', customize=None, configure='', globally=False):
    repository_path = download(repository_url, repository_name, yum_install, customize)
    configure = configure % dict(path=v.path)
    with virtualenv():
        with cd(repository_path):
            # run('make clean')
            if globally:
                run('./configure %s' % configure)
                run('make')
                sudo('make install')
            else:
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
