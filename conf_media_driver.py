# Copyright (c) 2019-2020 Intel Corporation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from pathlib import Path

DRIVER_REPO_NAME = 'media-driver'

DRIVER_REPO_DIR = options.get('REPOS_DIR') / DRIVER_REPO_NAME
BUILD_NUM = get_commit_number(DRIVER_REPO_DIR)

DRIVER_VERSION = manifest.get_component(DRIVER_REPO_NAME).version
DRIVER_PKG_VERSION = DRIVER_VERSION + f'.{BUILD_NUM}'


DEPENDENCIES = [
    'libva',
    'gmmlib'
]

# Workaround to run fpm tool on CentOS 6.9
ENABLE_RUBY24 = 'source /opt/rh/rh-ruby24/enable'
GCC_LATEST = '10'
CLANG_VERSION = '10'
options["STRIP_BINARIES"] = True

DRIVER_INSTALL_PREFIX = Path('/opt/intel/msdk_driver')
# Installation by default: /opt/intel/msdk_driver/lib64
DRIVER_LIB_DIR = 'lib64'


def set_env(gcc_latest, clang_version):
    compiler_version = args.get('compiler_version')
    if args.get('compiler') == "gcc" and compiler_version == gcc_latest:
        # TODO: Add possibility to choose other gcc versions
        options["ENV"]['CC'] = '/usr/bin/gcc-10'
        options["ENV"]['CXX'] = '/usr/bin/g++-10'

    elif args.get('compiler') == "clang" and compiler_version == clang_version:
        options["ENV"]['CC'] = f'/usr/bin/clang-{compiler_version}'
        options["ENV"]['CXX'] = f'/usr/bin/clang++-{compiler_version}'


action('set CC and CXX environment variables',
       callfunc=(set_env, [GCC_LATEST, CLANG_VERSION], {}))


cmake_command = [
    'cmake3',
    f'-DMEDIA_VERSION="{DRIVER_VERSION}"',
    f'-DCMAKE_INSTALL_PREFIX={DRIVER_INSTALL_PREFIX}',
    # By default install driver to /opt/intel/msdk_driver
    f'-DCMAKE_INSTALL_LIBDIR={DRIVER_INSTALL_PREFIX / DRIVER_LIB_DIR}',
    f'-DCMAKE_SKIP_RPATH=TRUE',
    f'-DINSTALL_DRIVER_SYSCONF=OFF',
    # Path contains iHD_drv_video.so
    f'-DLIBVA_DRIVERS_PATH={DRIVER_INSTALL_PREFIX / DRIVER_LIB_DIR}',
    f'-DBUILD_TYPE={options["BUILD_TYPE"]}',
]

if product_type == 'public_linux_driver_kernels_off':
    cmake_command.append('-DENABLE_KERNELS=OFF')
elif product_type == 'public_linux_driver_nonfree_kernels_off':
    cmake_command.append('-DENABLE_NONFREE_KERNELS=OFF')

cmake_command.append(str(DRIVER_REPO_DIR))

cmake = ' '.join(cmake_command)

# Prepare dependencies
# Libva
LIBVA_PATH = options['DEPENDENCIES_DIR'] / 'libva' / 'usr' / 'local'
LIBVA_PKG_CONFIG_PATH = LIBVA_PATH / 'lib64' / 'pkgconfig'
LIBVA_PKG_CONFIG_RPM_PATTERN = {
    '^prefix=.+': f'prefix={LIBVA_PATH}',
}
action('LibVA: change pkgconfigs',
       stage=stage.EXTRACT,
       callfunc=(update_config, [LIBVA_PKG_CONFIG_PATH, LIBVA_PKG_CONFIG_RPM_PATTERN], {}))

# Gmmlib
GMMLIB_PATH = options['DEPENDENCIES_DIR'] / 'gmmlib' / 'usr' / 'local'
GMMLIB_PKG_CONFIG_PATH = GMMLIB_PATH / 'lib64' / 'pkgconfig'
GMMLIB_PKG_CONFIG_RPM_PATTERN = {
    '^prefix=.+': f'prefix={GMMLIB_PATH}',
    '^includedir=.+': f'includedir={GMMLIB_PATH}/include/igdgmm',
    '^libdir=.+': f'libdir={GMMLIB_PATH}/lib64'
}

action('Gmmlib: change pkgconfigs',
       stage=stage.EXTRACT,
       callfunc=(update_config, [GMMLIB_PKG_CONFIG_PATH, GMMLIB_PKG_CONFIG_RPM_PATTERN], {}))


# Build Media Driver
action('media-driver: cmake',
       work_dir=options['BUILD_DIR'],
       cmd=cmake,
       env={'PKG_CONFIG_PATH': f'{LIBVA_PKG_CONFIG_PATH}:{GMMLIB_PKG_CONFIG_PATH}'})

options["LD_LIBRARY_PATH"] = f'{options["BUILD_DIR"]}/media_driver:{GMMLIB_PATH}/lib64'
action('media-driver: build',
       cmd=f'LD_LIBRARY_PATH={options["LD_LIBRARY_PATH"]} make -j`nproc`')

action('media-driver: list artifacts',
       cmd=f'echo " " && ls ./media_driver',
       verbose=True)

action('media-driver: make install',
       stage=stage.INSTALL,
       work_dir=options['BUILD_DIR'],
       cmd=f'LD_LIBRARY_PATH={options["LD_LIBRARY_PATH"]} make DESTDIR={options["INSTALL_DIR"]} install')

# Create configuration files
intel_mediasdk_file = options["INSTALL_DIR"] / 'intel-mediasdk.sh'
data = '# add libva driver path/name exporting for intel media solution\n'\
       'export LIBVA_DRIVERS_PATH=/opt/intel/msdk_driver/lib64\n'\
       'export LIBVA_DRIVER_NAME=iHD'

action('create intel-mediasdk.sh',
       stage=stage.INSTALL,
       callfunc=(create_file, [intel_mediasdk_file, data], {}))

# Get package installation dir for media-driver
pack_dir = options['INSTALL_DIR'] / DRIVER_INSTALL_PREFIX.relative_to(DRIVER_INSTALL_PREFIX.root)

DRIVER_PACK_DIRS = [
    f'{pack_dir}/lib64/={DRIVER_INSTALL_PREFIX / DRIVER_LIB_DIR }',
    f'{pack_dir}/include/={DRIVER_INSTALL_PREFIX}/include',
    f'{options["INSTALL_DIR"]}/intel-mediasdk.sh=/etc/profile.d/',
]

action('media-driver: create rpm pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('rpm', DRIVER_PACK_DIRS, ENABLE_RUBY24, DRIVER_PKG_VERSION, DRIVER_REPO_NAME.lower()))


action('media-driver: create deb pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('deb', DRIVER_PACK_DIRS, ENABLE_RUBY24, DRIVER_PKG_VERSION, DRIVER_REPO_NAME.lower()))

# TODO: Define where to copy
INSTALL_PKG_DATA_TO_ARCHIVE.extend([
    {
        'from_path': options['INSTALL_DIR'],
        'relative': [
            {
                'path': 'opt',
            }
        ]
    },
])

# TODO: Define where to copy
DEV_PKG_DATA_TO_ARCHIVE.extend([
    {
        'from_path': options['BUILD_DIR'],
        'relative': [
            {
                'path': '',
                'pack_as': ''
            },
        ]
    }
])
