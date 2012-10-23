import os
from contextlib import contextmanager
from fabric.api import cd, env, prefix, run, settings, sudo, task
from fabric.contrib.files import exists


class V(object):

    @property
    def home(self):
        return env.get('virtualenv.home', '/home/%s/.virtualenvs' % env.user)

    @property
    def name(self):
        return env.get('virtualenv.name', 'crosscompute')

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
        return os.path.join(self.userFolder, '.ipython', 'profile_%s' % IPYTHON_PROFILE_NAME)

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
Protocol 2
PermitRootLogin without-password
PubkeyAuthentication yes
PasswordAuthentication no
ChallengeResponseAuthentication no
UsePAM no
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
    # install_gpu()
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
    # Install terminal utilities
    sudo('yum -y install vim-enhanced screen git wget tar unzip fabric python-virtualenvwrapper')
    sudo('mkdir -p %(virtualenv.path)s/opt' % d)
    sudo('chown -R %(user)s %(virtualenv.home)s' % d)
    sudo('chgrp -R %(user)s %(virtualenv.home)s' % d)
    with virtualenvwrapper():
        run('mkvirtualenv %s' % v.name)

    # Install scripts
    def customize(repositoryPath):
        run(r"sed -i 's/^WORKON_HOME=$HOME\/.virtualenvs/WORKON_HOME=%s/' .bashrc" % v.home.replace('/', '\/'))
        run(r"sed -i 's/^workon crosscompute/workon %s/' .bashrc" % v.name)
        run('./setup')
        sudo('./setup')
    download('https://github.com/invisibleroads/scripts.git', customize=customize)
    # Install graphical utilities
    sudo('yum -y install libgnome nautilus-open-terminal system-config-firewall vim-X11 xcalib')
    # Install compilers
    sudo('yum -y install gcc gcc-c++ gcc-gfortran make swig hg svn')
    # Clean up
    sudo('yum -y remove aisleriot gnome-games')
    sudo('yum -y update')
    # Install packages
    with virtualenv():
        run('pip install --upgrade coverage distribute fabric nose pylint')


@task
def install_ipython():
    'Install IPython computing environment'
    install_package('https://github.com/ipython/ipython.git', yum_install='zeromq-devel', pip_install='pyzmq tornado')
    with virtualenv():
        run('ipython -c "from IPython.external.mathjax import install_mathjax; install_mathjax()"')
        run('pip install --upgrade ipdb')


@task
def install_pyramid():
    'Install Pyramid web framework'
    sudo('yum -y install postgresql postgresql-devel postgresql-server libevent-devel')
    with virtualenv():
        run('pip install --upgrade archiveIO cryptacular dogpile.cache formencode imapIO psycopg2 pyramid pyramid_beaker pyramid_debugtoolbar pyramid_mailer pyramid_tm python-openid recaptcha-client simplejson socketIO-client SQLAlchemy transaction waitress webtest whenIO zope.sqlalchemy gevent pika sphinx')


@task
def install_textual():
    with virtualenv():
        run('pip install --upgrade beautifulsoup4')


@task
def install_numerical():
    'Install numerical packages'
    sudo('yum -y install GraphicsMagick')
    install_package('https://github.com/numpy/numpy.git', yum_install='atlas-devel atlascpp-devel blas-devel lapack-devel')
    install_package('https://github.com/scipy/scipy.git')
    install_package('https://github.com/qsnake/h5py.git', yum_install='hdf5-devel')
    install_package('https://github.com/PyTables/PyTables.git', yum_install='bzip2-devel lzo-devel zlib-devel', pip_install='Cython numexpr')
    install_package('https://github.com/matplotlib/matplotlib.git', yum_install='freetype-devel libpng-devel tk-devel tkinter')
    install_package('https://github.com/abate/pydot.git')


@task
def install_gpu():
    'Install GPU packages'
    # workon crosscompute
    # cd $VIRTUAL_ENV/opt/cuda
    # wget http://developer.download.nvidia.com/compute/cuda/4_2/rel/drivers/devdriver_4.2_linux_32_295.41.run
    # wget http://developer.download.nvidia.com/compute/cuda/4_2/rel/toolkit/cudatoolkit_4.2.9_linux_32_fedora14.run
    # wget http://developer.download.nvidia.com/compute/cuda/4_2/rel/sdk/gpucomputingsdk_4.2.9_linux.run
    # chmod a+x *
    # lspci |grep -i VGA
    # sudo mv /boot/initramfs-$(uname -r).img /boot/initramfs-$(uname -r)-nouveau.img
    # sudo dracut /boot/initramfs-$(uname -r).img $(uname -r)
    # sudo yum -y install kernel-devel
    # sudo init 3
    # sudo ./devdriver_4.2_linux_32_295.41.run
    # ./cudatoolkit_4.2.9_linux_32_fedora14.run # $VIRTUAL_ENV/opt
    # ./gpucomputingsdk_4.2.9_linux.run # $VIRTUAL_ENV/opt/cuda-sdk
    # sudo yum -y install freeglut-devel libXmu-devel mesa-libGLU-devel libXi-devel
    def customize(repositoryPath):
        run('git submodule init')
        run('git submodule update')
        run('python configure.py')
    # install_package('https://github.com/inducer/pyopencl.git', customize=customize)
    install_package('https://github.com/inducer/pycuda.git', customize=customize)


@task
def install_computational():
    'Install computational packages'
    install_package('http://pyamg.googlecode.com/svn/trunk', 'pyamg', yum_install='suitesparse-devel')
    install_package('https://github.com/scikit-learn/scikit-learn.git', yum_install='freetype-devel lcms-devel libjpeg-turbo-devel lyx-fonts tk-devel zlib-devel')
    install_package('https://github.com/pydata/pandas.git')
    install_package('https://github.com/statsmodels/statsmodels.git', pip_install='openpyxl xlrd patsy')
    install_package('https://github.com/networkx/networkx.git')
    install_package('https://github.com/arruda/pygraphviz.git', yum_install='graphviz-devel')
    install_package('https://github.com/Theano/Theano.git')


@task
def install_spatial():
    'Install spatial packages'
    def customize_proj(repositoryPath):
        fileName = 'proj-datumgrid-1.5.zip'
        if not exists(fileName):
            run('wget http://download.osgeo.org/proj/%s' % fileName)
            run('unzip -o -d %s %s' % (os.path.join(repositoryPath, 'nad'), fileName))
    install_library('http://svn.osgeo.org/metacrs/proj/trunk/proj', yum_install='expat-devel', customize=customize_proj)

    def customize_geos(repositoryPath):
        run('./autogen.sh')
    install_library('http://svn.osgeo.org/geos/trunk', 'geos', yum_install='autoconf automake libtool', customize=customize_geos, configure='--enable-python')
    install_library('https://svn.osgeo.org/gdal/trunk/gdal', configure='--with-expat=%(path)s --with-python')
    install_package('https://github.com/sgillies/shapely.git', setup='build_ext -I %(path)s/include -L %(path)s/lib -l geos_c')
    install_package('http://pysal.googlecode.com/svn/trunk', 'pysal', yum_install='spatialindex-devel', pip_install='numpydoc rtree')
    with virtualenv():
        run('pip install --upgrade geojson geometryIO')


@task
def install_node():
    'Install node.js server'
    def customize(repositoryPath):
        run('git checkout e1f39468fa580c1e4cb15fac621f87944ee625dc')  # v0.8.11
    install_library('https://github.com/joyent/node.git', yum_install='openssl-devel', customize=customize)
    with virtualenv():
        run('npm install -g commander expresso http-proxy node-inspector should socket.io')
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
        run('git clone https://github.com/invisibleroads/%s.git' % NOTEBOOK_REPOSITORY_NAME)
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


def install_package(repositoryURL, repositoryName='', yum_install='', customize=None, pip_install='', setup=''):
    repositoryPath = download(repositoryURL, repositoryName, yum_install, customize)
    setup = setup % dict(path=v.path)
    with virtualenv():
        if pip_install:
            run('pip install --upgrade ' + pip_install)
        with cd(repositoryPath):
            run('||'.join([
                'python setup.py %s develop' % setup,
                'python setup.py %s install' % setup]))


def install_library(repositoryURL, repositoryName='', yum_install='', customize=None, configure=''):
    repositoryPath = download(repositoryURL, repositoryName, yum_install, customize)
    configure = configure % dict(path=v.path)
    with virtualenv():
        with cd(repositoryPath):
            run('./configure --prefix=%s %s' % (v.path, configure))
            run('make install')


def download(repositoryURL, repositoryName='', yum_install='', customize=None):
    if repositoryURL.endswith('.git'):
        repositoryClone = 'git clone'
        repositoryPull = 'git checkout master; git pull'
    else:
        repositoryClone = 'svn checkout'
        repositoryPull = 'svn update'
    if not repositoryName:
        repositoryName = os.path.splitext(os.path.basename(repositoryURL))[0].split()[-1]
    repositoryPath = os.path.join(v.path, 'opt', repositoryName)
    if yum_install:
        sudo('yum -y install ' + yum_install)
    with cd('%s/opt' % v.path):
        if not exists(repositoryPath):
            run('%s %s %s' % (repositoryClone, repositoryURL, repositoryName))
    with cd(repositoryPath):
        run(repositoryPull)
        customize and customize(repositoryPath)
    return repositoryPath


def upload_text(targetPath, text, append=False, su=False):
    'Note that this will not expand bash variables'
    text = text.replace('\n', '\\n')       # Replace newlines
    text = text.replace('\'', '\'"\'"\'')  # Escape single quotes
    command = sudo if su else run
    command("echo -e '%s' %s %s" % (text, '>>' if append else '>', targetPath))


def upload_file(targetPath, sourcePath, **kw):
    text = open(sourcePath, 'rt').read()
    upload_text(targetPath, text, **kw)
