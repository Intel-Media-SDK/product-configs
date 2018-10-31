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

MEDIA_SDK_REPO_NAME = 'MediaSDK'
LIBVA_REPO_NAME = 'libva'
PRODUCT_CONFIGS_REPO_NAME = 'product-configs'

PRODUCT_REPOS = [
    {'name': MEDIA_SDK_REPO_NAME},
    # Give possibility to build linux for changes from product configs repository
    # This repo not needed for build and added only to support CI process
    {'name': PRODUCT_CONFIGS_REPO_NAME},
    {'name': LIBVA_REPO_NAME},
    # {'name': 'flow_test'},
]

PACKAGES_TARGET_DIRS = {
    'deb': '/opt/intel/msdk_driver',
    'rpm': '/opt/intel/msdk_driver',
}


ENABLE_DEVTOOLSET = 'source /opt/rh/devtoolset-6/enable'
GCC_LATEST = '8.2.0'
CLANG_VERSION = '6.0'
options["STRIP_BINARIES"] = True
MEDIA_SDK_REPO_DIR = options.get('REPOS_DIR') / MEDIA_SDK_REPO_NAME
MEDIA_SDK_BUILD_DIR = options.get('BUILD_DIR')
LIBVA_REPO_DIR = options.get('REPOS_DIR') / LIBVA_REPO_NAME
LIBVA_BUILD_DIR = options.get('DEPENDENCIES_DIR') / LIBVA_REPO_NAME

# dir of package config
LIBVA_CONFIG_DIR = 'usr/local'

# Max size = current fastboot lib size + ~50Kb
FASTBOOT_LIB_MAX_SIZE = 1 * 1024 * 1024 + 256 * 1024  # byte


def get_commit_number(repo_path=MEDIA_SDK_REPO_DIR):
    if not repo_path.exists():
        return '0'
    import git
    git_repo = git.Git(str(repo_path))
    return str(git_repo.rev_list('--count', 'HEAD'))


def get_api_version(repo_path=MEDIA_SDK_REPO_DIR):
    """
    :param name: Path to the MediaSDK folder
    :type name: String or Path

    Function finds the lines like:
        `#define MFX_VERSION_MAJOR 1`
        `#define MFX_VERSION_MINOR 26`
    And prints the version like:
        `1.26`
    """
    import re
    import pathlib

    mediasdk_api_header = pathlib.Path(repo_path) / 'api' / 'include' / 'mfxdefs.h'
    if not mediasdk_api_header.exists():
        raise Exception(f"No {mediasdk_api_header.name} found in {mediasdk_api_header.parent}")

    with open(mediasdk_api_header, 'r') as lines:
        major_version = ""
        minor_version = ""
        for line in lines:
            major_version_pattern = re.search("MFX_VERSION_MAJOR\s(\d+)", line)
            if major_version_pattern:
                major_version = major_version_pattern.group(1)
                continue

            minor_version_pattern = re.search("MFX_VERSION_MINOR\s(\d+)", line)
            if minor_version_pattern:
                minor_version = minor_version_pattern.group(1)

            if major_version and minor_version:
                return f"{major_version}.{minor_version}"
        raise Exception(f"API_VERSION did not found in {mediasdk_api_header}")


# TODO: move functions to the shared module
def set_env(repo_path, gcc_latest, clang_version, _get_commit_number=get_commit_number, _get_api_version=get_api_version):
  
    api_ver = _get_api_version(repo_path)
    build_num = _get_commit_number(repo_path)

    plugin_version = f'{api_ver}.3.{build_num}'
    options["ENV"]["API_VERSION"] = api_ver
    options["ENV"]['MFX_VERSION'] = f'8.0.16093{build_num}'
    options["ENV"]['MFX_HEVC_VERSION'] = f'{plugin_version}'
    options["ENV"]['MFX_H265FEI_VERSION'] = f'{plugin_version}'
    options["ENV"]['MFX_VP8_VERSION'] = f'{plugin_version}'
    options["ENV"]['MFX_VP9_VERSION'] = f'{plugin_version}'
    options["ENV"]['MFX_H264LA_VERSION'] = f'{plugin_version}'
    options["ENV"]['MFX_HOME'] = f'{str(repo_path)}'

    compiler_version = args.get('compiler_version')
    if args.get('compiler') == "gcc" and compiler_version == gcc_latest:
        options["ENV"]['CC'] = '/usr/bin/gcc-8'
        options["ENV"]['CXX'] = '/usr/bin/g++-8'
        
    elif args.get('compiler') == "clang" and compiler_version == clang_version:
        options["ENV"]['CC'] = f'/usr/bin/clang-{compiler_version}'
        options["ENV"]['CXX'] = f'/usr/bin/clang++-{compiler_version}'


#TODO: add more smart logic or warnings?! (potential danger zone)
def get_building_cmd(command, gcc_latest, enable_devtoolset):
     # Ubuntu Server: gcc_latest or clang
    if args.get('compiler') == "clang" or (args.get('compiler') == "gcc" and args.get('compiler_version') == gcc_latest):
        return command
    else:
        return f'{enable_devtoolset} && {command}' #enable new compiler on CentOS


def get_packing_cmd(pack_type, LIBVA_CONFIG_DIR, PACKAGES_TARGET_DIRS):
    return f'fpm --verbose -s dir -t {pack_type} --version 1.0.0  -n intel-ci-libva \
                                ./{LIBVA_CONFIG_DIR}/lib/={PACKAGES_TARGET_DIRS[pack_type]}/lib64/ \
                                ./{LIBVA_CONFIG_DIR}/include/={PACKAGES_TARGET_DIRS[pack_type]}/include/'

def check_lib_size(threshold_size, lib_path):
    """
    :param lib_path: path to lib
    :return: pathlib.Path
    """

    import pathlib

    lib_path = pathlib.Path(str(lib_path).format_map(options))
    current_lib_size = lib_path.stat().st_size
    log.info(f'{lib_path} size = {current_lib_size}byte\n')
    if current_lib_size > threshold_size:
        if not options['STRIP_BINARIES']:
            log.warning("Library size could exceed threshold because stripping build binaries option is OFF")
        raise Exception(f"{lib_path.name} size = {current_lib_size}byte exceeds max_size = {threshold_size}byte")

# Choose repository in accordance with prefix of product type
if product_type.startswith("public"):
    repo_name = 'MediaSDK'
elif product_type.startswith("private"):
    repo_name = 'Next-GEN'
else:
    raise IOError(f"Unknown product type '{product_type}'")


action('count api version and build number',
       callfunc=(set_env, [MEDIA_SDK_REPO_DIR, GCC_LATEST, CLANG_VERSION], {}))

# Build dependencies
# Build LibVA
action('LibVA: autogen.sh',
       cmd=get_building_cmd(f'./autogen.sh', GCC_LATEST, ENABLE_DEVTOOLSET),
       work_dir=LIBVA_REPO_DIR)

action('LibVA: build',
       cmd=get_building_cmd(f'make -j`nproc`', GCC_LATEST, ENABLE_DEVTOOLSET),
       work_dir=LIBVA_REPO_DIR)

action('LibVA: list artifacts',
       cmd=f'echo " " && ls ./va',
       work_dir=LIBVA_REPO_DIR,
       verbose=True)

action('install',
       stage=stage.INSTALL,
       work_dir=LIBVA_REPO_DIR,
       cmd=get_building_cmd(f'make DESTDIR={LIBVA_BUILD_DIR} install', GCC_LATEST, ENABLE_DEVTOOLSET))

cmake_command = ['cmake']

cmake_command.append('--no-warn-unused-cli')
cmake_command.append('-Wno-dev -G "Unix Makefiles"')

#Build without -Werror option in case of clang:
#TODO: use the same command as for 'gcc'
if args.get('compiler') == "clang":
    cmake_command.append(
        '-DCMAKE_C_FLAGS_RELEASE="-O2 -Wformat -Wformat-security -Wall -D_FORTIFY_SOURCE=2 -fstack-protector-strong"')
    cmake_command.append(
        '-DCMAKE_CXX_FLAGS_RELEASE="-O2 -Wformat -Wformat-security -Wall -D_FORTIFY_SOURCE=2 -fstack-protector-strong"')
#Default parameters (default flow):
else:
    cmake_command.append(
        '-DCMAKE_C_FLAGS_RELEASE="-O2 -Wformat -Wformat-security -Wall -Werror -D_FORTIFY_SOURCE=2 -DNDEBUG -fstack-protector-strong"')
    cmake_command.append(
        '-DCMAKE_CXX_FLAGS_RELEASE="-O2 -Wformat -Wformat-security -Wall -Werror -D_FORTIFY_SOURCE=2 -DNDEBUG -fstack-protector-strong"')

#In all builders except Fastboot or clang build use parameter `-DENABLE_TOOLS=ON`:
if 'defconfig' not in product_type and not args.get('fastboot') and not args.get('compiler') == "clang":
    cmake_command.append('-DBUILD_ALL=ON')
    cmake_command.append('-DENABLE_ALL=ON')
    cmake_command.append('-DENABLE_ITT=ON')

#Additional (custom) options (they extend default parameters):
if args.get('fastboot'):
    fastboot_cmake_path = MEDIA_SDK_REPO_DIR / 'builder/profiles/fastboot.cmake'
    cmake_command.append(f'-DMFX_CONFIG_FILE={fastboot_cmake_path}')

if args.get('api_latest'):
    cmake_command.append('-DAPI:STRING=latest')

cmake_command.append(str(MEDIA_SDK_REPO_DIR))

cmake = ' '.join(cmake_command)

# Change system libva
options["ENV"]['PKG_CONFIG_PATH'] = f'{LIBVA_BUILD_DIR}/{LIBVA_CONFIG_DIR}/lib/pkgconfig'

action('cmake',
       cmd=get_building_cmd(cmake, GCC_LATEST, ENABLE_DEVTOOLSET))

action('build',
       cmd=get_building_cmd(f'make -j{options["CPU_CORES"]}', GCC_LATEST, ENABLE_DEVTOOLSET))

action('list artifacts',
       cmd=f'echo " " && ls ./__bin/release',
       verbose=True)

#TODO: add check for clang compiler
if args.get('compiler') == "gcc":
    action('used compiler',
           cmd=f'echo " " && strings -f ./__bin/release/*.so | grep GCC',
           verbose=True)                            

#TODO: `|| echo` is a temporary fix in situations if nothing found by grep (return code 1)
action('binary versions',
       cmd=f'echo " " && strings -f ./__bin/release/*.so | grep mediasdk || echo',
       verbose=True)

action('install',
       stage=stage.INSTALL,
       cmd=get_building_cmd(f'make DESTDIR={options["INSTALL_DIR"]} install', GCC_LATEST, ENABLE_DEVTOOLSET))

if args.get('fastboot'):
    # TODO: Pass data between stages with pickle in build scripts instead
    action('count api version and build number',
            stage=stage.INSTALL,
            callfunc=(set_env, [MEDIA_SDK_REPO_DIR, GCC_LATEST, CLANG_VERSION], {}))

    action('check fastboot lib size',
           stage=stage.INSTALL,
           callfunc=(check_lib_size, [FASTBOOT_LIB_MAX_SIZE, MEDIA_SDK_BUILD_DIR / '__bin/release/libmfxhw64-fastboot.so.{ENV[API_VERSION]}'], {}))

# Create rpm and deb packages of libva
# TODO: get libva version from manifest
# if options['BUILD_TYPE'] == 'release':
action('create rpm package',
           stage=stage.PACK,
           work_dir=LIBVA_BUILD_DIR,
           cmd=get_packing_cmd("rpm", LIBVA_CONFIG_DIR, PACKAGES_TARGET_DIRS))


action('create deb package',
           stage=stage.PACK,
           work_dir=LIBVA_BUILD_DIR,
           cmd=get_packing_cmd("deb", LIBVA_CONFIG_DIR, PACKAGES_TARGET_DIRS))

DEV_PKG_DATA_TO_ARCHIVE.extend([
    {
        'from_path': options['ROOT_DIR'],
        'relative': [
            {
                'path': options['BUILD_DIR'] / '__bin',
                'pack_as': 'mediasdk/bin'
            },
            {
                'path': options['BUILD_DIR'] / 'plugins.cfg',
                'pack_as': 'mediasdk/bin/release/plugins.cfg'
            },
        ]
    }
])

INSTALL_PKG_DATA_TO_ARCHIVE.extend([
    {
        'from_path': options['INSTALL_DIR'],
        'relative': [
            {
                'path': 'opt',
            }
        ]
    },
    {
        'from_path': options['DEPENDENCIES_DIR'],
        'relative': [
            {
                'path': 'libva',
                'pack_as': 'dependencies/libva'
            }
        ]
    }
])