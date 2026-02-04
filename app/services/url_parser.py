"""
YouTube URL 解析器

支持多种格式：
1. 单行 URL: https://www.youtube.com/watch?v=ENnjj7jQ23g
2. M3U 播放列表格式
3. 多行混合格式
"""

import re
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs


class URLParser:
    """YouTube URL 解析和识别器"""

    # YouTube URL 正则表达式集合
    YOUTUBE_PATTERNS = [
        # watch?v= 格式
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        # /live/ 格式
        r'(?:https?://)?(?:www\.)?youtube\.com/live/([a-zA-Z0-9_-]{11})',
        # youtu.be 格式
        r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
        # youtube.com/live?v= 格式
        r'(?:https?://)?(?:www\.)?youtube\.com/live\?v=([a-zA-Z0-9_-]{11})',
        # 只要 URL 中含有 watch 或 live 的都尝试匹配
        r'(?:https?://)?(?:www\.)?youtube\.com/(?:watch|live)[?&]v=([a-zA-Z0-9_-]{11})',
    ]

    @staticmethod
    def parse_urls(raw_input: str) -> List[str]:
        """
        从原始输入中解析并提取 YouTube URL。

        支持：
        1. 单行 URL
        2. 多行 URL（每行一个）
        3. M3U 播放列表格式
        4. 混合格式

        Args:
            raw_input: 原始输入字符串

        Returns:
            标准化后的 YouTube URL 列表（去重）
        """
        if not raw_input or not isinstance(raw_input, str):
            return []

        raw_input = raw_input.strip()

        # 检测是否是 M3U 格式
        if '#EXTINF' in raw_input or '#EXT' in raw_input:
            return URLParser._parse_m3u_content(raw_input)
        else:
            return URLParser._parse_raw_urls(raw_input)

    @staticmethod
    def _parse_m3u_content(m3u_content: str) -> List[str]:
        """
        从 M3U 播放列表内容中提取 YouTube URL。

        M3U 格式示例：
        #EXTINF:-1 tvg-id="1" tvg-name="频道名" group-title="分组",频道名
        https://www.youtube.com/watch?v=ENnjj7jQ23g

        Args:
            m3u_content: M3U 播放列表内容

        Returns:
            YouTube URL 列表
        """
        urls = []
        lines = m3u_content.split('\n')

        for i, line in enumerate(lines):
            line = line.strip()

            # 跳过空行和注释行
            if not line or line.startswith('#'):
                continue

            # 检查是否是 URL
            url = URLParser._extract_url_from_line(line)
            if url:
                urls.append(url)

        return URLParser._deduplicate_urls(urls)

    @staticmethod
    def _parse_raw_urls(raw_input: str) -> List[str]:
        """
        从原始文本中解析 YouTube URL。

        支持：
        1. 每行一个 URL
        2. 用逗号、空格分隔的 URL
        3. 混合格式

        Args:
            raw_input: 原始输入字符串

        Returns:
            YouTube URL 列表
        """
        urls = []

        # 按不同的分隔符分割
        # 先按换行符分割
        lines = raw_input.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 再按逗号分割（处理单行多个 URL 的情况）
            for segment in line.split(','):
                segment = segment.strip()
                if not segment:
                    continue

                # 尝试从单个文本段中提取 URL
                url = URLParser._extract_url_from_line(segment)
                if url:
                    urls.append(url)

        return URLParser._deduplicate_urls(urls)

    @staticmethod
    def _extract_url_from_line(line: str) -> Optional[str]:
        """
        从一行文本中提取 YouTube URL。

        Args:
            line: 单行文本

        Returns:
            规范化的 YouTube URL，如果没有找到则返回 None
        """
        line = line.strip()

        # 逐个尝试正则表达式
        for pattern in URLParser.YOUTUBE_PATTERNS:
            match = re.search(pattern, line)
            if match:
                video_id = match.group(1)
                return f"https://www.youtube.com/watch?v={video_id}"

        return None

    @staticmethod
    def _deduplicate_urls(urls: List[str]) -> List[str]:
        """
        对 URL 列表进行去重。

        Args:
            urls: URL 列表

        Returns:
            去重后的 URL 列表（保留顺序）
        """
        seen = set()
        result = []

        for url in urls:
            # 规范化 URL 进行比较
            normalized = URLParser.normalize_youtube_url(url)
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(normalized)

        return result

    @staticmethod
    def normalize_youtube_url(url: str) -> Optional[str]:
        """
        规范化 YouTube URL。

        将各种格式的 YouTube URL 转换为标准格式：
        https://www.youtube.com/watch?v=<video_id>

        支持的输入格式：
        1. https://www.youtube.com/watch?v=ENnjj7jQ23g
        2. https://www.youtube.com/live/ENnjj7jQ23g
        3. https://youtu.be/ENnjj7jQ23g
        4. https://youtube.com/watch?v=ENnjj7jQ23g
        5. 其他变体

        Args:
            url: 任意格式的 YouTube URL

        Returns:
            规范化后的 URL，如果不是有效的 YouTube URL 则返回 None
        """
        if not url:
            return None

        url = url.strip()

        # 尝试从 URL 中提取视频 ID
        video_id = URLParser._extract_video_id(url)
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"

        return None

    @staticmethod
    def _extract_video_id(url: str) -> Optional[str]:
        """
        从任意格式的 YouTube URL 中提取视频 ID。

        Args:
            url: YouTube URL

        Returns:
            11 字符的视频 ID，如果不是有效的 YouTube URL 则返回 None
        """
        # 逐个尝试正则表达式
        for pattern in URLParser.YOUTUBE_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    @staticmethod
    def extract_m3u_entries(m3u_content: str) -> List[Dict[str, str]]:
        """
        从 M3U 播放列表内容中提取频道信息。

        M3U 格式：
        #EXTINF:-1 tvg-id="1" tvg-name="频道名" tvg-logo="logo_url" group-title="分组",显示名
        https://www.youtube.com/watch?v=ENnjj7jQ23g

        Args:
            m3u_content: M3U 播放列表内容

        Returns:
            频道信息列表，每个条目包含：
            {
                'extinf_line': '#EXTINF 行',
                'name': '频道名',
                'url': 'YouTube URL',
                'logo': 'Logo URL',
                'group_title': '分组',
                'tvg_id': 'TV ID',
                'tvg_name': 'TV 名称'
            }
        """
        entries = []
        lines = m3u_content.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 查找 #EXTINF 行
            if line.startswith('#EXTINF'):
                extinf_line = line
                entry_info = URLParser._parse_extinf_line(extinf_line)

                # 下一行应该是 URL
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    url = URLParser._extract_url_from_line(next_line)

                    if url:
                        entry_info['url'] = url
                        entry_info['extinf_line'] = extinf_line
                        entries.append(entry_info)

                    i += 2
                else:
                    i += 1
            else:
                i += 1

        return entries

    @staticmethod
    def _parse_extinf_line(extinf_line: str) -> Dict[str, str]:
        """
        解析 #EXTINF 行获取频道元数据。

        Args:
            extinf_line: #EXTINF 行

        Returns:
            频道元数据字典
        """
        info = {
            'name': '未命名频道',
            'logo': '',
            'group_title': '',
            'tvg_id': '',
            'tvg_name': '',
        }

        # 提取 tvg-name
        tvg_name_match = re.search(r'tvg-name="([^"]*)"', extinf_line)
        if tvg_name_match:
            info['tvg_name'] = tvg_name_match.group(1)
            info['name'] = tvg_name_match.group(1)

        # 提取 tvg-logo
        tvg_logo_match = re.search(r'tvg-logo="([^"]*)"', extinf_line)
        if tvg_logo_match:
            info['logo'] = tvg_logo_match.group(1)

        # 提取 group-title
        group_title_match = re.search(r'group-title="([^"]*)"', extinf_line)
        if group_title_match:
            info['group_title'] = group_title_match.group(1)

        # 提取 tvg-id
        tvg_id_match = re.search(r'tvg-id="([^"]*)"', extinf_line)
        if tvg_id_match:
            info['tvg_id'] = tvg_id_match.group(1)

        # 提取逗号后的显示名称（如果 tvg-name 为空）
        comma_parts = extinf_line.split(',')
        if len(comma_parts) > 1:
            display_name = comma_parts[-1].strip()
            if display_name and not info['name']:
                info['name'] = display_name
            elif display_name and info['tvg_name'] == display_name:
                # 如果逗号后的名称和 tvg-name 相同，使用该名称
                info['name'] = display_name

        return info


# 简便函数
def parse_youtube_urls(raw_input: str) -> List[str]:
    """便利函数：直接解析 URL"""
    return URLParser.parse_urls(raw_input)


def extract_m3u_entries(m3u_content: str) -> List[Dict[str, str]]:
    """便利函数：从 M3U 内容提取频道"""
    return URLParser.extract_m3u_entries(m3u_content)
