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

MEDIA_SDK_REPO_NAME = 'MediaSDK'

DEPENDENCIES = [
    'libva'
]

ENABLE_DEVTOOLSET = 'source /opt/rh/devtoolset-6/enable'
# Workaround to run fpm tool on CentOS 6.9
ENABLE_RUBY24 = 'source /opt/rh/rh-ruby24/enable'
GCC_LATEST = '9.2.0'
CLANG_VERSION = '9'
options["STRIP_BINARIES"] = True
MEDIA_SDK_REPO_DIR = options.get('REPOS_DIR') / MEDIA_SDK_REPO_NAME
MEDIA_SDK_BUILD_DIR = options.get('BUILD_DIR')

# Full build log for checking SDL options
VERBOSE_BUILD_OUTPUT = True

# Max size = current fastboot lib size + ~50Kb
FASTBOOT_LIB_MAX_SIZE = 1 * 1024 * 1024 + 256 * 1024  # byte

MSDK_LIB_INSTALL_DIR = '/usr'


def set_env(repo_path, gcc_latest, clang_version):
    build_num = get_commit_number(repo_path)
    api_major_ver, api_minor_ver = get_api_version(f'{repo_path.name}/api')

    plugin_version = f'{api_major_ver}.{api_minor_ver}.3.{build_num}'
    options["ENV"]["API_VERSION"] = f'{api_major_ver}.{api_minor_ver}'
    options["ENV"]['MFX_VERSION'] = f'8.0.16093{build_num}'
    options["ENV"]['MFX_HEVC_VERSION'] = f'{plugin_version}'
    options["ENV"]['MFX_H265FEI_VERSION'] = f'{plugin_version}'
    options["ENV"]['MFX_VP8_VERSION'] = f'{plugin_version}'
    options["ENV"]['MFX_VP9_VERSION'] = f'{plugin_version}'
    options["ENV"]['MFX_H264LA_VERSION'] = f'{plugin_version}'
    options["ENV"]['MFX_HOME'] = f'{str(repo_path)}'

    compiler_version = args.get('compiler_version')
    if args.get('compiler') == "gcc" and compiler_version == gcc_latest:
        # TODO: Add possibility to choose other gcc versions
        options["ENV"]['CC'] = '/usr/bin/gcc-9'
        options["ENV"]['CXX'] = '/usr/bin/g++-9'
        
    elif args.get('compiler') == "clang" and compiler_version == clang_version:
        options["ENV"]['CC'] = f'/usr/bin/clang-{compiler_version}'
        options["ENV"]['CXX'] = f'/usr/bin/clang++-{compiler_version}'
        options["ENV"]['ASM'] = f'/usr/bin/clang-{compiler_version}'


# TODO: add more smart logic or warnings?! (potential danger zone)
def get_building_cmd(command, gcc_latest, enable_devtoolset):
    # Ubuntu Server: gcc_latest or clang
    if args.get('compiler') == "clang" or (args.get('compiler') == "gcc" and args.get('compiler_version') == gcc_latest):
        return command
    else:
        return f'{enable_devtoolset} && {command}' #enable new compiler on CentOS


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

# Prepare dependencies
LIBVA_PATH = options['DEPENDENCIES_DIR'] / 'libva' / 'usr' / 'local'
LIBVA_PKG_CONFIG_PATH = LIBVA_PATH / 'lib64' / 'pkgconfig'
LIBVA_PKG_CONFIG_RPM_PATTERN = {
    '^prefix=.+': f'prefix={LIBVA_PATH}',
}

action('LibVA: change pkgconfigs',
       stage=stage.EXTRACT,
       callfunc=(update_config, [LIBVA_PKG_CONFIG_PATH, LIBVA_PKG_CONFIG_RPM_PATTERN], {}))


action('count api version and build number',
       callfunc=(set_env, [MEDIA_SDK_REPO_DIR, GCC_LATEST, CLANG_VERSION], {}))


cmake_command = ['cmake3', '--no-warn-unused-cli', '-Wno-dev -G "Unix Makefiles"', '-LA']
cmake_command.append('-DCMAKE_INSTALL_PREFIX=/usr')
cmake_command.append('-DCMAKE_INSTALL_LIBDIR=lib64')
cmake_command.append('-DMFX_MODULES_DIR=/usr/lib64')

# TODO: make build for deb
# cmake_command.append('-DCMAKE_INSTALL_LIBDIR=lib/x86_64-linux-gnu')
# cmake_command.append('-DMFX_MODULES_DIR=/usr/lib/x86_64-linux-gnu')

# Default parameters (default flow):
cmake_command.append(
    '-DCMAKE_C_FLAGS_RELEASE="-O2 -Wformat -Wformat-security -Wall -Werror -D_FORTIFY_SOURCE=2 -fstack-protector-strong"')
cmake_command.append(
    '-DCMAKE_CXX_FLAGS_RELEASE="-O2 -Wformat -Wformat-security -Wall -Werror -D_FORTIFY_SOURCE=2 -fstack-protector-strong"')

cmake_command.append('-DBUILD_TESTS=ON ')

# In all builders except Fastboot or clang build use parameter `-DENABLE_TOOLS=ON`:
if 'defconfig' not in product_type and not args.get('fastboot'):
    cmake_command.append('-DBUILD_ALL=ON')
    cmake_command.append('-DENABLE_ALL=ON')
    cmake_command.append('-DENABLE_ITT=ON')

# Additional (custom) options (they extend default parameters):
if args.get('fastboot'):
    fastboot_cmake_path = MEDIA_SDK_REPO_DIR / 'builder/profiles/fastboot.cmake'
    cmake_command.append(f'-DMFX_CONFIG_FILE={fastboot_cmake_path}')

if args.get('api_latest') or args.get('compiler') == "clang" or \
    (args.get('compiler') == "gcc" and args.get('compiler_version') == GCC_LATEST and not args.get('fastboot')):
    cmake_command.append('-DAPI:STRING=latest')

cmake_command.append(str(MEDIA_SDK_REPO_DIR))

cmake = ' '.join(cmake_command)

action('cmake',
       cmd=get_building_cmd(cmake, GCC_LATEST, ENABLE_DEVTOOLSET),
       env={'PKG_CONFIG_PATH': str(LIBVA_PKG_CONFIG_PATH)})

BUILD_VERBOSE = 'VERBOSE=1' if VERBOSE_BUILD_OUTPUT else ''
action('build',
       cmd=get_building_cmd(f'make {BUILD_VERBOSE} -j{options["CPU_CORES"]}', GCC_LATEST, ENABLE_DEVTOOLSET))

action('list artifacts',
       cmd=f'echo " " && ls ./__bin/release',
       verbose=True)

# TODO: add check for clang compiler
if args.get('compiler') == "gcc":
    action('used compiler',
           cmd=f'echo " " && strings -f ./__bin/release/*.so | grep GCC',
           verbose=True)

# TODO: `|| echo` is a temporary fix in situations if nothing found by grep (return code 1)
action('binary versions',
       cmd=f'echo " " && strings -f ./__bin/release/*.so | grep mediasdk || echo',
       verbose=True)

if build_event != 'klocwork':
    action('run_unit_tests',
           cmd=f'ctest --verbose',
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


# Create configuration files
intel_mdf_conf = options["INSTALL_DIR"] / 'intel-mdf.conf'
data = '/opt/intel/msdk_driver/lib64'

action('create intel-mdf.conf',
       stage=stage.INSTALL,
       callfunc=(create_file, [intel_mdf_conf, data], {}))

# Get api version for MediaSDK package
action('count api version and build number',
       stage=stage.PACK,
       callfunc=(set_env, [MEDIA_SDK_REPO_DIR, GCC_LATEST, CLANG_VERSION], {}))

# Get package installation dirs for MediaSDK
pack_dir = options['INSTALL_DIR'] / MSDK_LIB_INSTALL_DIR[1:]

RPM_MEDIASDK_PACK_DIRS = [
    f'{pack_dir}/={MSDK_LIB_INSTALL_DIR}/',
    f'{options["INSTALL_DIR"]}/intel-mdf.conf=/etc/ld.so.conf.d/'
]

BUILD_NUM = get_commit_number(MEDIA_SDK_REPO_DIR)

action('MediaSDK: create rpm pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('rpm', RPM_MEDIASDK_PACK_DIRS, ENABLE_RUBY24, '{ENV[API_VERSION]}' + f'.{BUILD_NUM}', MEDIA_SDK_REPO_NAME.lower()))

DEB_MEDIASDK_PACK_DIRS = [
    f'{pack_dir}/bin/={MSDK_LIB_INSTALL_DIR}/bin/',
    f'{pack_dir}/include/={MSDK_LIB_INSTALL_DIR}/include/',
    f'{pack_dir}/share/={MSDK_LIB_INSTALL_DIR}/share/',
    f'{pack_dir}/lib64={MSDK_LIB_INSTALL_DIR}/lib/x86_64-linux-gnu',
    f'{options["INSTALL_DIR"]}/intel-mdf.conf=/etc/ld.so.conf.d/',
]

action('MediaSDK: create deb pkg',
       stage=stage.PACK,
       work_dir=options['PACK_DIR'],
       cmd=get_packing_cmd('deb', DEB_MEDIASDK_PACK_DIRS, ENABLE_RUBY24, '{ENV[API_VERSION]}' + f'.{BUILD_NUM}', MEDIA_SDK_REPO_NAME.lower()))

DEV_PKG_DATA_TO_ARCHIVE.extend([
    {
        'from_path': options['BUILD_DIR'],
        'relative': [
            {
                'path': '__bin',
                'pack_as': 'bin'
            },
            {
                'path': 'plugins.cfg',
                'pack_as': 'bin/release/plugins.cfg'
            },
        ]
    }
])

INSTALL_PKG_DATA_TO_ARCHIVE.extend([
    {
        'from_path': options['INSTALL_DIR'],
        'relative': [
            {
                'path': 'usr'
            }
        ]
    },
])
