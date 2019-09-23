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

LIBVA_UTILS_REPO_NAME = 'libva-utils'

LIBVA_UTILS_REPO_DIR = options.get('REPOS_DIR') / LIBVA_UTILS_REPO_NAME
BUILD_NUM = get_commit_number(LIBVA_UTILS_REPO_DIR)
LIBVA_UTILS_VERSION = manifest.get_component(LIBVA_UTILS_REPO_NAME).version + f'.{BUILD_NUM}'

DEPENDENCIES = [
    'libva'
]

ENABLE_DEVTOOLSET = 'source /opt/rh/devtoolset-6/enable'
# Workaround to run fpm tool on CentOS 6.9
ENABLE_RUBY24 = 'source /opt/rh/rh-ruby24/enable'
GCC_LATEST = '8.2.0'
CLANG_VERSION = '6.0'
options["STRIP_BINARIES"] = True
# _DEB_PREFIX is used by default
LIBVA_UTILS_DEB_PREFIX = Path('/usr/local')
LIBVA_UTILS_CENTOS_PREFIX = Path('/usr')

LIBVA_UTILS_INSTALL_DIRS = {
    'rpm': 'lib64',
    'deb': 'lib/x86_64-linux-gnu'
}


# TODO: add more smart logic or warnings?! (potential danger zone)
def get_building_cmd(command, gcc_latest, enable_devtoolset):
    # Ubuntu Server: gcc_latest or clang
    if args.get('compiler') == "clang" or (args.get('compiler') == "gcc" and args.get('compiler_version') == gcc_latest):
        return command
    else:
        return f'{enable_devtoolset} && {command}'  # enable new compiler on CentOS


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


# Build libva-utils
LIBVA_UTILS_BUILD_DIR = options["BUILD_DIR"] / LIBVA_UTILS_REPO_NAME
LIBVA_UTILS_REPO_DIR = options.get('REPOS_DIR') / LIBVA_UTILS_REPO_NAME

action('libva-utils: meson',
       work_dir=LIBVA_UTILS_BUILD_DIR,
       cmd=get_building_cmd(f'meson {LIBVA_UTILS_REPO_DIR}', GCC_LATEST, ENABLE_DEVTOOLSET))

action('libva-utils: ninja-build',
       work_dir=LIBVA_UTILS_BUILD_DIR,
       cmd=get_building_cmd(f'ninja-build -j`nproc`', GCC_LATEST, ENABLE_DEVTOOLSET))

action('libva-utils: ninja-build install',
       stage=stage.INSTALL,
       work_dir=LIBVA_UTILS_BUILD_DIR,
       cmd=get_building_cmd(f'DESTDIR={options["INSTALL_DIR"]} ninja-build install', GCC_LATEST, ENABLE_DEVTOOLSET))

# Get package installation dirs for LibVA
pack_dir = options['INSTALL_DIR'] / LIBVA_UTILS_DEB_PREFIX.relative_to(LIBVA_UTILS_DEB_PREFIX.root)
install_to = LIBVA_UTILS_DEB_PREFIX

LIBVA_PACK_DIRS = [
    f'{pack_dir}/bin/={install_to}/bin'
]

# libva-utils: pkgconfig for OS Ubuntu
action('libva-utils: create deb pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('deb',  LIBVA_PACK_DIRS, ENABLE_RUBY24, LIBVA_UTILS_VERSION, LIBVA_UTILS_REPO_NAME))

# libva-utils: pkgconfig for OS CentOS
install_to = LIBVA_UTILS_CENTOS_PREFIX

LIBVA_PACK_DIRS = [
    f'{pack_dir}/bin/={install_to}/bin'
]

action('libva-utils: create rpm pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('rpm', LIBVA_PACK_DIRS, ENABLE_RUBY24, LIBVA_UTILS_VERSION, LIBVA_UTILS_REPO_NAME))


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
