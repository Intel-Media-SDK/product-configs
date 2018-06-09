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


#TODO: move functions to the shared module
def set_env(repo_path):
    def _get_commit_number(repo_path):
        import git
        git_repo = git.Git(repo_path)
        return str(git_repo.rev_list('--count', 'HEAD'))

    def _get_api_version(repo_path):
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

    api_ver = _get_api_version(repo_path)
    build_num = _get_commit_number(str(repo_path))

    plugin_version = f'{api_ver}.3.{build_num}'
    options["ENV"]["API_VERSION"] = api_ver
    options["ENV"]['MFX_VERSION'] = f'7.0.16093{build_num}'
    options["ENV"]['MFX_HEVC_VERSION'] = f'{plugin_version}'
    options["ENV"]['MFX_H265FEI_VERSION'] = f'{plugin_version}'
    options["ENV"]['MFX_VP8_VERSION'] = f'{plugin_version}'
    options["ENV"]['MFX_VP9_VERSION'] = f'{plugin_version}'
    options["ENV"]['MFX_H264LA_VERSION'] = f'{plugin_version}'

    options["ENV"]['MFX_HOME'] = f'{str(repo_path)}'

PRODUCT_REPOS = [
    {'name': 'MediaSDK'},
    #{'name': 'flow_test'},
]

options["STRIP_BINARIES"] = True

ENABLE_DEVTOOLSET = 'source /opt/rh/devtoolset-6/enable'

MEDIA_SDK_REPO_DIR = options.get('REPOS_DIR') / PRODUCT_REPOS[0]['name']

action('count api version and build number',
       callfunc=(set_env, [MEDIA_SDK_REPO_DIR], {}))

action('compiler version',
       cmd=f'{ENABLE_DEVTOOLSET} && echo " " && gcc --version',
       verbose=True)

cmake_command = ['cmake',
                 '--no-warn-unused-cli',
                 '-Wno-dev -G "Unix Makefiles"',
                 '-DWARNING_FLAGS="-Wall -Werror"',
                 f'-DCMAKE_BUILD_TYPE:STRING={options["BUILD_TYPE"]}',
                 '-DCMAKE_C_FLAGS_RELEASE="-O2 -D_FORTIFY_SOURCE=2 -fstack-protector"',
                 '-DCMAKE_CXX_FLAGS_RELEASE="-O2 -D_FORTIFY_SOURCE=2 -fstack-protector"',
                ]

if args.get('api_latest') == "true": #build with api_latest
    cmake_command.append('-DAPI:STRING=latest')

cmake_command.append(str(MEDIA_SDK_REPO_DIR))

cmake = ' '.join(cmake_command)

action('cmake',
       cmd=f'{ENABLE_DEVTOOLSET} && {cmake}')

action('build',
       cmd=f'{ENABLE_DEVTOOLSET} && make -j{options["CPU_CORES"]}')

action('list artifacts',
       cmd=f'echo " " && ls ./__bin/release',
       verbose=True)

action('binary versions',
       cmd=f'echo " " && strings -f ./__bin/release/*.so | grep mediasdk',
       verbose=True)

action('install',
       stage=stage.INSTALL,
       cmd=f'{ENABLE_DEVTOOLSET} && make DESTDIR={options["INSTALL_DIR"]} install')


DEV_PKG_DATA_TO_ARCHIVE = [
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
            }
        ]
    }
]

INSTALL_PKG_DATA_TO_ARCHIVE = [
    {
        'from_path': options['INSTALL_DIR'],
        'relative': [
            {
                'path': 'opt'
            }
        ]
    }
]
