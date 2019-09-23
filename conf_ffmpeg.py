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

FFMPEG_REPO_NAME = 'FFmpeg'

FFMPEG_REPO_DIR = options.get('REPOS_DIR') / FFMPEG_REPO_NAME
BUILD_NUM = get_commit_number(FFMPEG_REPO_DIR)
FFMPEG_VERSION = manifest.get_component(FFMPEG_REPO_NAME.lower()).version + f'.{BUILD_NUM}'

DEPENDENCIES = [
    'libva'
]


ENABLE_DEVTOOLSET = 'source /opt/rh/devtoolset-6/enable'
# Workaround to run fpm tool on CentOS 6.9
ENABLE_RUBY24 = 'source /opt/rh/rh-ruby24/enable'
GCC_LATEST = '8.2.0'
CLANG_VERSION = '6.0'
options["STRIP_BINARIES"] = True

# By default install to the system
# _DEB_PREFIX is used by default
FFMPEG_DEB_PREFIX = Path('/usr/local')
FFMPEG_CENTOS_PREFIX = Path('/usr')

PKGCONFIG = 'lib/pkgconfig'
FFMPEG_PKGCONFIG_DIR = FFMPEG_DEB_PREFIX / PKGCONFIG

FFMPEG_LIB_INSTALL_DIRS = {
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

# Build ffmpeg
action('ffmpeg: configure',
       work_dir=options['BUILD_DIR'],
       cmd=get_building_cmd(f'{FFMPEG_REPO_DIR}/configure --disable-x86asm', GCC_LATEST, ENABLE_DEVTOOLSET),
       env={'PKG_CONFIG_PATH': f'{LIBVA_PKG_CONFIG_PATH}'})

action('ffmpeg: make',
       cmd=get_building_cmd(f'make -j`nproc`', GCC_LATEST, ENABLE_DEVTOOLSET))

action('ffmpeg: make install',
       stage=stage.INSTALL,
       work_dir=options['BUILD_DIR'],
       cmd=get_building_cmd(f'make DESTDIR={options["INSTALL_DIR"]} install', GCC_LATEST, ENABLE_DEVTOOLSET))

# ffmpeg: pkgconfig for OS Ubuntu
# Update pkgconfig prefix
pkgconfig_deb_pattern = {
    f'{FFMPEG_DEB_PREFIX}/lib': f'{FFMPEG_DEB_PREFIX / FFMPEG_LIB_INSTALL_DIRS["deb"]}',
}

action('ffmpeg: change pkgconfig for deb',
       stage=stage.PACK,
       callfunc=(update_config, [options["INSTALL_DIR"] / FFMPEG_DEB_PREFIX.relative_to(FFMPEG_DEB_PREFIX.root) / PKGCONFIG,
                                 pkgconfig_deb_pattern], {}))

# Get package installation dir for ffmpeg
pack_dir = options['INSTALL_DIR'] / FFMPEG_DEB_PREFIX.relative_to(FFMPEG_DEB_PREFIX.root)
lib_install_to = FFMPEG_DEB_PREFIX / FFMPEG_LIB_INSTALL_DIRS['deb']
include_install_to = FFMPEG_DEB_PREFIX

FFMPEG_PACK_DIRS = [
    f'{pack_dir}/lib/={lib_install_to}/',
    f'{pack_dir}/include/={include_install_to}/include',
    f'{pack_dir}/bin/={include_install_to}/bin',
    f'{pack_dir}/share/={include_install_to}/share',
]

action('ffmpeg: create deb pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('deb',  FFMPEG_PACK_DIRS, ENABLE_RUBY24, FFMPEG_VERSION, FFMPEG_REPO_NAME))

# ffmpeg: pkgconfig for OS CentOS
# Update pkgconfig prefix
pkgconfig_rpm_pattern = {
    '^prefix=.+': 'prefix=/usr',
    f'{FFMPEG_DEB_PREFIX}/include': f'{FFMPEG_CENTOS_PREFIX}/include',
    f'{FFMPEG_DEB_PREFIX / FFMPEG_LIB_INSTALL_DIRS["deb"]}': f'{FFMPEG_CENTOS_PREFIX / FFMPEG_LIB_INSTALL_DIRS["rpm"]}',
}

action('ffmpeg: change pkgconfigs for rpm',
       stage=stage.PACK,
       callfunc=(update_config, [options["INSTALL_DIR"] / FFMPEG_DEB_PREFIX.relative_to(FFMPEG_DEB_PREFIX.root) / PKGCONFIG,
                                 pkgconfig_rpm_pattern], {}))

# Get package installation dir for FFMPEG
lib_install_to = FFMPEG_CENTOS_PREFIX / FFMPEG_LIB_INSTALL_DIRS['rpm']
include_install_to = FFMPEG_CENTOS_PREFIX

FFMPEG_PACK_DIRS = [
    f'{pack_dir}/lib/={lib_install_to}/',
    f'{pack_dir}/include/={include_install_to}/include',
    f'{pack_dir}/bin/={include_install_to}/bin',
    f'{pack_dir}/share/={include_install_to}/share',
]

action('ffmpeg: create rpm pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('rpm', FFMPEG_PACK_DIRS, ENABLE_RUBY24, FFMPEG_VERSION, FFMPEG_REPO_NAME))

INSTALL_PKG_DATA_TO_ARCHIVE.extend([
    {
        'from_path': options['INSTALL_DIR'],
        'relative': [
            {
                'path': 'usr/local/lib',
                'pack_as': 'usr/local/lib64'
            },
            {
                'path': 'usr/local/bin'
            },
            {
                'path': 'usr/local/include'
            },
            {
                'path': 'usr/local/share'
            }
        ]
    },
])
