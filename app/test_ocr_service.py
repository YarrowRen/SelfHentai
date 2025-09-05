#!/usr/bin/env python3
"""
测试修复后的 OCR 服务
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

try:
    print('🔧 测试修复后的 OCR 服务')
    print('=' * 50)
    
    print('1. 导入 OCR 服务...')
    from services.ocr_service import ocr_service
    
    print('2. 加载 OCR 模型...')
    ocr_service.load_model()
    
    print('3. 检查服务状态...')
    status = ocr_service.get_status()
    print(f'   模型加载状态: {status["is_loaded"]}')
    print(f'   模型可用性: {status["model_available"]}')
    
    if status["is_loaded"]:
        print('4. 测试 OCR 识别...')
        
        # 创建一个测试用的 base64 图片
        from PIL import Image
        import io
        import base64
        
        # 创建白底黑字测试图片
        img = Image.new('RGB', (200, 100), color='white')
        
        # 转换为 base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        img_data = f"data:image/png;base64,{img_base64}"
        
        # 进行 OCR 识别
        result = ocr_service.recognize_text(img_data)
        print(f'   OCR 识别结果: "{result}"')
        
        print('✅ OCR 服务测试完成！')
    else:
        print('❌ OCR 模型未成功加载')
        
except Exception as e:
    print(f'❌ 测试失败: {e}')
    import traceback
    traceback.print_exc()