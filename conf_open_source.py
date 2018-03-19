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

"""
Media SDK open source product configuration

See the API documentation at the end of this configuration

Root dir Layout:
root_dir
    repos
        repo1
        repo2
    build
    install
    logs
        clean
            _all.log
            name1.log
            name2.log
        extract
            _all.log
            repo1.log
            repo2.log
        build
            _all.log
            name1.log
            name2.log
        install
            _all.log
            name1.log
"""

PRODUCT_REPOS = [
    {'name': 'MediaSDK'},
    #{'name': 'flow_test'},
]

DEVTOOLSET = [
    'scl enable devtoolset-6 bash',
]

MEDIA_SDK_REPO_DIR = DEFAULT_OPTIONS.get('REPOS_DIR') / PRODUCT_REPOS[0]['name']
CMAKE_CFG = 'intel64.make.' + DEFAULT_OPTIONS.get('BUILD_TYPE')

DEFAULT_OPTIONS['BUILD_DIR'] = MEDIA_SDK_REPO_DIR / '__cmake' / CMAKE_CFG

#action('cmake', cmd=DEVTOOLSET + [f'perl tools/builder/build_mfx.pl --cmake={CMAKE_CFG}'],
#       work_dir=MEDIA_SDK_REPO_DIR,
#       env={'MFX_HOME': str(MEDIA_SDK_REPO_DIR)})
action('cmake', cmd=f'perl tools/builder/build_mfx.pl --cmake={CMAKE_CFG}',
       work_dir=MEDIA_SDK_REPO_DIR,
       env={'MFX_HOME': str(MEDIA_SDK_REPO_DIR)})

#action('build', cmd=DEVTOOLSET + [f'make -j{DEFAULT_OPTIONS["CPU_CORES"]}'])
action('build', cmd=f'make -j{DEFAULT_OPTIONS["CPU_CORES"]}')

#action('install', stage=Stage.INSTALL, cmd=DEVTOOLSET + [f'make DESTDIR={DEFAULT_OPTIONS["INSTALL_DIR"]} install'])
action('install', stage=Stage.INSTALL, cmd=f'make DESTDIR={DEFAULT_OPTIONS["INSTALL_DIR"]} install')

DATA_TO_ARCHIVE = [
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

# ==============================================================================
# For pylint checking and API documentation only
# ==============================================================================
DEFAULT_OPTIONS = {}


class Stage(object):
    BUILD = "build"


def action(name, stage='build', cmd=None, work_dir=None, env=None, script=None, call_func=None):
    """
    Call the specified function.
    Example:
        action("install", stage="install", call_func=(func, args))

    :param stage: build stage, can be: clean, extract, build, install, pack, copy
    :return: None (status True, False? or exceptions)
    """
    print('DEMO action', stage, call_func)