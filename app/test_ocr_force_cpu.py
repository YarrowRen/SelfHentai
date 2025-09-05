#!/usr/bin/env python3
"""
强制在 CPU 上运行 manga-ocr，完全禁用 MPS
"""

import os
# 在导入任何 torch 相关模块之前设置环境变量
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'
# 强制使用 CPU
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['MPS_VISIBLE_DEVICES'] = ''

try:
    print('1. 导入并配置 PyTorch...')
    import torch
    
    # 猴子补丁：禁用 MPS
    original_is_available = torch.backends.mps.is_available
    torch.backends.mps.is_available = lambda: False
    
    print(f'PyTorch 版本: {torch.__version__}')
    print(f'MPS 可用状态（已禁用）: {torch.backends.mps.is_available()}')
    print(f'默认设备: {torch.get_default_device() if hasattr(torch, "get_default_device") else "N/A"}')
    
    print('2. 导入 manga-ocr...')
    from manga_ocr import MangaOcr
    print('✅ manga-ocr 导入成功')
    
    print('3. 初始化模型（CPU 模式）...')
    model = MangaOcr()
    print('✅ MangaOcr 模型初始化成功!')
    
    print('4. 测试模型推理...')
    from PIL import Image
    
    # 创建一个简单的测试图像
    test_img = Image.new('RGB', (200, 100), color='white')
    result = model(test_img)
    print(f'✅ 测试推理成功，结果: "{result}"')
    
    # 恢复原始函数（可选）
    torch.backends.mps.is_available = original_is_available
    
except Exception as e:
    print(f'❌ 错误: {e}')
    import traceback
    traceback.print_exc()