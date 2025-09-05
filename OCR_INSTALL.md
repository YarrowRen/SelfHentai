# manga-ocr 安装指南

## 问题描述
遇到错误：`module 'tensorflow' has no attribute 'Tensor'`

这是 TensorFlow 版本兼容性问题。manga-ocr 需要特定版本的 TensorFlow。

## 解决方案

### 方案1：自动安装脚本（推荐）
```bash
cd app
python install_ocr.py
```

### 方案2：手动安装

#### 第一步：清理环境
```bash
pip uninstall -y tensorflow tensorflow-macos tensorflow-metal
```

#### 第二步：安装兼容版本
**普通系统 (Windows/Linux/Intel Mac):**
```bash
pip install tensorflow==2.13.1
pip install transformers==4.21.3
pip install torch==2.0.1 torchvision==0.15.2
pip install manga-ocr==0.1.11
```

**Apple Silicon Mac (M1/M2):**
```bash
pip install tensorflow-macos==2.13.1
pip install tensorflow-metal==1.1.0
pip install transformers==4.21.3
pip install torch==2.0.1 torchvision==0.15.2
pip install manga-ocr==0.1.11
```

#### 第三步：测试安装
```bash
cd app
python install_ocr.py --test
```

## 常见问题

### Q1: 下载模型很慢怎么办？
A: manga-ocr 首次运行时会自动下载模型文件（约500MB），这是正常的。请耐心等待。

### Q2: 内存不足
A: manga-ocr 模型需要约2GB内存。如果内存不足，可以考虑：
- 关闭其他应用程序
- 使用方案2或方案3（懒加载）

### Q3: Apple Silicon Mac 特殊问题
A: 确保使用 tensorflow-macos 和 tensorflow-metal 而不是普通的 tensorflow。

## 验证安装
成功安装后，重启后端服务：
```bash
cd app
python main.py
```

看到以下信息表示成功：
```
正在加载 manga-ocr 模型，这可能需要一些时间...
TensorFlow 版本: 2.13.1
正在初始化 MangaOcr 模型，这可能需要下载模型文件...
manga-ocr 模型加载完成！
```

## 性能优化建议
- 首次启动会比较慢（下载和加载模型）
- 后续启动会快很多（模型已缓存）
- 建议在内存充足的环境下运行