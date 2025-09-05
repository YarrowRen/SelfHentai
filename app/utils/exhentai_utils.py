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

    def fetch_gallery_metadatas(self, favorites: list):
        """
        批量请求收藏本子的元数据（每批最多 25 条）

        参数:
            favorites: List[dict]，包含 'gid' 和 'token'

        返回:
            List[dict]，每个本子的元数据
        """
        url = "https://api.e-hentai.org/api.php"
        all_metadata = []

        for i in range(0, len(favorites), 25):
            batch = favorites[i : i + 25]
            gidlist = [[int(f["gid"]), f["token"]] for f in batch]

            payload = {"method": "gdata", "gidlist": gidlist, "namespace": 1}
            self.logger.info(f"正在请求第 {i // 25 + 1} 批，共 {len(batch)} 条数据...")
            try:
                res = requests.post(url, json=payload)
                res.raise_for_status()
                data = res.json().get("gmetadata", [])
                all_metadata.extend(data)
            except Exception:
                self.logger.exception("请求失败")

        return all_metadata

    def get_favorites_metadata(self):
        """
        高层封装：从收藏夹获取所有本子元数据。
        """
        favorites = self.extract_favorites()
        return self.fetch_gallery_metadatas(favorites)

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
