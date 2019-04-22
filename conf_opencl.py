# Copyright (c) 2019 Intel Corporation
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

OPENCL_REPO_NAME = 'opencl_runtime'
# Codename for opencl_runtime is neo
OPENCL_CODE_NAME = 'neo'

# TODO: get OpenCL version from manifest
OPENCL_VERSION = '19.11.12599'
OPENCL_REPO_DIR = options.get('REPOS_DIR') / OPENCL_REPO_NAME

# Repos_to_extract
PRODUCT_REPOS = [
    {'name': OPENCL_REPO_NAME, 'commit_id': OPENCL_VERSION},

    # This repo not needed for build and added only to support CI process
    {'name': 'product-configs'}
]

DEPENDENCIES = [
    'gmmlib',
    'intel-graphic-compiler',
]

ENABLE_DEVTOOLSET = 'source /opt/rh/devtoolset-6/enable'
# Workaround to run fpm tool on CentOS 6.9
ENABLE_RUBY24 = 'source /opt/rh/rh-ruby24/enable'
GCC_LATEST = '8.2.0'
options["STRIP_BINARIES"] = True

OPENCL_DEB_PREFIX = Path('/usr/local')
OPENCL_CENTOS_PREFIX = Path('/usr')

OPENCL_LIB_INSTALL_DIRS = {
    'rpm': 'lib64',
    'deb': 'lib/x86_64-linux-gnu'
}

# TODO: Export from Dependency directory
GMMLIB_PKG_DIR = '/usr/local/lib64/pkgconfig/'
IGC_DIR = '/usr/local/'

# TODO: add more smart logic or warnings?! (potential danger zone)
def get_building_cmd(command, gcc_latest, enable_devtoolset):
    # Ubuntu Server: gcc_latest or clang
    if args.get('compiler') == "clang" or (
            args.get('compiler') == "gcc" and args.get('compiler_version') == gcc_latest):
        return command
    else:
        return f'{enable_devtoolset} && {command}'  # enable new compiler on CentOS


cmake_command = ['cmake3',
                 '-DBUILD_TYPE=Release',
                 f'-DCMAKE_INSTALL_PREFIX={OPENCL_CENTOS_PREFIX}',
                 f'-DCMAKE_INSTALL_LIBDIR={OPENCL_LIB_INSTALL_DIRS["rpm"]}',
                 f'-DIGC_DIR={IGC_DIR}',
                 f'-DDO_NOT_RUN_AUB_TESTS=1',
                 str(OPENCL_REPO_DIR)]

# TODO: define path to igc
# TODO: WORKAROUND Enable tests when issue https://github.com/intel/compute-runtime/issues/155 is closed

cmake = ' '.join(cmake_command)

# Build OpenCL
action('OpenCL: cmake',
       work_dir=options['BUILD_DIR'],
       cmd=get_building_cmd(cmake, GCC_LATEST, ENABLE_DEVTOOLSET),
       env={'PKG_CONFIG_PATH': GMMLIB_PKG_DIR})

action('OpenCL: build',
       cmd=get_building_cmd(f'make -j`nproc`', GCC_LATEST, ENABLE_DEVTOOLSET),)

action('OpenCL: make install',
       stage=stage.INSTALL,
       work_dir=options['BUILD_DIR'],
       cmd=get_building_cmd(f'make DESTDIR={options["INSTALL_DIR"]} install', GCC_LATEST, ENABLE_DEVTOOLSET))

# OpenCL: rpm package
pack_dir = options['INSTALL_DIR']

# TODO: Hack of file intel.icd to resolve location of artifacts
OPENCL_PACK_DIRS = [
    f'{pack_dir}/etc/=/etc/',
    f'{pack_dir}/{OPENCL_CENTOS_PREFIX.relative_to(OPENCL_CENTOS_PREFIX.root)}/{OPENCL_LIB_INSTALL_DIRS["rpm"]}/='
    f'{OPENCL_CENTOS_PREFIX}/{OPENCL_LIB_INSTALL_DIRS["rpm"]}',
    f'{pack_dir}/{OPENCL_CENTOS_PREFIX.relative_to(OPENCL_CENTOS_PREFIX.root)}/bin={OPENCL_CENTOS_PREFIX}',
]

action('OpenCL: create rpm pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('rpm', OPENCL_PACK_DIRS, ENABLE_RUBY24, OPENCL_VERSION, OPENCL_CODE_NAME))

# Update path to OpenCL on Ubuntu
pkgconfig_deb_pattern = {
    str(OPENCL_CENTOS_PREFIX / OPENCL_LIB_INSTALL_DIRS['rpm']): str(OPENCL_DEB_PREFIX / OPENCL_LIB_INSTALL_DIRS['deb']),
}
path_to_config = options["INSTALL_DIR"] / 'etc/OpenCL/vendors/'
action('OpenCL: change intel.icd for deb',
       stage=stage.PACK,
       callfunc=(update_config, [path_to_config,
                                 pkgconfig_deb_pattern], {'pattern': '*.icd'}))

path_to_config = options["INSTALL_DIR"] / 'etc/ld.so.conf.d/'
action('OpenCL: change libintelopencl.conf for deb',
       stage=stage.PACK,
       callfunc=(update_config, [path_to_config,
                                 pkgconfig_deb_pattern], {'pattern': '*.conf'}))

OPENCL_PACK_DIRS = [
    f'{pack_dir}/etc/=/etc/',
    f'{pack_dir}/{OPENCL_CENTOS_PREFIX.relative_to(OPENCL_CENTOS_PREFIX.root)}/{OPENCL_LIB_INSTALL_DIRS["rpm"]}/='
    f'{OPENCL_DEB_PREFIX}/{OPENCL_LIB_INSTALL_DIRS["deb"]}',
    f'{pack_dir}/{OPENCL_CENTOS_PREFIX.relative_to(OPENCL_CENTOS_PREFIX.root)}/bin={OPENCL_DEB_PREFIX}',
]

action('OpenCL: create deb pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('deb', OPENCL_PACK_DIRS, ENABLE_RUBY24, OPENCL_VERSION, OPENCL_CODE_NAME))

INSTALL_PKG_DATA_TO_ARCHIVE.extend([
    {
        'from_path': options['INSTALL_DIR'],
        'relative': [
            {
                'path': 'usr'
            },
            {
                'path': 'etc'
            }
        ]
    },
])
