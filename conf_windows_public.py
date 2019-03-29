PRODUCT_REPOS = [
    {'name': 'MediaSDK'},
    # Give possibility to build windows for changes from product configs repository
    {'name': 'product-configs'}
]

BUILD_ENVIRONMENT = {
    'INTELMEDIASDKROOT': str(options['REPOS_DIR'] / 'MediaSDK' / 'api'),
    'MINIDDK_ROOT': r'C:\Program Files (x86)\Windows Kits\10',
    'MINIDDK_VERSION': '10.0.17134.0',
    'MSBuildEmitSolution': '1'
}


def clean_msbuild_dirs(repos_dir):
    import shutil

    build_dir = repos_dir / 'build'
    if build_dir.exists():
        log.info('remove directory %s', build_dir)
        shutil.rmtree(build_dir)

action(
    'Clean msbuild dirs',
    stage=stage.CLEAN,
    callfunc=(clean_msbuild_dirs, [options['REPOS_DIR']], {})
)

for platform in ['x64', 'Win32']:
    vs_component(
        f"Build dispatcher (2015) {platform}",
        solution_path=options['REPOS_DIR'] / r'MediaSDK\api\mfx_dispatch\windows\libmfx_vs2015.sln',
        msbuild_args={
            '/property': {
                'Platform': platform
            }
        },
        env=BUILD_ENVIRONMENT
    )

    INSTALL_PKG_DATA_TO_ARCHIVE.extend([{
        'from_path': options['REPOS_DIR'] / 'build',
        'relative': [
            {
                'path': rf'win_{platform}\lib\libmfx_vs2015_d.idb'
            },
            {
                'path': rf'win_{platform}\lib\libmfx_vs2015_d.lib'
            },
            {
                'path': rf'win_{platform}\lib\libmfx_vs2015_d.pdb'
            }
        ]
    }])

    DEV_PKG_DATA_TO_ARCHIVE.extend([{
        'from_path': options['REPOS_DIR'] / 'build',
        'relative': [
            {
                'path': rf'win_{platform}'
            }
        ]
    }])

