# app/utils/exhentai_utils.py

import json
import os
import re

import requests
from bs4 import BeautifulSoup
from core.logger import get_logger


class ExHentaiUtils:
    def __init__(self, base_url, cookies: dict, logger=None):
        self.base_url = base_url
        self.cookies = cookies
        self.logger = logger or get_logger(__name__)
        self.session = requests.Session()
        self.session.cookies.update(cookies)

    def extract_favorites(self):
        """
        按页提取收藏夹中的本子信息，包括 gid、token、分类和收藏时间。
        """
        result = []
        next_page = self.base_url

        while next_page:
            self.logger.info(f"正在爬取: {next_page}")
            response = self.session.get(next_page)
            if response.status_code != 200:
                self.logger.error(f"请求失败，状态码: {response.status_code}")
                break

            soup = BeautifulSoup(response.content, "html.parser")
            rows = soup.select("table.itg tr")

            for row in rows:
                try:
                    # 提取 gid 和 token
                    link = row.select_one('a[href*="/g/"]')
                    if not link:
                        continue
                    match = re.search(r"/g/(\d+)/(\w+)", link["href"])
                    if not match:
                        continue
                    gid, token = match.groups()

                    # 提取分类
                    fav_category_elem = row.select_one("div[title]")
                    fav_category = fav_category_elem["title"].strip() if fav_category_elem else "Unknown"

                    # 提取收藏时间
                    fav_time_elem = row.select("td.glfc p")
                    fav_time = " ".join(p.text.strip() for p in fav_time_elem) if fav_time_elem else "Unknown"

                    result.append(
                        {
                            "gid": gid,
                            "token": token,
                            "favCategory": fav_category,
                            "favTime": fav_time,
                        }
                    )
                except Exception:
                    self.logger.exception("解析错误")

            # 获取下一页链接
            next_link = soup.select_one("div.searchnav a#unext")
            if next_link and "href" in next_link.attrs:
                next_page = (
                    next_link["href"]
                    if next_link["href"].startswith("http")
                    else self.base_url.rsplit("/", 1)[0] + next_link["href"]
                )
            else:
                next_page = None

        return result

    def fetch_gallery_metadatas(self, favorites: list, max_retries: int = 5, retry_delay: float = 2.0):
        """
        批量获取画廊元数据，带重试机制确保数据完整性和顺序一致性

        参数:
            favorites: List[dict]，包含 'gid' 和 'token'
            max_retries: 最大重试次数（默认5次）
            retry_delay: 重试延迟秒数（默认2秒）

        返回:
            List[dict]，每个本子的元数据（保持原始顺序）
            
        异常:
            如果有批次在重试后仍然失败，抛出异常
        """
        import time
        
        url = "https://api.e-hentai.org/api.php"
        # 使用字典存储批次数据，key为批次开始索引，确保顺序
        batch_results = {}
        failed_batches = []
        total_batches = (len(favorites) + 24) // 25
        
        self.logger.info(f"开始获取元数据，共 {total_batches} 批，每批最多25条")

        # 第一轮：处理所有批次
        for i in range(0, len(favorites), 25):
            batch = favorites[i : i + 25]
            batch_num = i // 25 + 1
            
            success, batch_data = self._fetch_single_batch_with_result(url, batch, batch_num)
            if success:
                batch_results[i] = batch_data
            else:
                failed_batches.append((i, batch, batch_num))
        
        # 重试失败的批次
        if failed_batches:
            self.logger.warning(f"第一轮完成，有 {len(failed_batches)} 个批次失败，开始重试...")
            
            for retry_round in range(1, max_retries + 1):
                if not failed_batches:
                    break
                    
                self.logger.info(f"第 {retry_round} 轮重试，处理 {len(failed_batches)} 个失败批次...")
                remaining_failed = []
                
                for i, batch, batch_num in failed_batches:
                    self.logger.info(f"重试第 {batch_num} 批（第{retry_round}次重试）...")
                    time.sleep(retry_delay)  # 延迟重试
                    
                    success, batch_data = self._fetch_single_batch_with_result(url, batch, batch_num)
                    if success:
                        batch_results[i] = batch_data
                    else:
                        remaining_failed.append((i, batch, batch_num))
                
                failed_batches = remaining_failed
                
                if failed_batches:
                    self.logger.warning(f"第 {retry_round} 轮重试完成，还有 {len(failed_batches)} 个批次失败")
                else:
                    self.logger.info(f"第 {retry_round} 轮重试完成，所有批次成功！")
                    break
        
        # 检查是否还有失败的批次
        if failed_batches:
            failed_batch_nums = [str(batch_num) for _, _, batch_num in failed_batches]
            error_msg = f"经过 {max_retries} 次重试后，仍有 {len(failed_batches)} 个批次失败（批次: {', '.join(failed_batch_nums)}），为保证数据完整性，同步已终止"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # 按原始顺序组装最终结果
        all_metadata = []
        for i in range(0, len(favorites), 25):
            if i in batch_results:
                all_metadata.extend(batch_results[i])
        
        self.logger.info(f"所有批次处理完成，成功获取 {len(all_metadata)} 条元数据（顺序已保持）")
        return all_metadata
    
    def _fetch_single_batch_with_result(self, url: str, batch: list, batch_num: int) -> tuple:
        """
        获取单个批次的数据，返回数据和成功状态
        
        返回:
            tuple: (是否成功, 数据列表)
        """
        gidlist = [[int(f["gid"]), f["token"]] for f in batch]
        payload = {"method": "gdata", "gidlist": gidlist, "namespace": 1}
        
        self.logger.info(f"正在请求第 {batch_num} 批，共 {len(batch)} 条数据...")
        
        try:
            res = requests.post(url, json=payload, timeout=30)
            res.raise_for_status()
            data = res.json().get("gmetadata", [])
            
            if len(data) != len(batch):
                self.logger.warning(f"第 {batch_num} 批返回数据不完整：期望 {len(batch)} 条，实际 {len(data)} 条")
            
            self.logger.info(f"第 {batch_num} 批成功，获取 {len(data)} 条数据")
            return True, data
            
        except Exception as e:
            self.logger.error(f"第 {batch_num} 批请求失败: {str(e)}")
            return False, []

    def _fetch_single_batch(self, url: str, batch: list, batch_num: int, all_metadata: list) -> bool:
        """
        获取单个批次的数据（兼容性方法）
        
        返回:
            bool: 是否成功
        """
        success, data = self._fetch_single_batch_with_result(url, batch, batch_num)
        if success:
            all_metadata.extend(data)
        return success

    def get_favorites_metadata(self, max_retries: int = 5, retry_delay: float = 2.0):
        """
        高层封装：从收藏夹获取所有本子元数据。
        
        参数:
            max_retries: 最大重试次数
            retry_delay: 重试延迟秒数
        """
        favorites = self.extract_favorites()
        return self.fetch_gallery_metadatas(favorites, max_retries=max_retries, retry_delay=retry_delay)

    def export_favorites_metadata(self, output_path="favorites_metadata.json"):
        """
        提取收藏夹中所有本子的元数据并保存为 JSON 文件

        参数:
            output_path: 输出文件路径，默认为 favorites_metadata.json
        """
        self.logger.info("开始提取收藏夹信息...")
        favorites = self.extract_favorites()
        self.logger.info(f"共提取到 {len(favorites)} 项收藏")

        self.logger.info("开始获取元数据...")
        metadata = self.fetch_gallery_metadatas(favorites)
        self.logger.info(f"成功获取 {len(metadata)} 项元数据")

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            self.logger.info(f"已保存至 {os.path.abspath(output_path)}")
        except Exception:
            self.logger.exception("保存失败")

    def fetch_gallery_thumbnails(self, gid: str, token: str, page: int = 0):
        """
        获取画廊的缩略图数据
        
        参数:
            gid: Gallery ID
            token: Gallery token  
            page: 页码，从0开始
            
        返回:
            dict: 包含缩略图数据、分页信息等
        """
        url = f"https://exhentai.org/g/{gid}/{token}/"
        if page > 0:
            url += f"?p={page}"
            
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # 提取分页信息
            pagination_info = {}
            gpc_elem = soup.select_one(".gpc")
            if gpc_elem:
                # 例如: "Showing 1 - 20 of 258 images"
                match = re.search(r"Showing (\d+) - (\d+) of (\d+) images", gpc_elem.text)
                if match:
                    pagination_info = {
                        "start": int(match.group(1)),
                        "end": int(match.group(2)), 
                        "total": int(match.group(3))
                    }
            
            # 提取分页导航
            page_links = []
            ptt_elem = soup.select_one(".ptt")
            if ptt_elem:
                for link in ptt_elem.select("td a"):
                    href = link.get("href", "")
                    text = link.text.strip()
                    if href and text.isdigit():
                        # 提取页码参数
                        page_match = re.search(r"p=(\d+)", href)
                        page_num = int(page_match.group(1)) if page_match else 0
                        page_links.append({
                            "page": page_num,
                            "display": text,
                            "url": href
                        })
                        
            # 当前页码
            current_page = page
            total_pages = 0
            if page_links:
                total_pages = max(link["page"] for link in page_links) + 1
            
            # 提取缩略图数据
            thumbnails = []
            gdt_elem = soup.select_one("#gdt")
            if gdt_elem:
                for link in gdt_elem.select("a"):
                    href = link.get("href", "")
                    div = link.select_one("div")
                    if div and href:
                        title = div.get("title", "")
                        style = div.get("style", "")
                        
                        # 解析背景图片URL和位置
                        bg_match = re.search(r"url\(([^)]+)\)", style)
                        pos_match = re.search(r"(-?\d+)px\s+(\d+)\s+no-repeat", style)
                        size_match = re.search(r"width:(\d+)px;height:(\d+)px", style)
                        
                        thumbnail_data = {
                            "page_url": href,
                            "title": title,
                        }
                        
                        if bg_match:
                            thumbnail_data["background_url"] = bg_match.group(1)
                            
                        if pos_match:
                            thumbnail_data["bg_position"] = {
                                "x": int(pos_match.group(1)),
                                "y": int(pos_match.group(2))
                            }
                            
                        if size_match:
                            thumbnail_data["size"] = {
                                "width": int(size_match.group(1)),
                                "height": int(size_match.group(2))
                            }
                            
                        # 提取页码信息
                        page_match = re.search(r"/s/[^/]+/\d+-(\d+)", href)
                        if page_match:
                            thumbnail_data["page_number"] = int(page_match.group(1))
                            
                        thumbnails.append(thumbnail_data)
            
            return {
                "thumbnails": thumbnails,
                "pagination": {
                    "current_page": current_page,
                    "total_pages": total_pages,
                    "page_info": pagination_info,
                    "page_links": page_links
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取缩略图失败: {e}")
            return {
                "thumbnails": [],
                "pagination": {
                    "current_page": 0,
                    "total_pages": 0,
                    "page_info": {},
                    "page_links": []
                },
                "error": str(e)
            }

    def fetch_full_image(self, gid: str, token: str, page: int):
        """
        获取画廊的完整大图信息
        
        参数:
            gid: Gallery ID
            token: Gallery token
            page: 页码，从1开始（用户界面显示）
            
        返回:
            dict: 包含大图URL、图片名称、画廊标题等信息
        """
        # 首先获取缩略图页面的跳转链接
        thumb_page = max(0, (page - 1) // 20)  # 缩略图页面从0开始
        thumb_index = (page - 1) % 20  # 该页面中第几个缩略图
        
        try:
            # 获取缩略图页面
            thumb_url = f"https://exhentai.org/g/{gid}/{token}/"
            if thumb_page > 0:
                thumb_url += f"?p={thumb_page}"
                
            response = self.session.get(thumb_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # 获取画廊标题
            title_elem = soup.select_one("#gn")
            gallery_title = title_elem.text.strip() if title_elem else "Unknown Gallery"
            
            # 获取总页数信息
            gpc_elem = soup.select_one(".gpc")
            total_images = 0
            if gpc_elem:
                match = re.search(r"Showing \d+ - \d+ of (\d+) images", gpc_elem.text)
                if match:
                    total_images = int(match.group(1))
            
            # 获取缩略图链接
            gdt_elem = soup.select_one("#gdt")
            if not gdt_elem:
                raise Exception("无法找到缩略图容器")
                
            thumb_links = gdt_elem.select("a")
            if thumb_index >= len(thumb_links):
                raise Exception(f"缩略图索引超出范围: {thumb_index} >= {len(thumb_links)}")
            
            # 获取指定缩略图的跳转链接
            target_link = thumb_links[thumb_index]
            image_page_url = target_link.get("href")
            if not image_page_url:
                raise Exception("无法获取图片页面链接")
            
            # 访问图片页面获取大图信息
            image_response = self.session.get(image_page_url)
            image_response.raise_for_status()
            
            image_soup = BeautifulSoup(image_response.content, "html.parser")
            
            # 查找大图元素 (#i3 > a > img)
            img_elem = image_soup.select_one("#i3 img")
            if not img_elem:
                raise Exception("无法找到大图元素")
            
            image_url = img_elem.get("src")
            image_name = img_elem.get("alt", "")
            
            # 从图片URL中提取文件名（如果alt为空）
            if not image_name and image_url:
                # 从URL路径中提取文件名
                url_parts = image_url.split("/")
                if len(url_parts) > 1:
                    # 获取最后部分并解码
                    last_part = url_parts[-1]
                    # 移除可能的查询参数
                    if "?" in last_part:
                        last_part = last_part.split("?")[0]
                    image_name = last_part
            
            if not image_url:
                raise Exception("无法获取大图URL")
            
            return {
                "imageUrl": image_url,
                "imageName": image_name,
                "galleryTitle": gallery_title,
                "currentPage": page,
                "totalPages": total_images,
                "imagePageUrl": image_page_url
            }
            
        except Exception as e:
            self.logger.error(f"获取大图失败: {e}")
            return {
                "error": str(e),
                "imageUrl": "",
                "imageName": "",
                "galleryTitle": "",
                "currentPage": page,
                "totalPages": 0
            }
