from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging
import asyncio
import aiofiles
import re
from core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

class ConfigModel(BaseModel):
    EXHENTAI_BASE_URL: str = "https://exhentai.org/favorites.php"
    EXHENTAI_COOKIE_MEMBER_ID: str = ""
    EXHENTAI_COOKIE_PASS_HASH: str = ""
    EXHENTAI_COOKIE_IGNEOUS: str = ""
    JM_USERNAME: str = ""
    JM_PASSWORD: str = ""
    JM_APP_VERSION: str = "1.8.0"
    JM_API_BASES: List[str] = []
    # AI翻译配置
    TRANSLATION_PROVIDER: str = "volcano"
    TRANSLATION_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    TRANSLATION_MODEL: str = "doubao-1-5-lite-32k-250115"
    TRANSLATION_API_KEY_ENV: str = "ARK_API_KEY"
    ARK_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    DASHSCOPE_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    # OCR服务配置
    OCR_ENABLED: bool = False

class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None

# 获取 .env 文件路径
def get_env_file_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

# 读取环境变量配置
async def read_env_config() -> ConfigModel:
    """从 .env 文件读取配置"""
    env_file = get_env_file_path()
    config = ConfigModel()
    
    if not os.path.exists(env_file):
        logger.warning(f".env file not found at {env_file}")
        return config
    
    try:
        async with aiofiles.open(env_file, 'r', encoding='utf-8') as f:
            content = await f.read()
            
        # 解析环境变量
        for line in content.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                
                if key == 'EXHENTAI_BASE_URL':
                    config.EXHENTAI_BASE_URL = value
                elif key == 'EXHENTAI_COOKIE_MEMBER_ID':
                    config.EXHENTAI_COOKIE_MEMBER_ID = value
                elif key == 'EXHENTAI_COOKIE_PASS_HASH':
                    config.EXHENTAI_COOKIE_PASS_HASH = value
                elif key == 'EXHENTAI_COOKIE_IGNEOUS':
                    config.EXHENTAI_COOKIE_IGNEOUS = value
                elif key == 'JM_USERNAME':
                    config.JM_USERNAME = value
                elif key == 'JM_PASSWORD':
                    config.JM_PASSWORD = value
                elif key == 'JM_APP_VERSION':
                    config.JM_APP_VERSION = value
                elif key == 'JM_API_BASES':
                    # 分割逗号分隔的API地址
                    config.JM_API_BASES = [url.strip() for url in value.split(',') if url.strip()]
                # AI翻译配置
                elif key == 'TRANSLATION_PROVIDER':
                    config.TRANSLATION_PROVIDER = value
                elif key == 'TRANSLATION_BASE_URL':
                    config.TRANSLATION_BASE_URL = value
                elif key == 'TRANSLATION_MODEL':
                    config.TRANSLATION_MODEL = value
                elif key == 'TRANSLATION_API_KEY_ENV':
                    config.TRANSLATION_API_KEY_ENV = value
                elif key == 'ARK_API_KEY':
                    config.ARK_API_KEY = value
                elif key == 'OPENAI_API_KEY':
                    config.OPENAI_API_KEY = value
                elif key == 'ANTHROPIC_API_KEY':
                    config.ANTHROPIC_API_KEY = value
                elif key == 'DASHSCOPE_API_KEY':
                    config.DASHSCOPE_API_KEY = value
                elif key == 'GEMINI_API_KEY':
                    config.GEMINI_API_KEY = value
                elif key == 'OCR_ENABLED':
                    config.OCR_ENABLED = value.lower() in ("true", "1", "yes", "on")
                    
    except Exception as e:
        logger.error(f"Error reading .env file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read configuration: {str(e)}")
    
    return config

# 写入环境变量配置
async def write_env_config(config: ConfigModel) -> bool:
    """写入配置到 .env 文件"""
    env_file = get_env_file_path()
    
    try:
        # 读取现有文件内容
        existing_content = ""
        if os.path.exists(env_file):
            async with aiofiles.open(env_file, 'r', encoding='utf-8') as f:
                existing_content = await f.read()
        
        # 要更新的配置项
        config_items = {
            'EXHENTAI_BASE_URL': config.EXHENTAI_BASE_URL,
            'EXHENTAI_COOKIE_MEMBER_ID': config.EXHENTAI_COOKIE_MEMBER_ID,
            'EXHENTAI_COOKIE_PASS_HASH': config.EXHENTAI_COOKIE_PASS_HASH,
            'EXHENTAI_COOKIE_IGNEOUS': config.EXHENTAI_COOKIE_IGNEOUS,
            'JM_USERNAME': config.JM_USERNAME,
            'JM_PASSWORD': config.JM_PASSWORD,
            'JM_APP_VERSION': config.JM_APP_VERSION,
            'JM_API_BASES': ','.join(config.JM_API_BASES),
            # AI翻译配置
            'TRANSLATION_PROVIDER': config.TRANSLATION_PROVIDER,
            'TRANSLATION_BASE_URL': config.TRANSLATION_BASE_URL,
            'TRANSLATION_MODEL': config.TRANSLATION_MODEL,
            'TRANSLATION_API_KEY_ENV': config.TRANSLATION_API_KEY_ENV,
            'ARK_API_KEY': config.ARK_API_KEY,
            'OPENAI_API_KEY': config.OPENAI_API_KEY,
            'ANTHROPIC_API_KEY': config.ANTHROPIC_API_KEY,
            'DASHSCOPE_API_KEY': config.DASHSCOPE_API_KEY,
            'GEMINI_API_KEY': config.GEMINI_API_KEY,
            'OCR_ENABLED': str(config.OCR_ENABLED).lower()
        }
        
        lines = existing_content.split('\n') if existing_content else []
        updated_keys = set()
        
        # 更新现有行
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key = line.split('=')[0].strip()
                if key in config_items:
                    lines[i] = f"{key}={config_items[key]}"
                    updated_keys.add(key)
        
        # 添加新的配置项
        for key, value in config_items.items():
            if key not in updated_keys:
                lines.append(f"{key}={value}")
        
        # 写入文件
        new_content = '\n'.join(lines)
        async with aiofiles.open(env_file, 'w', encoding='utf-8') as f:
            await f.write(new_content)
            
        logger.info("Configuration saved successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error writing .env file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")

@router.get("/config", response_model=ConfigModel)
async def get_config():
    """获取当前配置"""
    try:
        config = await read_env_config()
        return config
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config")
async def save_config(config: ConfigModel):
    """保存配置"""
    try:
        # 验证 EXHENTAI_BASE_URL
        valid_ex_urls = [
            "https://exhentai.org/favorites.php",
            "https://e-hentai.org/favorites.php"
        ]
        if config.EXHENTAI_BASE_URL not in valid_ex_urls:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid EXHENTAI_BASE_URL. Must be one of: {', '.join(valid_ex_urls)}"
            )
        
        # 验证 JM_API_BASES 格式
        if config.JM_API_BASES:
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
            for url in config.JM_API_BASES:
                if not url_pattern.match(url):
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Invalid URL format: {url}"
                    )
        
        success = await write_env_config(config)
        if success:
            return {"message": "Configuration saved successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save configuration")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_connection(config: ConfigModel):
    """测试连接配置"""
    import aiohttp
    
    results = {}
    all_success = True
    
    try:
        async with aiohttp.ClientSession() as session:
            # 测试 ExHentai 连接
            if config.EXHENTAI_COOKIE_MEMBER_ID and config.EXHENTAI_COOKIE_PASS_HASH:
                try:
                    cookies = {
                        'ipb_member_id': config.EXHENTAI_COOKIE_MEMBER_ID,
                        'ipb_pass_hash': config.EXHENTAI_COOKIE_PASS_HASH,
                    }
                    if config.EXHENTAI_COOKIE_IGNEOUS:
                        cookies['igneous'] = config.EXHENTAI_COOKIE_IGNEOUS
                    
                    timeout = aiohttp.ClientTimeout(total=10)
                    async with session.get(
                        config.EXHENTAI_BASE_URL, 
                        cookies=cookies, 
                        timeout=timeout
                    ) as response:
                        if response.status == 200:
                            content = await response.text()
                            if 'This page requires you to log on.' not in content:
                                results['exhentai'] = {'success': True, 'message': 'ExHentai连接成功'}
                            else:
                                results['exhentai'] = {'success': False, 'message': 'ExHentai需要登录'}
                                all_success = False
                        else:
                            results['exhentai'] = {'success': False, 'message': f'ExHentai连接失败: HTTP {response.status}'}
                            all_success = False
                            
                except asyncio.TimeoutError:
                    results['exhentai'] = {'success': False, 'message': 'ExHentai连接超时'}
                    all_success = False
                except Exception as e:
                    results['exhentai'] = {'success': False, 'message': f'ExHentai连接错误: {str(e)}'}
                    all_success = False
            else:
                results['exhentai'] = {'success': False, 'message': 'ExHentai配置信息不完整'}
                all_success = False
            
            # 测试 JM API 连接
            if config.JM_API_BASES:
                jm_results = []
                for api_base in config.JM_API_BASES[:3]:  # 只测试前3个
                    try:
                        timeout = aiohttp.ClientTimeout(total=5)
                        async with session.get(f"{api_base}/login", timeout=timeout) as response:
                            if response.status in [200, 404, 405]:  # 404/405也表示服务器响应
                                jm_results.append({'url': api_base, 'success': True})
                            else:
                                jm_results.append({'url': api_base, 'success': False, 'error': f'HTTP {response.status}'})
                    except Exception as e:
                        jm_results.append({'url': api_base, 'success': False, 'error': str(e)})
                
                successful_jm = [r for r in jm_results if r['success']]
                if successful_jm:
                    results['jm'] = {
                        'success': True, 
                        'message': f'JM API连接成功 ({len(successful_jm)}/{len(jm_results)} 个可用)',
                        'details': jm_results
                    }
                else:
                    results['jm'] = {
                        'success': False, 
                        'message': 'JM API连接全部失败',
                        'details': jm_results
                    }
                    all_success = False
            else:
                results['jm'] = {'success': False, 'message': 'JM API地址未配置'}
                all_success = False
            
            # 测试AI翻译服务连接
            translation_api_key = getattr(config, config.TRANSLATION_API_KEY_ENV, "")
            if config.TRANSLATION_BASE_URL and translation_api_key:
                try:
                    # 简单测试API端点是否可达
                    timeout = aiohttp.ClientTimeout(total=10)
                    headers = {}
                    
                    # 根据不同的服务商设置请求头
                    if 'openai' in config.TRANSLATION_BASE_URL.lower() or 'api.openai.com' in config.TRANSLATION_BASE_URL:
                        headers['Authorization'] = f'Bearer {translation_api_key}'
                    elif 'anthropic' in config.TRANSLATION_BASE_URL.lower():
                        headers['x-api-key'] = translation_api_key
                        headers['anthropic-version'] = '2023-06-01'
                    elif 'dashscope' in config.TRANSLATION_BASE_URL.lower():
                        headers['Authorization'] = f'Bearer {translation_api_key}'
                    elif 'googleapis.com' in config.TRANSLATION_BASE_URL.lower():
                        headers['x-goog-api-key'] = translation_api_key
                    elif 'volces.com' in config.TRANSLATION_BASE_URL.lower():
                        headers['Authorization'] = f'Bearer {translation_api_key}'
                    
                    # 测试模型列表端点
                    models_url = f"{config.TRANSLATION_BASE_URL.rstrip('/')}/models"
                    async with session.get(models_url, headers=headers, timeout=timeout) as response:
                        if response.status in [200, 401, 403]:  # 200成功，401/403表示服务响应但认证问题
                            if response.status == 200:
                                results['translation'] = {
                                    'success': True, 
                                    'message': f'翻译服务连接成功 (模型: {config.TRANSLATION_MODEL})'
                                }
                            else:
                                results['translation'] = {
                                    'success': False, 
                                    'message': f'翻译服务连接成功但认证失败 (HTTP {response.status})'
                                }
                                all_success = False
                        else:
                            results['translation'] = {
                                'success': False, 
                                'message': f'翻译服务连接失败: HTTP {response.status}'
                            }
                            all_success = False
                            
                except asyncio.TimeoutError:
                    results['translation'] = {'success': False, 'message': '翻译服务连接超时'}
                    all_success = False
                except Exception as e:
                    results['translation'] = {'success': False, 'message': f'翻译服务连接错误: {str(e)}'}
                    all_success = False
            else:
                results['translation'] = {'success': False, 'message': '翻译服务配置信息不完整'}
                all_success = False
        
        overall_message = "所有连接测试成功" if all_success else "部分连接测试失败"
        
        return TestConnectionResponse(
            success=all_success,
            message=overall_message,
            details=results
        )
        
    except Exception as e:
        logger.error(f"Connection test error: {e}")
        return TestConnectionResponse(
            success=False,
            message=f"连接测试失败: {str(e)}",
            details=results
        )