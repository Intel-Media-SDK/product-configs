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


DRIVER_REPO_NAME = 'media-driver'
# TODO: get Media-driver version from manifest
DRIVER_VERSION = 'intel-media-18.4.0'
DRIVER_REPO_DIR = options.get('REPOS_DIR') / DRIVER_REPO_NAME

# Repos_to_extract
# TODO: get branch, commit_id from Manifest
PRODUCT_REPOS = [
    {'name': DRIVER_REPO_NAME},
    # Give possibility to build the driver for changes from product configs repository
    # This repo not needed for build and added only to support CI process
    {'name': 'product-configs'}
]

ENABLE_DEVTOOLSET = 'source /opt/rh/devtoolset-6/enable'
# Workaround to run fpm tool on CentOS 6.9
ENABLE_RUBY24 = 'source /opt/rh/rh-ruby24/enable'
GCC_LATEST = '8.2.0'
options["STRIP_BINARIES"] = True

DRIVER_INSTALL_PREFIX = Path('/opt/intel/msdk_driver')
# Installation by default: /opt/intel/msdk_driver/lib64
DRIVER_LIB_DIR = 'lib64'


#TODO: add more smart logic or warnings?! (potential danger zone)
def get_building_cmd(command, gcc_latest, enable_devtoolset):
     # Ubuntu Server: gcc_latest or clang
    if args.get('compiler') == "clang" or (args.get('compiler') == "gcc" and args.get('compiler_version') == gcc_latest):
        return command
    else:
        return f'{enable_devtoolset} && {command}' #enable new compiler on CentOS


cmake_command = ['cmake3']
cmake_command.append(f'-DMEDIA_VERSION="$MEDIA_VERSION"')
# By default install driver to /opt/intel/msdk_driver
cmake_command.append(f'-DCMAKE_INSTALL_PREFIX={DRIVER_INSTALL_PREFIX}')
cmake_command.append(f'-DCMAKE_INSTALL_LIBDIR={DRIVER_INSTALL_PREFIX / DRIVER_LIB_DIR}')
cmake_command.append(f'-DINSTALL_DRIVER_SYSCONF=OFF')
# Path contains iHD_drv_video.so
cmake_command.append(f'-DLIBVA_DRIVERS_PATH={DRIVER_INSTALL_PREFIX / DRIVER_LIB_DIR}')

cmake_command.append(str(DRIVER_REPO_DIR))
cmake = ' '.join(cmake_command)

# Build Media Driver
action('media-driver: cmake',
       work_dir=options['BUILD_DIR'],
       cmd=get_building_cmd(cmake, GCC_LATEST, ENABLE_DEVTOOLSET))

action('media-driver: build',
       cmd=get_building_cmd(f'make -j`nproc`', GCC_LATEST, ENABLE_DEVTOOLSET))

action('media-driver: list artifacts',
        cmd=f'echo " " && ls ./media_driver',
        verbose=True)

action('media-driver: make install',
       stage=stage.INSTALL,
       work_dir=options['BUILD_DIR'],
       cmd=get_building_cmd(f'make DESTDIR={options["INSTALL_DIR"]} install', GCC_LATEST, ENABLE_DEVTOOLSET))


# Get package installation dir for media-driver
pack_dir = options['INSTALL_DIR'] / DRIVER_INSTALL_PREFIX.relative_to(DRIVER_INSTALL_PREFIX.root)

DRIVER_PACK_DIRS = [
    f'{pack_dir}/lib64/={DRIVER_INSTALL_PREFIX / DRIVER_LIB_DIR }',
    f'{pack_dir}/include/={DRIVER_INSTALL_PREFIX}/include',
]

action('media-driver: create rpm pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('rpm', DRIVER_PACK_DIRS, ENABLE_RUBY24, DRIVER_VERSION, DRIVER_REPO_NAME.lower()))


action('media-driver: create deb pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('deb', DRIVER_PACK_DIRS, ENABLE_RUBY24, DRIVER_VERSION, DRIVER_REPO_NAME.lower()))

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
