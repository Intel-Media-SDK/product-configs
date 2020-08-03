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

CALC_REPO_NAME = 'tools'
PRODUCT_NAME = 'metrics-calc-lite'

CALC_REPO_DIR = options.get('REPOS_DIR') / CALC_REPO_NAME / 'metrics_calc_lite'
BUILD_NUM = get_commit_number(CALC_REPO_DIR)
CALC_VERSION = manifest.get_component(PRODUCT_NAME).version + f'.{BUILD_NUM}'


ENABLE_DEVTOOLSET = 'source /opt/rh/devtoolset-6/enable'
# Workaround to run fpm tool on CentOS 6.9
ENABLE_RUBY24 = 'source /opt/rh/rh-ruby24/enable'
GCC_LATEST = '8.2.0'
CLANG_VERSION = '9'
options["STRIP_BINARIES"] = True

# By default install to the system
# _DEB_PREFIX is used by default
CALC_DEB_PREFIX = Path('/usr/local')
CALC_CENTOS_PREFIX = Path('/usr')

CALC_LIB_INSTALL_DIRS = {
    'rpm': 'lib64',
    'deb': 'lib/x86_64-linux-gnu'
}


# TODO: add more smart logic or warnings?! (potential danger zone)
def get_building_cmd(command, gcc_latest, enable_devtoolset):
    # Ubuntu Server: gcc_latest or clang
    if args.get('compiler') == "clang" or (args.get('compiler') == "gcc" and args.get('compiler_version') == gcc_latest):
        return command
    else:
        return f'{enable_devtoolset} && {command}' #enable new compiler on CentOS


action('metrics calc: cmake',
       work_dir=options['BUILD_DIR'],
       cmd=get_building_cmd(f'cmake {CALC_REPO_DIR}', GCC_LATEST, ENABLE_DEVTOOLSET))

action('metrics calc: make',
       cmd=get_building_cmd(f'make -j`nproc`', GCC_LATEST, ENABLE_DEVTOOLSET))

action('metrics calc: make install',
       stage=stage.INSTALL,
       work_dir=options['BUILD_DIR'],
       cmd=get_building_cmd(f'make DESTDIR={options["INSTALL_DIR"]} install', GCC_LATEST, ENABLE_DEVTOOLSET))


# Get package installation dir for metrics calc
pack_dir = options['INSTALL_DIR'] / CALC_DEB_PREFIX.relative_to(CALC_DEB_PREFIX.root)

CALC_PACK_DIRS = [
    f'{pack_dir}/bin/={CALC_DEB_PREFIX}/bin'
]

action('metrics calc: create deb pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('deb',  CALC_PACK_DIRS, ENABLE_RUBY24, CALC_VERSION, PRODUCT_NAME))


CALC_PACK_DIRS = [
    f'{pack_dir}/bin/={CALC_CENTOS_PREFIX}/bin'
]

action('metrics calc: create rpm pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('rpm', CALC_PACK_DIRS, ENABLE_RUBY24, CALC_VERSION, PRODUCT_NAME))

INSTALL_PKG_DATA_TO_ARCHIVE.extend([
    {
        'from_path': options['INSTALL_DIR'],
        'relative': [
            {
                'path': 'usr'
            }
        ]
    }
])
