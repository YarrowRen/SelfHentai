# app/utils/websocket_logger.py

import asyncio
import logging

from api.websocket import active_connections


class WebSocketLogHandler(logging.Handler):
    """
    自定义日志 handler，用于将日志消息通过 WebSocket 推送到前端。
    """

    def __init__(self, loop=None):
        super().__init__()
        # 使用传入的事件循环或尝试自动获取主线程的事件循环
        try:
            self.loop = loop or asyncio.get_event_loop_policy().get_event_loop()
        except RuntimeError:
            self.loop = None  # 无法获取事件循环（如子线程），跳过发送

    def emit(self, record):
        """
        格式化日志记录并异步广播到所有活跃的 WebSocket 连接。
        """
        log_entry = self.format(record)

        if not self.loop:
            return  # 无法获取事件循环，跳过广播

        try:
            # 在线程中调度协程到事件循环中执行
            future = asyncio.run_coroutine_threadsafe(self.broadcast(log_entry), self.loop)

            # 添加回调用于捕获异常（可选）
            future.add_done_callback(
                lambda f: f.exception() and logging.getLogger(__name__).error(f"WebSocketLogHandler error: {f.exception()}")
            )

        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to schedule broadcast: {e}")

    async def broadcast(self, message: str):
        """
        向所有活跃的 WebSocket 客户端发送日志信息。
        """
        for conn in list(active_connections):
            try:
                await conn.send_text(message)
            except Exception:
                pass  # 忽略发送失败
