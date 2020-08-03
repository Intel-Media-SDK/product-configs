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

INSTALL = ['libva', 'libva-utils', 'gmmlib', 'ffmpeg', 'metrics-calc-lite', 'media-driver', 'mediasdk']

TEST_SCRIPT_PATH = infra_path / 'driver_tests'
TEST_ENV = {
    'MFX_HOME': '/opt/intel/mediasdk',
    'LD_LIBRARY_PATH': '/opt/intel/mediasdk/lib64',
    'LIBVA_DRIVERS_PATH': '/opt/intel/msdk_driver/lib64',
    'LIBVA_DRIVER_NAME': 'iHD'
}

DRIVER_TESTS = [
    'CABA1_SVA_B',
    'CABA1_Sony_D',
    'avc_cbr_001',
    'avc_cqp_001',
    'scale_001'
]

ARTIFACTS_LAYOUT = {
    str(options['LOGS_DIR']): 'logs',
    str(infra_path / 'ted/results'): 'mediasdk',
    str(infra_path / 'smoke_test' / 'hevc_fei_tests_res.log'): 'hevc_fei_tests.log'
}

action(f'Create temp dir for driver tests',
       work_dir=TEST_SCRIPT_PATH,
       cmd=f'mkdir -p temp',
       verbose=True)

for test_id in DRIVER_TESTS:
    action(f'Run media-driver test {test_id}',
           work_dir=TEST_SCRIPT_PATH,
           cmd=f'python3 run_test.py {test_id}',
           env=TEST_ENV,
           verbose=True)

action(f'Run MediaSDK TED test',
       work_dir=infra_path,
       cmd=f'python3 ted/ted.py',
       env=TEST_ENV,
       verbose=True)

action(f'Run MediaSDK fei test',
       work_dir=infra_path,
       cmd=f'python3 smoke_test/hevc_fei_smoke_test.py',
       env=TEST_ENV,
       verbose=True)
