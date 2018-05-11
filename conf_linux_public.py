# Copyright (c) 2017 Intel Corporation
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


PRODUCT_REPOS = [
    {'name': 'MediaSDK'},
    #{'name': 'flow_test'},
]

ENABLE_DEVTOOLSET='source /opt/rh/devtoolset-6/enable'

MEDIA_SDK_REPO_DIR = DEFAULT_OPTIONS.get('REPOS_DIR') / PRODUCT_REPOS[0]['name']
CMAKE_CFG = 'intel64.make.' + DEFAULT_OPTIONS.get('BUILD_TYPE')

DEFAULT_OPTIONS['BUILD_DIR'] = MEDIA_SDK_REPO_DIR / '__cmake' / CMAKE_CFG

action('compiler version', cmd=f'{ENABLE_DEVTOOLSET} && gcc --version')

action('cmake', cmd=f'{ENABLE_DEVTOOLSET} && perl tools/builder/build_mfx.pl --cmake={CMAKE_CFG}',
       work_dir=MEDIA_SDK_REPO_DIR,
       env={'MFX_HOME': str(MEDIA_SDK_REPO_DIR)})

action('build', cmd=f'{ENABLE_DEVTOOLSET} && make -j{DEFAULT_OPTIONS["CPU_CORES"]}')

action('install', stage=Stage.INSTALL, cmd=f'{ENABLE_DEVTOOLSET} && make DESTDIR={DEFAULT_OPTIONS["INSTALL_DIR"]} install'])

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
