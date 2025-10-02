#!/usr/bin/env python3
"""Test import agenthub module"""

import sys
sys.path.insert(0, '/Users/nguyenbinhan/Workspace/AgentAI/Onyx/onyx/backend')

try:
    from onyx.server.features.agenthub.api import router
    print('✓ Import thành công!')
    print(f'Router prefix: {router.prefix}')
    print(f'Router tags: {router.tags}')
    print(f'Number of routes: {len(router.routes)}')
    
    for route in router.routes:
        print(f'  - {route.methods} {route.path}')
        
except Exception as e:
    print(f'✗ Lỗi import: {e}')
    import traceback
    traceback.print_exc()
