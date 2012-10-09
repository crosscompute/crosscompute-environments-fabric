import os
from contextlib import contextmanager
from fabric.api import cd, env, prefix, run, settings, sudo, task
from fabric.contrib.files import exists


normalize_path = lambda path: os.path.abspath(os.path.expanduser(os.path.expandvars(path)))
env.virtualenvHome = normalize_path(env.get('virtualenvHome', '~/.virtualenvs'))
env.virtualenvName = env.get('virtualenvName', 'crosscompute')
env.virtualenvPath = os.path.join(env.virtualenvHome, env.virtualenvName)
ipythonProfileName = 'server'


@contextmanager
def virtualenvwrapper():
    commandLines = [
        'export WORKON_HOME=%s' % env.virtualenvHome,
        'mkdir -p %s/opt' % env.virtualenvPath,
        'source /usr/bin/virtualenvwrapper.sh' % env,
    ]
    with prefix('; '.join(commandLines)):
        yield


@contextmanager
def virtualenv():
    with virtualenvwrapper():
        with prefix('workon ' + env.virtualenvName):
            yield


@task(default=True)
def install():
    'Install scientific computing environment'
    install_base()
    install_ipython()
    install_pyramid()
    install_numerical()
    # install_gpu()
    install_computational()
    install_geospatial()
    # install_node()
    # configure_ipython_notebook()


@task
def install_base():
    'Install base applications and packages'
    # Install terminal utilities
    sudo('yum -y install vim-enhanced screen git wget tar unzip fabric python-virtualenvwrapper')
    with virtualenvwrapper():
        run('mkvirtualenv ' + env.virtualenvName)

    # Install scripts
    def customize(repositoryPath):
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
        run('pip install --upgrade archiveIO cryptacular formencode imapIO psycopg2 pyramid pyramid_beaker pyramid_debugtoolbar pyramid_mailer pyramid_tm python-openid recaptcha-client simplejson socketIO-client SQLAlchemy transaction waitress webtest whenIO zope.sqlalchemy gevent pika sphinx')


@task
def install_numerical():
    'Install numerical packages'
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
    install_package('https://github.com/statsmodels/statsmodels.git', pip_install='openpyxl xlrd')
    install_package('https://github.com/networkx/networkx.git')
    install_package('https://github.com/arruda/pygraphviz.git', yum_install='graphviz-devel')
    install_package('https://github.com/Theano/Theano.git')


@task
def install_geospatial():
    'Install geospatial packages'
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


@task
def configure_ipython_notebook():
    'Configure IPython Notebook server'
    print 'Please specify a password for your IPython server'
    from IPython.lib import passwd
    ipythonPassword = passwd()
    # Set folders
    userFolder = run('echo $HOME')
    documentFolder = os.path.join(userFolder, 'Documents')
    profileFolder = os.path.join(userFolder, '.ipython', 'profile_%s' % ipythonProfileName)
    securityFolder = os.path.join(profileFolder, 'security')
    # Set paths
    certificatePath = os.path.join(securityFolder, 'ssl.pem')
    userCrontabPath = os.path.join(profileFolder, 'server.crt')
    rootCrontabPath = '/root/proxy.crt'
    logPath = os.path.join(profileFolder, 'log', 'server.log')
    run('rm -Rf %s %s' % (profileFolder, documentFolder))
    # Download documents
    run('mkdir -p %s' % documentFolder)
    with cd(documentFolder):
        run('git clone https://github.com/invisibleroads/crosscompute-tutorials.git')
    # Create profile
    with virtualenv():
        run('ipython profile create %s' % ipythonProfileName)
    # Generate certificate
    with cd(securityFolder):
        run('openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout ssl.pem -out ssl.pem')
    # Configure server
    upload_lines(os.path.join(profileFolder, 'ipython_notebook_config.py'), [
        "",
        "# Custom configuration",
        "c.NotebookApp.certfile = u'%s'" % certificatePath,
        "c.NotebookApp.open_browser = False",
        "c.NotebookApp.password = u'%s'" % ipythonPassword,
        "c.NotebookApp.port = 8888",
        "c.NotebookApp.port_retries = 0",
        "c.IPKernelApp.pylab = u'inline'",
    ], append=True)
    # Add crontab
    upload_lines(userCrontabPath, [
        "* * * * * %s" % '; '.join([
            'source %s/bin/activate' % env.virtualenvPath,
            'export LD_LIBRARY_PATH=%s/lib' % env.virtualenvPath,
            'export NODE_PATH=%s/lib/node_modules' % env.virtualenvPath,
            'cd %s/Documents/crosscompute-tutorials' % userFolder,
            'ipython notebook --profile=server >> %s 2>&1' % logPath,
        ]),
    ])
    run('crontab %s' % userCrontabPath)
    # Setup proxy
    sudo('cd /root; openssl req -new -newkey rsa:2048 -x509 -days 365 -nodes -out proxy.pem -keyout proxy.key')
    upload_file('/root/proxy.js', sourcePath='proxy.js', su=True)
    upload_lines(rootCrontabPath, [
        "* * * * * %s" % '; '.join([
            'source %s/bin/activate' % env.virtualenvPath,
            'export LD_LIBRARY_PATH=%s/lib' % env.virtualenvPath,
            'export NODE_PATH=%s/lib/node_modules' % env.virtualenvPath,
            'cd /root',
            'node proxy.js >> proxy.log 2>&1'
        ]),
    ], su=True)
    sudo('crontab %s' % rootCrontabPath)
    # Open ports
    upload_file('/etc/sysconfig/iptables', sourcePath='iptables', su=True)


@task
def refresh_ami():
    'Clear logs and bash history'
    sudo('yum -y update')
    run('rm -Rf tmp')
    userFolder = run('echo $HOME')
    profileFolder = os.path.join(userFolder, '.ipython', 'profile_%s' % ipythonProfileName)
    shred = lambda path: sudo('shred %s -fuz' % path)
    with settings(warn_only=True):
        shred(os.path.join(userFolder, '.bash_history'))
        shred(os.path.join(profileFolder, 'history.sqlite'))
        shred(os.path.join(profileFolder, 'log', 'server.log'))
        shred('/root/.bash_history')
        shred('/root/proxy.log')
    sudo('history -c')
    run('history -c')


@task
def prepare_ami():
    'Prepare AMI for public release'
    refresh_ami()
    # Use only public key authentication
    upload_lines('/etc/ssh/sshd_config', [
        'PermitRootLogin without-password',
        'PubkeyAuthentication yes',
        'PasswordAuthentication no',
        'UseDNS no',
    ], append=True, su=True)
    # Remove passwords
    sudo('passwd -l %s' % run('eval whoami'))
    sudo('passwd -l root')
    # Clear sensitive information
    sudo('shred %s -fuz' % ' '.join([
        '/etc/ssh/ssh_host_key',
        '/etc/ssh/ssh_host_key.pub',
        '/etc/ssh/ssh_host_dsa_key',
        '/etc/ssh/ssh_host_dsa_key.pub',
        '/etc/ssh/ssh_host_rsa_key',
        '/etc/ssh/ssh_host_rsa_key.pub',
    ]))
    sudo('find /root /home -name authorized_keys | xargs shred -fuz')


def install_package(repositoryURL, repositoryName='', yum_install='', customize=None, pip_install='', setup=''):
    repositoryPath = download(repositoryURL, repositoryName, yum_install, customize)
    setup = setup % dict(path=env.virtualenvPath)
    with virtualenv():
        if pip_install:
            run('pip install --upgrade ' + pip_install)
        with cd(repositoryPath):
            run('||'.join([
                'python setup.py %s develop' % setup,
                'python setup.py %s install' % setup]))


def install_library(repositoryURL, repositoryName='', yum_install='', customize=None, configure=''):
    repositoryPath = download(repositoryURL, repositoryName, yum_install, customize)
    configure = configure % dict(path=env.virtualenvPath)
    with virtualenv():
        with cd(repositoryPath):
            run('./configure --prefix=%s %s' % (env.virtualenvPath, configure))
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
    repositoryPath = os.path.join(env.virtualenvPath, 'opt', repositoryName)
    if yum_install:
        sudo('yum -y install ' + yum_install)
    with cd('%s/opt' % env.virtualenvPath):
        if not exists(repositoryPath):
            run('%s %s %s' % (repositoryClone, repositoryURL, repositoryName))
    with cd(repositoryPath):
        run(repositoryPull)
        customize and customize(repositoryPath)
    return repositoryPath


def upload_lines(targetPath, lines, append=False, su=False):
    command = sudo if su else run
    command('echo -e "%s" %s %s' % ('\\n'.join(lines), '>>' if append else '>', targetPath))


def upload_file(targetPath, sourcePath, **kw):
    lines = open(sourcePath, 'rt').read().splitlines()  # readlines() keeps newlines
    upload_lines(targetPath, lines, **kw)
