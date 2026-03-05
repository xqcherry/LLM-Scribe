import asyncio

from loguru import logger
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Playwright, ViewportSize


class HTMLRenderer:
    """HTML 转图片渲染器"""

    def __init__(self, browser_path: Optional[str] = None):
        self.browser_path = browser_path
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._lock = asyncio.Lock()

    async def _ensure_browser(self):
        """确保浏览器已启动（线程/协程安全版）"""
        if self._browser is not None:
            return self._browser

        async with self._lock:
            # 双重检查锁,使用锁确保同一时间只有一个初始化任务
            if self._browser is None:
                logger.info("正在启动 Chromium 浏览器...")
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    executable_path=self.browser_path,
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
                )
        return self._browser

    async def html_render_to_img(
            self,
            html_content: str,
            img_opt: Optional[Dict[str, Any]] = None,
    ) -> Optional[bytes]:
        """渲染 HTML 字符串为图片"""
        image_options = img_opt or {}
        image_type = image_options.get("type", "jpeg")
        quality = image_options.get("quality", 95)
        full_page = image_options.get("full_page", True)
        viewport_width = image_options.get("width", 750)  # 建议固定宽度，长图更美观

        try:
            browser = await self._ensure_browser()

            # 为每个请求创建独立的上下文，防止 Cookie 或缓存污染
            # device_scale_factor=2 保证了视网膜屏级别的高清效果
            context = await browser.new_context(
                viewport=ViewportSize(width=viewport_width, height=1000),  # 使用类型构造
                device_scale_factor=2,
            )

            page = await context.new_page()
            try:
                # 设置 HTML
                await page.set_content(html_content, wait_until="networkidle", timeout=30000)

                # 如果你的模板有渐变或动画，给一点点渲染缓冲时间
                await page.wait_for_timeout(200)

                screenshot_bytes = await page.screenshot(
                    type=image_type,
                    quality=quality if image_type == "jpeg" else None,
                    full_page=full_page,
                )
                return screenshot_bytes
            finally:
                # 只关闭页面和上下文，不关闭浏览器进程
                await page.close()
                await context.close()

        except Exception as e:
            logger.error(f"HTML 渲染异常: {e}", exc_info=True)
            return None

    async def close(self):
        """服务关闭时调用，退出浏览器"""
        if self._browser:
            await self._browser.close()
            await self._playwright.stop()
            logger.info("浏览器已关闭")