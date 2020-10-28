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


IGC_REPO_NAME = 'intel-graphics-compiler'
IGC_PACK_NAME = 'intel-igc-opencl'

IGC_REPO_DIR = options.get('REPOS_DIR') / IGC_REPO_NAME
BUILD_NUM = get_commit_number(IGC_REPO_DIR)
IGC_VERSION = manifest.get_component(IGC_REPO_NAME).version + f'.{BUILD_NUM}'


# Workaround to run fpm tool on CentOS 6.9
ENABLE_RUBY24 = 'source /opt/rh/rh-ruby24/enable'
GCC_LATEST = '8.2.0'
options["STRIP_BINARIES"] = False

DEPENDENCY_STRUCTURE = {
        'llvm-project': 'llvm-project',
        'opencl-clang': 'llvm-project/llvm/projects/opencl-clang',
        'SPIRV-LLVM-Translator': 'llvm-project/llvm/projects/llvm-spirv',
        'llvm-patches': 'llvm_patches',
        'intel-graphics-compiler': 'igc',
        'vc-intrinsics': 'vc-intrinsics',
    }

# By default install to the system
# _DEB_PREFIX is used by default
IGC_DEB_PREFIX = Path('/usr/local')
IGC_CENTOS_PREFIX = Path('/usr')

# By default
PKGCONFIG = 'lib64/pkgconfig'
IGC_PKGCONFIG_DIR = IGC_DEB_PREFIX / PKGCONFIG

IGC_LIB_INSTALL_DIRS = {
    'rpm': 'lib64',
    'deb': 'lib/x86_64-linux-gnu'
}


# Copy directory according to dependency structure
def build_dependency_structure(src_dir, dst_dir, dependency_structure):
    '''
    Creates directory structure regarding source_path as follows:
    source_path: options.get('REPOS_DIR')
    Structure:
    {
        llvm_source:
            llvm_source/tools/clang
            llvm_source/projects/opencl-clang
            llvm_source/projects/llvm-spirv
        llvm_patches
        igc
    }

    '''

    for repo_name, link_name in dependency_structure.items():
        copytree(str(src_dir / repo_name), str(dst_dir / link_name), symlinks=True, ignore_dangling_symlinks=True)


cmake_command = ['cmake3']

IGC_REPO_DIR = options['BUILD_DIR'] / f'{DEPENDENCY_STRUCTURE[IGC_REPO_NAME]}/IGC'

cmake_command.append('-Wno-dev')
cmake_command.append(str(IGC_REPO_DIR))
cmake = ' '.join(cmake_command)

# Make Structure
action('igc: create repos structure',
       stage=stage.EXTRACT,
       work_dir=options['BUILD_DIR'],
       callfunc=(build_dependency_structure, [options['REPOS_DIR'], options['BUILD_DIR'], DEPENDENCY_STRUCTURE], {}))

action('igc: move clang dir',
       stage=stage.EXTRACT,
       cmd="mv llvm-project/clang llvm-project/llvm/tools/",
       work_dir=options['BUILD_DIR'])

# Build igc
action('igc: cmake',
       work_dir=options['BUILD_DIR'],
       cmd=cmake)

action('igc: build',
       cmd='make -j`nproc`')

action('igc: list artifacts',
         cmd=f'echo " " && ls {options["BUILD_DIR"]}/Release',
         verbose=True)

action('igc: make install',
       stage=stage.INSTALL,
       work_dir=options['BUILD_DIR'],
       cmd=f'make DESTDIR={options["INSTALL_DIR"]} install')

# igc: pkgconfig for OS Ubuntu
# Update pkgconfig prefix
pkgconfig_deb_pattern = {
    '/lib': f"/{IGC_LIB_INSTALL_DIRS['deb']}",
}

action('igc: change pkgconfig for deb',
       stage=stage.PACK,
       callfunc=(update_config, [options["INSTALL_DIR"] / IGC_DEB_PREFIX.relative_to(IGC_DEB_PREFIX.root) / PKGCONFIG,
                                 pkgconfig_deb_pattern], {}))

# Get package installation dir for igc
pack_dir = options['INSTALL_DIR'] / IGC_DEB_PREFIX.relative_to(IGC_DEB_PREFIX.root)
lib_install_to = IGC_DEB_PREFIX / IGC_LIB_INSTALL_DIRS['deb']
include_install_to = IGC_DEB_PREFIX

IGC_PACK_DIRS = [
    f'{pack_dir}/lib64/={lib_install_to}/',
    f'{pack_dir}/include/={include_install_to}/include',
    f'{pack_dir}/bin/={include_install_to}/bin',
]

action('igc: create deb pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('deb',  IGC_PACK_DIRS, ENABLE_RUBY24, IGC_VERSION, IGC_PACK_NAME))

# igc: pkgconfig for OS CentOS
# Update pkgconfig prefix
pkgconfig_rpm_pattern = {
    '^prefix=.+': 'prefix=/usr',
    f'{IGC_LIB_INSTALL_DIRS["deb"]}': f'{IGC_LIB_INSTALL_DIRS["rpm"]}',
}

action('igc: change pkgconfigs for rpm',
       stage=stage.PACK,
       callfunc=(update_config, [options["INSTALL_DIR"] / IGC_DEB_PREFIX.relative_to(IGC_DEB_PREFIX.root) / PKGCONFIG,
                                 pkgconfig_rpm_pattern], {}))

# Get package installation dir for igc
lib_install_to = IGC_CENTOS_PREFIX / IGC_LIB_INSTALL_DIRS['rpm']
include_install_to = IGC_CENTOS_PREFIX

IGC_PACK_DIRS = [
    f'{pack_dir}/lib64/={lib_install_to}/',
    f'{pack_dir}/include/={include_install_to}/include',
    f'{pack_dir}/bin/={include_install_to}/bin',
]

action('igc: create rpm pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('rpm', IGC_PACK_DIRS, ENABLE_RUBY24, IGC_VERSION, IGC_PACK_NAME))


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
