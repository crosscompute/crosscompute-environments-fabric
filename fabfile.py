import os
from contextlib import contextmanager
from fabric.api import cd, env, prefix, run, sudo, task
from fabric.contrib.files import exists


normalize_path = lambda path: os.path.abspath(os.path.expanduser(os.path.expandvars(path)))
env.virtualenvHome = normalize_path(env.get('virtualenvHome', '~/.virtualenvs'))
env.virtualenvName = env.get('virtualenvName', 'crosscompute')
env.virtualenvPath = os.path.join(env.virtualenvHome, env.virtualenvName)


@contextmanager
def virtualenvwrapper():
    with prefix(
        'export WORKON_HOME=%(virtualenvHome)s;'
        'mkdir -p %(virtualenvPath)s/opt;'
        'source /usr/bin/virtualenvwrapper.sh' % env):
        yield


@contextmanager
def virtualenv():
    with virtualenvwrapper():
        with prefix('workon ' + env.virtualenvName):
            yield


@task(default=True)
def install():
    install_base()
    install_ipython()
    install_pyramid()
    install_numerical()
    # install_gpu()
    install_computational()
    install_geospatial()
    # install_node()


@task
def install_base():
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
    install_package('https://github.com/ipython/ipython.git', yum_install='zeromq-devel', pip_install='pyzmq tornado')
    with virtualenv():
        run('ipython -c "from IPython.external.mathjax import install_mathjax; install_mathjax()"')
        run('pip install --upgrade ipdb')


@task
def install_pyramid():
    sudo('yum -y install postgresql postgresql-devel postgresql-server libevent-devel')
    with virtualenv():
        run('pip install --upgrade archiveIO cryptacular formencode imapIO psycopg2 pyramid pyramid_beaker pyramid_debugtoolbar pyramid_mailer pyramid_tm python-openid recaptcha-client simplejson socketIO-client SQLAlchemy transaction waitress webtest whenIO zope.sqlalchemy gevent pika sphinx')


@task
def install_numerical():
    install_package('https://github.com/numpy/numpy.git', yum_install='atlas-devel atlascpp-devel blas-devel lapack-devel')
    install_package('https://github.com/scipy/scipy.git')
    install_package('https://github.com/qsnake/h5py.git', yum_install='hdf5-devel')
    install_package('https://github.com/PyTables/PyTables.git', yum_install='bzip2-devel lzo-devel zlib-devel', pip_install='Cython numexpr')
    install_package('https://github.com/matplotlib/matplotlib.git', yum_install='freetype-devel libpng-devel tk-devel tkinter')
    install_package('https://github.com/abate/pydot.git')


@task
def install_gpu():
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
    install_package('http://pyamg.googlecode.com/svn/trunk', 'pyamg', yum_install='suitesparse-devel')
    install_package('https://github.com/scikit-learn/scikit-learn.git', yum_install='freetype-devel lcms-devel libjpeg-turbo-devel lyx-fonts tk-devel zlib-devel')
    install_package('https://github.com/pydata/pandas.git')
    install_package('https://github.com/statsmodels/statsmodels.git', pip_install='openpyxl xlrd')
    install_package('https://github.com/networkx/networkx.git')
    install_package('https://github.com/arruda/pygraphviz.git', yum_install='graphviz-devel')
    install_package('https://github.com/Theano/Theano.git')


@task
def install_geospatial():
    def customize(repositoryPath):
        fileName = 'proj-datumgrid-1.5.zip'
        if not exists(fileName):
            run('wget http://download.osgeo.org/proj/%s' % fileName)
            run('unzip -o -d %s %s' % (os.path.join(repositoryPath, 'nad'), fileName))
    install_library('http://svn.osgeo.org/metacrs/proj/trunk/proj', yum_install='expat-devel', customize=customize)
    def customize(repositoryPath):
        run('./autogen.sh')
    install_library('http://svn.osgeo.org/geos/trunk', 'geos', yum_install='autoconf automake libtool', customize=customize, configure='--enable-python')
    install_library('https://svn.osgeo.org/gdal/trunk/gdal', configure='--with-expat=%(path)s --with-python')
    install_package('https://github.com/sgillies/shapely.git', setup='build_ext -I %(path)s/include -L %(path)s/lib -l geos_c')
    install_package('http://pysal.googlecode.com/svn/trunk', 'pysal', yum_install='spatialindex-devel', pip_install='numpydoc rtree')
    with virtualenv():
        run('pip install --upgrade geojson geometryIO')


@task
def install_node():
    def customize(repositoryPath):
        run('git checkout b88c3902b241cf934e75443b934f2033ad3915b1') # v0.8.9
    install_library('https://github.com/joyent/node.git', yum_install='openssl-devel', customize=customize)
    with virtualenv():
        run('npm install -g commander expresso http-proxy node-inspector should socket.io')


def install_package(repositoryURL, repositoryName='', yum_install='', customize=None, pip_install='', setup=''):
    repositoryPath = download(repositoryURL, repositoryName, yum_install, customize)
    setup = setup % dict(path=env.virtualenvPath)
    with virtualenv():
        if pip_install:
            run('pip install --upgrade ' + pip_install)
        with cd(repositoryPath):
            run('||'.join([
                'python setup.py %s develop' % setup,
                'python setup.py %s install' % setup,
            ]))


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
