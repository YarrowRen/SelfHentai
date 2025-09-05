"""
AI 翻译服务模块
使用火山引擎 API 进行日文到中文的专业漫画翻译
"""

import logging
import os
from typing import Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class TranslationService:
    """AI 翻译服务类，管理火山引擎 API 调用"""
    
    def __init__(self):
        self.client = None
        self.is_initialized = False
        self.model_name = "doubao-seed-1-6-250615"
        
        # 专业漫画翻译 Prompt
        self.translation_prompt = """**你的身份**

* 你是"日→中漫画翻译 agent"。你的唯一目标：在理解语境的前提下，把可能含有 OCR 错误的日文文本**纠正后**准确翻译为自然流畅的**简体中文**。
* 不进行创作与删改，不做剧透或点评，不自行审查或弱化用词；只做纠错与忠实翻译。若平台政策必须约束内容，请在不改变核心意义的前提下采用中性表达，而非删减。

---

## 翻译流程（必须逐步执行，但不要在输出中显式展现步骤）

1. **纠错清洗**
   * 修正 OCR 常见错误：长音、假名/片假名混淆、助词误读、汉字近形、符号错位等。
   * 根据上下文补齐省略，恢复自然语序。
   * 合并同气泡断行，分离不同文本块。

2. **语境判定**
   * 判别对白、独白、旁白、拟声词（SFX）、招牌/界面文字。
   * 推断角色语气（尊敬/随意/粗口/撒娇/吐槽等）。

3. **术语与称谓**
   * 保持人名、地名、专有名词统一。
   * 敬称映射：
     * さん → "先生/小姐/同学"等
     * ちゃん → "小X/—酱"
     * くん → "同学/君"
     * 様 → "大人/阁下/您"
     * 先輩 → "前辈"，先生 → "老师"
   * 第一/二人称根据语境自然化。

4. **翻译策略**
   * 忠实准确，中文口语自然。
   * 保持粗口、俚语力度，避免弱化。
   * 双关/梗：保留笑点，必要时加【译注】（≤20字）。
   * 标点：使用中文全角，省略号统一"……"。

5. **拟声词（SFX）**
   * 画面拟声词采用双轨：`原文（中文释义）`，如 `ドン（砰！）`。
   * 若与剧情强相关，可加【译注】。

6. **不确定性**
   * 模糊/多解：给出最自然的译文，并在行尾加 `〔? 备选：…〕`。
   * 难辨字符用 `□` 占位，并附猜测。

7. **一致性与校对**
   * 统一译名、称谓、标点。
   * 保持角色口吻前后一致。

---

## 输出要求（纯中文模式）

* 仅输出中文译文，按输入顺序逐条分段。
* 拟声词用 `原文（中文释义）` 格式。
* 必要的【译注】直接写在行尾。
* 不输出原文，不输出纠错过程，不输出说明。

---

请翻译以下日文文本："""
        
    def initialize(self):
        """初始化火山引擎 API 客户端"""
        if self.is_initialized:
            logger.info("翻译服务已经初始化，跳过")
            return True
            
        try:
            # 获取 API Key
            api_key = os.environ.get("ARK_API_KEY")
            if not api_key:
                logger.error("未找到 ARK_API_KEY 环境变量")
                return False
            
            # 初始化火山引擎客户端
            self.client = OpenAI(
                base_url="https://ark.cn-beijing.volces.com/api/v3",
                api_key=api_key,
            )
            
            self.is_initialized = True
            logger.info("火山引擎翻译服务初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"翻译服务初始化失败: {str(e)}")
            return False
    
    def translate_text(self, japanese_text: str, target_language: str = "zh") -> dict:
        """
        翻译日文文本到指定语言
        
        Args:
            japanese_text: 日文原文
            target_language: 目标语言代码，暂时只支持 zh (中文)
            
        Returns:
            {"success": bool, "translation": str, "error": str}
        """
        if not self.is_initialized:
            if not self.initialize():
                return {
                    "success": False,
                    "translation": "",
                    "error": "翻译服务初始化失败"
                }
        
        if not japanese_text or not japanese_text.strip():
            return {
                "success": False,
                "translation": "",
                "error": "输入文本为空"
            }
        
        if target_language != "zh":
            return {
                "success": False,
                "translation": "",
                "error": f"暂不支持目标语言: {target_language}，目前只支持中文 (zh)"
            }
        
        try:
            logger.info(f"开始翻译日文文本，长度: {len(japanese_text)}")
            
            # 构建翻译请求
            messages = [
                {
                    "role": "user",
                    "content": f"{self.translation_prompt}\n\n{japanese_text}"
                }
            ]
            
            # 调用火山引擎 API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3,  # 较低的温度确保翻译的一致性
                max_tokens=1000,  # 限制响应长度
            )
            
            # 提取翻译结果
            if response.choices and len(response.choices) > 0:
                translation = response.choices[0].message.content.strip()
                
                logger.info(f"翻译完成，结果长度: {len(translation)}")
                
                return {
                    "success": True,
                    "translation": translation,
                    "error": ""
                }
            else:
                logger.error("API 响应中没有翻译结果")
                return {
                    "success": False,
                    "translation": "",
                    "error": "API 响应格式错误"
                }
                
        except Exception as e:
            logger.error(f"翻译请求失败: {str(e)}")
            return {
                "success": False,
                "translation": "",
                "error": f"翻译失败: {str(e)}"
            }
    
    def get_status(self) -> dict:
        """获取翻译服务状态"""
        return {
            "is_initialized": self.is_initialized,
            "api_key_available": bool(os.environ.get("ARK_API_KEY")),
            "model_name": self.model_name
        }


# 全局翻译服务实例
translation_service = TranslationService()