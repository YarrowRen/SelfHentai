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
