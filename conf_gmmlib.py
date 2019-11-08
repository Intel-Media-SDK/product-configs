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

GMMLIB_REPO_NAME = 'gmmlib'

GMMLIB_REPO_DIR = options.get('REPOS_DIR') / GMMLIB_REPO_NAME
BUILD_NUM = get_commit_number(GMMLIB_REPO_DIR)
GMMLIB_VERSION = manifest.get_component(GMMLIB_REPO_NAME).version + f'.{BUILD_NUM}'


ENABLE_DEVTOOLSET = 'source /opt/rh/devtoolset-6/enable'
# Workaround to run fpm tool on CentOS 6.9
ENABLE_RUBY24 = 'source /opt/rh/rh-ruby24/enable'
GCC_LATEST = '8.2.0'
options["STRIP_BINARIES"] = True

# By default install to the system
# _DEB_PREFIX is used by default
GMMLIB_DEB_PREFIX = Path('/usr/local')
GMMLIB_CENTOS_PREFIX = Path('/usr')

PKGCONFIG = 'lib64/pkgconfig'
GMMLIB_PKGCONFIG_DIR = GMMLIB_DEB_PREFIX / PKGCONFIG

GMMLIB_LIB_INSTALL_DIRS = {
    'rpm': 'lib64',
    'deb': 'lib/x86_64-linux-gnu'
}


#TODO: add more smart logic or warnings?! (potential danger zone)
def get_building_cmd(command, gcc_latest, enable_devtoolset):
     # Ubuntu Server: gcc_latest or clang
    if args.get('compiler') == "clang" or (args.get('compiler') == "gcc" and args.get('compiler_version') == gcc_latest):
        return command
    else:
        return f'{enable_devtoolset} && {command}' #enable new compiler on CentOS


cmake_command = ['cmake3']
cmake_command.append('-DCMAKE_SHARED_LINKER_FLAGS="-pie -z noexecstack -z relro -z now"')
cmake_command.append(str(GMMLIB_REPO_DIR))
cmake = ' '.join(cmake_command)

# Build gmmlib
action('gmmlib: cmake',
       work_dir=options['BUILD_DIR'],
       cmd=get_building_cmd(cmake, GCC_LATEST, ENABLE_DEVTOOLSET))

action('gmmlib: build',
       cmd=get_building_cmd(f'make -j`nproc`', GCC_LATEST, ENABLE_DEVTOOLSET))

action('gmmlib: list artifacts',
         cmd=f'echo " " && ls ./Source/GmmLib',
         verbose=True)

action('gmmlib: make install',
       stage=stage.INSTALL,
       work_dir=options['BUILD_DIR'],
       cmd=get_building_cmd(f'make DESTDIR={options["INSTALL_DIR"]} install', GCC_LATEST, ENABLE_DEVTOOLSET))

# gmmlib: pkgconfig for OS Ubuntu
# Update pkgconfig prefix
pkgconfig_deb_pattern = {
    '/lib64': f"/{GMMLIB_LIB_INSTALL_DIRS['deb']}",
}

action('gmmlib: change pkgconfig for deb',
       stage=stage.PACK,
       callfunc=(update_config, [options["INSTALL_DIR"] / GMMLIB_DEB_PREFIX.relative_to(GMMLIB_DEB_PREFIX.root) / PKGCONFIG,
                                 pkgconfig_deb_pattern], {}))

# Get package installation dir for gmmlib
pack_dir = options['INSTALL_DIR'] / GMMLIB_DEB_PREFIX.relative_to(GMMLIB_DEB_PREFIX.root)
lib_install_to = GMMLIB_DEB_PREFIX / GMMLIB_LIB_INSTALL_DIRS['deb']
include_install_to = GMMLIB_DEB_PREFIX

GMMLIB_PACK_DIRS = [
    f'{pack_dir}/lib64/={lib_install_to}/',
    f'{pack_dir}/include/={include_install_to}/include',
]

action('gmmlib: create deb pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('deb',  GMMLIB_PACK_DIRS, ENABLE_RUBY24, GMMLIB_VERSION, GMMLIB_REPO_NAME))

# gmmlib: pkgconfig for OS CentOS
# Update pkgconfig prefix
pkgconfig_rpm_pattern = {
    '^prefix=.+': 'prefix=/usr',
    f'{GMMLIB_DEB_PREFIX}/include': f'{GMMLIB_CENTOS_PREFIX}/include',
    f'{GMMLIB_DEB_PREFIX / GMMLIB_LIB_INSTALL_DIRS["deb"]}': f'{GMMLIB_CENTOS_PREFIX / GMMLIB_LIB_INSTALL_DIRS["rpm"]}',
}

action('gmmlib: change pkgconfigs for rpm',
       stage=stage.PACK,
       callfunc=(update_config, [options["INSTALL_DIR"] / GMMLIB_DEB_PREFIX.relative_to(GMMLIB_DEB_PREFIX.root) / PKGCONFIG,
                                 pkgconfig_rpm_pattern], {}))

# Get package installation dir for GMMLIB
lib_install_to = GMMLIB_CENTOS_PREFIX / GMMLIB_LIB_INSTALL_DIRS['rpm']
include_install_to = GMMLIB_CENTOS_PREFIX

GMMLIB_PACK_DIRS = [
    f'{pack_dir}/lib64/={lib_install_to}/',
    f'{pack_dir}/include/={include_install_to}/include',
]

action('gmmlib: create rpm pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('rpm', GMMLIB_PACK_DIRS, ENABLE_RUBY24, GMMLIB_VERSION, GMMLIB_REPO_NAME))


# TODO: Define where to copy
INSTALL_PKG_DATA_TO_ARCHIVE.extend([
    {
        'from_path': options['INSTALL_DIR'],
        'relative': [
            {
                'path': 'usr',
            }
        ]
    },
])