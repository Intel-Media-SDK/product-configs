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


LIBVA_REPO_NAME = 'libva'
LIBVA_UTILS_REPO_NAME = 'libva-utils'

# Libva-utils version maps libva version
LIBVA_VERSION = manifest.get_component(LIBVA_REPO_NAME).version

LIBVA_UTILS_BUILD_DIR = options["BUILD_DIR"] / LIBVA_UTILS_REPO_NAME

ENABLE_DEVTOOLSET = 'source /opt/rh/devtoolset-6/enable'
# Workaround to run fpm tool on CentOS 6.9
ENABLE_RUBY24 = 'source /opt/rh/rh-ruby24/enable'
GCC_LATEST = '8.2.0'
CLANG_VERSION = '6.0'
options["STRIP_BINARIES"] = True

# Create dir for Fake pkgconfig
options["LIBVA_PKG_DIR"] = options["BUILD_DIR"] / "libva_pkgconfig"

# _DEB_PREFIX is used by default
LIBVA_DEB_PREFIX = Path('/usr/local')
LIBVA_CENTOS_PREFIX = Path('/usr')

LIBVA_PKGCONFIG_DIR = LIBVA_DEB_PREFIX / 'lib64/pkgconfig'

LIBVA_LIB_INSTALL_DIRS = {
    'rpm': 'lib64',
    'deb': 'lib/x86_64-linux-gnu'
}

LIBVA_REPO_DIR = options.get('REPOS_DIR') / LIBVA_REPO_NAME
LIBVA_UTILS_REPO_DIR = options.get('REPOS_DIR') / LIBVA_UTILS_REPO_NAME


#TODO: add more smart logic or warnings?! (potential danger zone)
def get_building_cmd(command, gcc_latest, enable_devtoolset):
     # Ubuntu Server: gcc_latest or clang
    if args.get('compiler') == "clang" or (args.get('compiler') == "gcc" and args.get('compiler_version') == gcc_latest):
        return command
    else:
        return f'{enable_devtoolset} && {command}' #enable new compiler on CentOS

cmd = []
cmd.append('--buildtype=release')
cmd.append('-Ddriverdir=/opt/intel/mediasdk/lib64')
cmd.append('-Dc_args="-O2 -fPIC -fPIE -D_FORTIFY_SOURCE=2 -DNDEBUG -fstack-protector-strong -Wno-dev"')
cmd.append('-Dc_link_args="-z noexecstack -z relro -z now"')

# Build LibVA
action('LibVA: meson',
       work_dir=options['BUILD_DIR'],
       cmd=get_building_cmd(f'meson {(" ").join(cmd)} {LIBVA_REPO_DIR}', GCC_LATEST, ENABLE_DEVTOOLSET))

action('LibVA: ninja-build',
       work_dir=options['BUILD_DIR'],
       cmd=get_building_cmd(f'ninja-build -j`nproc`', GCC_LATEST, ENABLE_DEVTOOLSET))

action('LibVA: list artifacts',
       work_dir=options['BUILD_DIR'],
       cmd=f'echo " " && ls ./va',
       verbose=True)

action('LibVA: ninja-build install',
       stage=stage.INSTALL,
       work_dir=options['BUILD_DIR'],
       cmd=get_building_cmd(f'DESTDIR={options["INSTALL_DIR"]} ninja-build install', GCC_LATEST, ENABLE_DEVTOOLSET))

# Build libva-utils
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


# Create fake LibVA pkgconfigs to build MediaSDK from custom location
pkgconfig_pattern = {'^prefix=.+': f'prefix={options["INSTALL_DIR"] / LIBVA_DEB_PREFIX.relative_to(LIBVA_DEB_PREFIX.root)}'}

action('LibVA: change LibVA pkgconfigs',
       stage=stage.INSTALL,
       callfunc=(update_config, [options["INSTALL_DIR"] / LIBVA_PKGCONFIG_DIR.relative_to(LIBVA_PKGCONFIG_DIR.root),
                                 pkgconfig_pattern], {'copy_to': options["LIBVA_PKG_DIR"]}))


# LibVA: pkgconfig for OS Ubuntu
# Update pkgconfig prefix
pkgconfig_deb_pattern = {
    'libdir=.*/lib64': "libdir=${prefix}/"+LIBVA_LIB_INSTALL_DIRS['deb'],
}

action('LibVA: change pkgconfig for deb',
       stage=stage.PACK,
       callfunc=(update_config, [options["INSTALL_DIR"] / LIBVA_PKGCONFIG_DIR.relative_to(LIBVA_PKGCONFIG_DIR.root),
                                 pkgconfig_deb_pattern], {}))

# Get package installation dirs for LibVA
pack_dir = options['INSTALL_DIR'] / LIBVA_DEB_PREFIX.relative_to(LIBVA_DEB_PREFIX.root)
lib_install_to = LIBVA_DEB_PREFIX / LIBVA_LIB_INSTALL_DIRS['deb']
include_install_to = LIBVA_DEB_PREFIX

LIBVA_PACK_DIRS = [
    f'{pack_dir}/lib64/={lib_install_to}/',
    f'{pack_dir}/include/={include_install_to}/include',
    f'{pack_dir}/bin/={include_install_to}/bin',
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
       callfunc=(update_config, [options["INSTALL_DIR"] / LIBVA_PKGCONFIG_DIR.relative_to(LIBVA_PKGCONFIG_DIR.root),
                                 pkgconfig_rpm_pattern], {}))

# Get package installation dir for LibVA
lib_install_to = LIBVA_CENTOS_PREFIX / LIBVA_LIB_INSTALL_DIRS['rpm']
include_install_to = LIBVA_CENTOS_PREFIX

LIBVA_PACK_DIRS = [
    f'{pack_dir}/lib64/={lib_install_to}/',
    f'{pack_dir}/include/={include_install_to}/include',
    f'{pack_dir}/bin/={include_install_to}/bin',
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
                'path': 'usr',
            }
        ]
    },
])
