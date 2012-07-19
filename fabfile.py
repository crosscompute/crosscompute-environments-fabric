import os
from fabric.api import cd, prefix, run, sudo, task
from fabric.contrib.files import exists


@task
def install(path):
    install_base(path)
    install_ipython(path)
    install_pyramid(path)
    install_numerical(path)
    # install_gpu(path)
    install_computational(path)
    install_geospatial(path)
    # install_node(path)


@task
def install_base(path):
    path = os.path.abspath(path)
    # Prepare directories
    run('mkdir -p %s/opt' % path)
    # Install terminal utilities
    sudo('yum -y install fabric git screen vim-enhanced wget')
    # Install scripts
    def customize(repositoryPath):
        run('./setup')
        sudo('./setup')
    download(path, 'https://github.com/invisibleroads/scripts.git', customize=customize)
    # Install graphical utilities
    sudo('yum -y install libgnome nautilus-open-terminal system-config-firewall vim-X11')
    # Install compilers
    sudo('yum -y install python-virtualenv gcc gcc-c++ gcc-gfortran make swig hg svn')
    # Clean up
    sudo('yum -y remove aisleriot gnome-games')
    sudo('yum -y update')
    # Install packages
    if not exists('%s/bin' % path):
        run('virtualenv --distribute %s' % path)
    with prefix('source %s/bin/activate' % path):
        run('pip install --upgrade coverage distribute fabric nose pylint')


@task
def install_ipython(path):
    install_package(path, 'https://github.com/ipython/ipython.git', yum_install='zeromq-devel', pip_install='pyzmq tornado')
    run('ipython -c "from IPython.external.mathjax import install_mathjax; install_mathjax()"')
    with prefix('source %s/bin/activate' % path):
        run('pip install --upgrade ipdb')


@task
def install_pyramid(path):
    sudo('yum -y install postgresql postgresql-devel postgresql-server libevent-devel')
    with prefix('source %s/bin/activate' % path):
        run('pip install --upgrade archiveIO cryptacular formencode imapIO psycopg2 pycrypto pyramid pyramid_beaker pyramid_debugtoolbar pyramid_mailer pyramid_tm python-openid recaptcha-client simplejson socketIO-client SQLAlchemy transaction waitress webtest whenIO zope.sqlalchemy gevent pika sphinx')


@task
def install_numerical(path):
    install_package(path, 'https://github.com/numpy/numpy.git', yum_install='atlas-devel atlascpp-devel blas-devel lapack-devel')
    install_package(path, 'https://github.com/scipy/scipy.git')
    install_package(path, 'https://github.com/qsnake/h5py.git', yum_install='hdf5-devel')
    install_package(path, 'https://github.com/PyTables/PyTables.git', yum_install='bzip2-devel lzo-devel zlib-devel', pip_install='Cython numexpr')
    install_package(path, 'https://github.com/matplotlib/matplotlib.git', yum_install='freetype-devel libpng-devel tk-devel tkinter')
    install_package(path, 'https://github.com/abate/pydot.git')


@task
def install_gpu(path):
    # cd $VIRTUAL_ENV
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
    # install_package(path, 'https://github.com/inducer/pyopencl.git', customize=customize)
    install_package(path, 'https://github.com/inducer/pycuda.git', customize=customize)


@task
def install_computational(path):
    install_package(path, 'http://pyamg.googlecode.com/svn/trunk', 'pyamg', yum_install='suitesparse-devel')
    install_package(path, 'https://github.com/scikit-learn/scikit-learn.git', yum_install='freetype-devel lcms-devel libjpeg-turbo-devel lyx-fonts tk-devel zlib-devel')
    install_package(path, 'https://github.com/pydata/pandas.git')
    install_package(path, 'https://github.com/statsmodels/statsmodels.git', pip_install='openpyxl xlrd')
    install_package(path, 'https://github.com/networkx/networkx.git')
    install_package(path, 'https://github.com/arruda/pygraphviz.git', yum_install='graphviz-devel')
    install_package(path, 'https://github.com/Theano/Theano.git')


@task
def install_geospatial(path):
    def customize(repositoryPath):
        fileName = 'proj-datumgrid-1.5.zip'
        if not exists(fileName):
            run('wget http://download.osgeo.org/proj/%s' % fileName)
            run('unzip -o -d %s %s' % (os.path.join(repositoryPath, 'nad'), fileName))
    install_library(path, 'http://svn.osgeo.org/metacrs/proj/trunk/proj', yum_install='expat-devel', customize=customize)
    def customize(repositoryPath):
        run('./autogen.sh')
    install_library(path, 'http://svn.osgeo.org/geos/trunk', 'geos', yum_install='autoconf automake libtool', customize=customize, configure='--enable-python')
    install_library(path, 'https://svn.osgeo.org/gdal/trunk/gdal', configure='--with-expat=%(path)s --with-python')
    install_package(path, 'https://github.com/sgillies/shapely.git', setup='build_ext -I %(path)s/include -L %(path)s/lib -l geos_c')
    install_package(path, 'http://pysal.googlecode.com/svn/trunk', 'pysal', yum_install='spatialindex-devel', pip_install='numpydoc rtree')
    with prefix('source %s/bin/activate' % path):
        run('pip install --upgrade geojson geometryIO')


@task
def install_node(path):
    def customize(repositoryPath):
        # Checkout v0.8.2
        run('git checkout cc6084b9ac5cf1d4fe5e7165b71e8fc05d11be1f')
    install_library(path, 'https://github.com/joyent/node.git', yum_install='openssl-devel', customize=customize)
    with prefix('source %s/bin/activate' % path):
        run('npm install -g commander expresso node-inspector should socket.io')


def install_package(path, repositoryURL, repositoryName='', yum_install='', customize=None, pip_install='', setup=''):
    repositoryPath = download(path, repositoryURL, repositoryName, yum_install, customize)
    setup = setup % dict(path=path)
    with prefix('source %s/bin/activate' % path):
        if pip_install:
            run('pip install --upgrade ' + pip_install)
        with cd(repositoryPath):
            run('||'.join([
                'python setup.py %s develop' % setup,
                'python setup.py %s install' % setup,
            ]))


def install_library(path, repositoryURL, repositoryName='', yum_install='', customize=None, configure=''):
    repositoryPath = download(path, repositoryURL, repositoryName, yum_install, customize)
    configure = configure % dict(path=path)
    with prefix('source %s/bin/activate' % path):
        with cd(repositoryPath):
            run('./configure --prefix=%s %s' % (path, configure))
            run('make install')


def download(path, repositoryURL, repositoryName='', yum_install='', customize=None):
    if repositoryURL.endswith('.git'):
        repositoryClone = 'git clone'
        repositoryPull = 'git pull'
    else:
        repositoryClone = 'svn checkout'
        repositoryPull = 'svn update'
    if not repositoryName:
        repositoryName = os.path.splitext(os.path.basename(repositoryURL))[0].split()[-1]
    repositoryPath = os.path.join(path, 'opt', repositoryName)
    if yum_install:
        sudo('yum -y install ' + yum_install)
    with cd('%s/opt' % path):
        if not exists(repositoryPath):
            run('%s %s %s' % (repositoryClone, repositoryURL, repositoryName))
    with cd(repositoryPath):
        run(repositoryPull)
        customize and customize(repositoryPath)
    return repositoryPath
