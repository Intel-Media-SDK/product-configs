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
def set_commit_number(repo_path):
    import git
    git_repo = git.Git(repo_path)
    commits = git_repo.log('--all', '--oneline')
    DEFAULT_OPTIONS["ENV"]["BUILD_NUMBER"] = str(len(commits.splitlines()))

def set_additional_env(repo_path):
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

    mediasdk_api_header_path = pathlib.Path(repo_path) / 'api' / 'include' / 'mfxdefs.h'

    with open(mediasdk_api_header_path, 'r') as lines:
        for line in lines:
            major_version = re.search("MFX_VERSION_MAJOR\s(\d+)", line)
            if major_version:
                minor_version = re.search("MFX_VERSION_MINOR\s(\d+)", next(lines))
                api_ver = f"{major_version.group(1)}.{minor_version.group(1)}"
                build_num = DEFAULT_OPTIONS["ENV"].get("BUILD_NUMBER", 0)
                DEFAULT_OPTIONS["ENV"]["API_VERSION"] = api_ver
                PLUGIN_VERSION = f'{api_ver}.3.${build_num}'
                DEFAULT_OPTIONS["ENV"]['MFX_VERSION'] = f'7.0.16093{build_num}',
                DEFAULT_OPTIONS["ENV"]['MFX_HEVC_VERSION'] = f'{PLUGIN_VERSION}',
                DEFAULT_OPTIONS["ENV"]['MFX_H265FEI_VERSION'] = f'{PLUGIN_VERSION}',
                DEFAULT_OPTIONS["ENV"]['MFX_VP8_VERSION'] = f'{PLUGIN_VERSION}',
                DEFAULT_OPTIONS["ENV"]['MFX_VP9_VERSION'] = f'{PLUGIN_VERSION}',
                DEFAULT_OPTIONS["ENV"]['MFX_H264LA_VERSION'] = f'{PLUGIN_VERSION}',


PRODUCT_REPOS = [
    {'name': 'MediaSDK'},
    #{'name': 'flow_test'},
]

ENABLE_DEVTOOLSET = 'source /opt/rh/devtoolset-6/enable'

MEDIA_SDK_REPO_DIR = DEFAULT_OPTIONS.get('REPOS_DIR') / PRODUCT_REPOS[0]['name']

action('count build_number',
       callfunc=(set_commit_number, [str(MEDIA_SDK_REPO_DIR)], {}))

action('count api_version',
       callfunc=(set_additional_env, [MEDIA_SDK_REPO_DIR], {}))

BUILD_ENVIRONMENT = {
    'MFX_HOME': str(MEDIA_SDK_REPO_DIR)
}

CMAKE_CFG = 'intel64.make.' + DEFAULT_OPTIONS.get('BUILD_TYPE')
DEFAULT_OPTIONS['BUILD_DIR'] = MEDIA_SDK_REPO_DIR / '__cmake' / CMAKE_CFG


action('compiler version',
       cmd=f'{ENABLE_DEVTOOLSET} && gcc --version')

action('cmake',
       cmd=f'{ENABLE_DEVTOOLSET} && perl tools/builder/build_mfx.pl --cmake={CMAKE_CFG}',
       work_dir=MEDIA_SDK_REPO_DIR,
       env=BUILD_ENVIRONMENT)

action('build',
       cmd=f'{ENABLE_DEVTOOLSET} && make -j{DEFAULT_OPTIONS["CPU_CORES"]}',
       env=BUILD_ENVIRONMENT)

action('install',
       stage=Stage.INSTALL,
       cmd=f'{ENABLE_DEVTOOLSET} && make DESTDIR={DEFAULT_OPTIONS["INSTALL_DIR"]} install')

DEV_PKG_DATA_TO_ARCHIVE = [
    {
        'from_path': DEFAULT_OPTIONS['BUILD_DIR'],
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
        'from_path': DEFAULT_OPTIONS['INSTALL_DIR'],
        'relative': [
            {
                'path': 'opt'
            }
        ]
    }
]
