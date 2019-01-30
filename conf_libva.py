# Copyright (c) 2018 Intel Corporation
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


LIBVA_REPO_NAME = 'libva'

# TODO: get LibVA version from manifest
LIBVA_VERSION = '2.3.0'

# Repos_to_extract
# TODO: get branch, commit_id from Manifest
PRODUCT_REPOS = [
    {'name': 'MediaSDK'},
    {'name': LIBVA_REPO_NAME, }
]

ENABLE_DEVTOOLSET = 'source /opt/rh/devtoolset-6/enable'
# Workaround to run fpm tool on CentOS 6.9
ENABLE_RUBY24 = 'source /opt/rh/rh-ruby24/enable'
GCC_LATEST = '8.2.0'
CLANG_VERSION = '6.0'
options["STRIP_BINARIES"] = True

# Create subfolders for libVA
libva_options = {
    "BUILD_DIR": options["BUILD_DIR"] / "libva",
    "INSTALL_DIR": options["INSTALL_DIR"] / "libva",
    "LOGS_DIR": options["LOGS_DIR"] / "libva",
    "LIBVA_PKG_DIR": options["BUILD_DIR"] / "libva_pkgconfig",  # Fake pkgconfig dir
}

# _DEB_PREFIX is used by default
LIBVA_DEB_PREFIX = Path('/usr/local')
LIBVA_CENTOS_PREFIX = Path('/usr')

LIBVA_PKGCONFIG_DIR = LIBVA_DEB_PREFIX / 'lib/pkgconfig'

LIBVA_LIB_INSTALL_DIRS = {
    'rpm': 'lib64',
    'deb': 'lib/x86_64-linux-gnu'
}

LIBVA_REPO_DIR = options.get('REPOS_DIR') / LIBVA_REPO_NAME

#TODO: add more smart logic or warnings?! (potential danger zone)
def get_building_cmd(command, gcc_latest, enable_devtoolset):
     # Ubuntu Server: gcc_latest or clang
    if args.get('compiler') == "clang" or (args.get('compiler') == "gcc" and args.get('compiler_version') == gcc_latest):
        return command
    else:
        return f'{enable_devtoolset} && {command}' #enable new compiler on CentOS


# Build LibVA
action('LibVA: autogen.sh',
       work_dir=libva_options['BUILD_DIR'],
       cmd=get_building_cmd(f'{LIBVA_REPO_DIR}/autogen.sh', GCC_LATEST, ENABLE_DEVTOOLSET))

action('LibVA: make',
       work_dir=libva_options['BUILD_DIR'],
       cmd=get_building_cmd(f'make -j`nproc`', GCC_LATEST, ENABLE_DEVTOOLSET))

action('LibVA: list artifacts',
       work_dir=libva_options['BUILD_DIR'],
       cmd=f'echo " " && ls ./va',
       verbose=True)

action('LibVA: make install',
       stage=stage.INSTALL,
       work_dir=libva_options['BUILD_DIR'],
       cmd=get_building_cmd(f'make DESTDIR={libva_options["INSTALL_DIR"]} install', GCC_LATEST, ENABLE_DEVTOOLSET))

# Create fake LibVA pkgconfigs to build MediaSDK from custom location
pkgconfig_pattern = {'^prefix=.+': f'prefix={libva_options["INSTALL_DIR"] / LIBVA_DEB_PREFIX.relative_to(LIBVA_DEB_PREFIX.root)}'}

action('LibVA: change LibVA pkgconfigs',
       stage=stage.INSTALL,
       callfunc=(update_config, [libva_options["INSTALL_DIR"] / LIBVA_PKGCONFIG_DIR.relative_to(LIBVA_PKGCONFIG_DIR.root),
                                 pkgconfig_pattern], {'copy_to': libva_options["LIBVA_PKG_DIR"]}))


# LibVA: pkgconfig for OS Ubuntu
# Update pkgconfig prefix
pkgconfig_deb_pattern = {
    '/lib': f"/{LIBVA_LIB_INSTALL_DIRS['deb']}",
}

action('LibVA: change pkgconfig for deb',
       stage=stage.PACK,
       callfunc=(update_config, [libva_options["INSTALL_DIR"] / LIBVA_DEB_PREFIX.relative_to(LIBVA_DEB_PREFIX.root) / 'lib/pkgconfig',
                                 pkgconfig_deb_pattern], {}))

# Get package installation dirs for LibVA
pack_dir = libva_options['INSTALL_DIR'] / LIBVA_DEB_PREFIX.relative_to(LIBVA_DEB_PREFIX.root)
lib_install_to = LIBVA_DEB_PREFIX / LIBVA_LIB_INSTALL_DIRS['deb']
include_install_to = LIBVA_DEB_PREFIX

LIBVA_PACK_DIRS = [
    f'{pack_dir}/lib/={lib_install_to}/',
    f'{pack_dir}/include/={include_install_to}/include',
]

action('LibVA: create deb pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('deb',  LIBVA_PACK_DIRS, ENABLE_RUBY24, LIBVA_VERSION, LIBVA_REPO_NAME))

# LibVA: pkgconfig for OS CentOS
pkgconfig_rpm_pattern = {
    '^prefix=.+': 'prefix=/usr',
    f'/{LIBVA_LIB_INSTALL_DIRS["deb"]}': f'/{LIBVA_LIB_INSTALL_DIRS["rpm"]}',
}

action('LibVA: change pkgconfigs for rpm',
       stage=stage.PACK,
       callfunc=(update_config, [libva_options["INSTALL_DIR"] / LIBVA_DEB_PREFIX.relative_to(LIBVA_DEB_PREFIX.root) / 'lib/pkgconfig',
                                 pkgconfig_rpm_pattern], {}))

# Get package installation dir for LibVA
lib_install_to = LIBVA_CENTOS_PREFIX / LIBVA_LIB_INSTALL_DIRS['rpm']
include_install_to = LIBVA_CENTOS_PREFIX

LIBVA_PACK_DIRS = [
    f'{pack_dir}/lib/={lib_install_to}/',
    f'{pack_dir}/include/={include_install_to}/include',
]

action('LibVA: create rpm pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('rpm', LIBVA_PACK_DIRS, ENABLE_RUBY24, LIBVA_VERSION, LIBVA_REPO_NAME))



INSTALL_PKG_DATA_TO_ARCHIVE.extend([
    {
        'from_path': options['INSTALL_DIR'],
        'relative': [
            {
                'path': 'libva',
            }
        ]
    },
])
