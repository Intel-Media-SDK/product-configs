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
This file is an example which represents how to write product configurations
for Media SDK needs.

The main thing you have to know about these configurations that it is simple
Python-code with the build scripts (`build_runner.py`) API extension so you can
use all goodies of Python language.
There is only some API things which will help you by writting configuration.
They will be covered in this file.

This example is based on open source Media SDK build config
with some unnecessary things for this build but it needed to show you all ascpects.

Let`s go!
"""

# ==============================================================================
# Some general information
# ==============================================================================
"""
Media SDK open source dir layout:
root_dir                - "sandbox" on machine where all actions are executed
    install             - ...
    logs                - folder with all logs by stages
        build.log
        copy.log
        extract.log
        install.log
        pack.log
    pack                - packed artifacts and logs to send it to the share
    repos               - git repo(s) in target state which are used to build product
        repo_1
        repo_2
        ...
    repos_forked        - git repo in target state which is used to build product in case of pull request from forked Github repo
        repo_1
"""

"""
What are stages?
By default process of CI "building" has following stages:
- clean                 - clean work folders from previous run
- extract               - extract git repositories and checkout them to the needed state
- build                 - build product by instructions which are written in product configuration
- install               - (optional) prepare product package
- pack                  - pack all artifacts and logs (tar or zip with minimal compression)
- copy                  - copy packed artifacts and logs to the share
"""


# ==============================================================================
# Configuration: variables
# ==============================================================================
"""
At first you have to mention which repositories should be extracted to build the product.
You have to use aliases (names of repositories). All available aliases defined in:
`infrastructure/common/mediasdk_directories.py` variable `_repositories`
"""
PRODUCT_REPOS = [
    {'name': 'MediaSDK'},
]


"""
You can specify the build with help of variable `DEFAULT_OPTIONS` 
which has following data (from `infrastructure/build_scripts/build_runner.py`):

self.default_options = {
    "ROOT_DIR": root_dir,
    "REPOS_DIR": root_dir / "repos",
    "REPOS_FORKED_DIR": root_dir / "repos_forked",
    "BUILD_DIR": root_dir / "build",
    "INSTALL_DIR": root_dir / "install",
    "PACK_DIR": root_dir / "pack",
    "LOGS_DIR": root_dir / "logs",
    "BUILD_TYPE": build_type,  # sets from command line argument ('release' by default)
    "CPU_CORES": multiprocessing.cpu_count()  # count of logical CPU cores
}
"""
"""
Here some examples:
"""
MEDIA_SDK_REPO_DIR = DEFAULT_OPTIONS.get('REPOS_DIR') / PRODUCT_REPOS[0]['name']
CMAKE_CFG = 'intel64.make.' + DEFAULT_OPTIONS.get('BUILD_TYPE')

DEFAULT_OPTIONS['BUILD_DIR'] = MEDIA_SDK_REPO_DIR / '__cmake' / CMAKE_CFG


# ==============================================================================
# Configuration: actions
# ==============================================================================
"""
In each stage there are some actions. By using function `action()` you can 
specify what to do (how to build, how to store some metrics,
store compiler version and so on).

Signature of function:
def action(name, stage='build', cmd=None, work_dir=None, env=None, script=None, call_func=None):
    :param stage: build stage, can be: clean, extract, build, install, pack, copy

name - name of the action which will be printed in log
stage - specifies during which stage this action should be executed (by default `BUILD`)
cmd - your command what you want to do
work_dir - where to execute your `cmd`
env - use it to define environment variables during this action execution

Examples:
"""
action('cmake', cmd=f'perl tools/builder/build_mfx.pl --cmake={CMAKE_CFG}',
       work_dir=MEDIA_SDK_REPO_DIR,
       env={'MFX_HOME': str(MEDIA_SDK_REPO_DIR)})

action('build', cmd=f'make -j{DEFAULT_OPTIONS["CPU_CORES"]}')

action('install', stage=Stage.INSTALL, cmd=f'make DESTDIR={DEFAULT_OPTIONS["INSTALL_DIR"]} install')

"""
If you want to execute multiple commands during one actions you can use `&&`:
"""
DEVTOOLSET = 'source /opt/rh/devtoolset-6/enable'
action('compiler version', cmd=f'{DEVTOOLSET} && gcc --version')

"""
Or execute them as a list:
"""
COMMANDS = [
    'source /opt/rh/devtoolset-6/enable',
    'gcc --version',
]
action('compiler version', cmd=COMMANDS)

"""
On Ubuntu we recommend to call `bash -c "<your commands>"` because default
shell on Ubuntu is `dash` :(
"""
DEVTOOLSET = 'source /opt/rh/devtoolset-6/enable'
action('compiler version', cmd=f'bash -c "{DEVTOOLSET} && gcc --version"')


# ==============================================================================
# Configuration: archiving
# ==============================================================================
"""
After the build you can specify what to archive with help of variables:
- `DEV_PKG_DATA_TO_ARCHIVE`
- `INSTALL_PKG_DATA_TO_ARCHIVE`

Examples:
"""
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
