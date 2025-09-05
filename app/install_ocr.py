#!/usr/bin/env python3
"""
manga-ocr 依赖安装脚本
解决 TensorFlow 版本兼容性问题
"""

import subprocess
import sys
import platform

def run_command(cmd):
    """执行命令并显示输出"""
    print(f"执行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"错误: {result.stderr}")
    return result.returncode == 0

def install_ocr_dependencies():
    """安装 OCR 相关依赖"""
    print("=== 安装 manga-ocr 依赖 ===")
    
    # 检测系统类型
    system = platform.system()
    machine = platform.machine()
    print(f"系统类型: {system} {machine}")
    
    # 1. 卸载可能冲突的 TensorFlow 版本
    print("\n1. 清理现有 TensorFlow 安装...")
    run_command("pip uninstall -y tensorflow tensorflow-macos tensorflow-metal")
    
    # 2. 安装基础依赖
    print("\n2. 安装基础依赖...")
    run_command("pip install pillow==10.1.0")
    
    # 3. 根据系统类型安装 TensorFlow
    print("\n3. 安装 TensorFlow...")
    if system == "Darwin" and machine == "arm64":
        # Apple Silicon Mac - 使用可用的最新版本
        print("检测到 Apple Silicon Mac，安装 tensorflow-macos")
        success = run_command("pip install tensorflow-macos==2.13.0")
        if success:
            # 尝试安装 tensorflow-metal，如果失败也继续
            print("尝试安装 tensorflow-metal...")
            run_command("pip install tensorflow-metal")
    else:
        # 其他系统
        print("安装标准 TensorFlow")
        run_command("pip install tensorflow==2.13.1")
    
    # 4. 安装其他 ML 依赖
    print("\n4. 安装其他机器学习依赖...")
    
    # 由于 tokenizers 编译问题，使用已有的新版本 transformers
    print("使用现有的 transformers 版本（跳过降级）")
    
    # 只安装缺失的依赖
    run_command("pip install jaconv fire loguru unidic-lite fugashi pyperclip")
    
    # PyTorch (根据系统选择版本)
    if system == "Darwin" and machine == "arm64":
        # Apple Silicon Mac
        run_command("pip install torch==2.0.1 torchvision==0.15.2")
    else:
        run_command("pip install torch==2.0.1 torchvision==0.15.2")
    
    # 5. 最后安装 manga-ocr
    print("\n5. 安装 manga-ocr...")
    success = run_command("pip install manga-ocr==0.1.11")
    
    if success:
        print("\n=== 安装完成 ===")
        print("正在测试安装...")
        test_success = test_installation()
        if test_success:
            print("✅ manga-ocr 安装成功！")
        else:
            print("❌ 安装可能有问题，请检查错误信息")
    else:
        print("\n❌ 安装失败")

def test_installation():
    """测试安装是否成功"""
    try:
        import tensorflow as tf
        print(f"TensorFlow 版本: {tf.__version__}")
        
        from manga_ocr import MangaOcr
        print("manga-ocr 导入成功")
        
        # 尝试初始化模型（这会下载模型文件）
        print("初始化模型（首次运行会下载模型文件，请稍等...）")
        model = MangaOcr()
        print("✅ 模型初始化成功")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("manga-ocr 依赖安装脚本")
    print("这将安装 manga-ocr 及其依赖项")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_installation()
    else:
        install_ocr_dependencies()