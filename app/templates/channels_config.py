# 频道配置（从 YouTube M3U 导入）
import json
import os
from typing import List, Optional

# 默认频道列表（JSON 未找到时使用）
DEFAULT_CHANNELS = [
    # 台湾新闻直播
    {
        "name": "三立新闻",
        "url": "https://www.youtube.com/watch?v=QsGswQvRmtU",
        "description": "台湾新闻 24hr 直播",
        "logo": "https://yt3.googleusercontent.com/xxx"
    },
    {
        "name": "民视新闻",
        "url": "https://www.youtube.com/watch?v=ylYJSBUgaMA",
        "description": "民视新闻24小时直播",
        "logo": "https://yt3.googleusercontent.com/yyy"
    },
    {
        "name": "台视新闻",
        "url": "https://www.youtube.com/watch?v=xL0ch83RAK8",
        "description": "台视新闻台HD 24小时线上直播",
        "logo": "https://yt3.googleusercontent.com/zzz"
    },
    {
        "name": "华视新闻",
        "url": "https://www.youtube.com/watch?v=wM0g8EoUZ_E",
        "description": "华视新闻直播",
        "logo": ""
    },
    {
        "name": "中视新闻",
        "url": "https://www.youtube.com/watch?v=TCnaIE_SAtM",
        "description": "中视新闻LIVE直播频道",
        "logo": ""
    },
    {
        "name": "TVBS新闻",
        "url": "https://www.youtube.com/watch?v=m_dhMSvUCIc",
        "description": "TVBS NEWS网路独家新闻24小时直播",
        "logo": ""
    },
    {
        "name": "东森新闻",
        "url": "https://www.youtube.com/watch?v=V1p33hqPrUk",
        "description": "东森新闻 51 频道 24 小时直播",
        "logo": ""
    },
    {
        "name": "东森财经新闻",
        "url": "https://www.youtube.com/watch?v=1I2iq41Akmo",
        "description": "EBC 东森财经新闻24小时线上直播",
        "logo": ""
    },
    {
        "name": "中天新闻",
        "url": "https://www.youtube.com/watch?v=vr3XyVCR4T0",
        "description": "中天新闻24小时HD新闻直播",
        "logo": ""
    },
    {
        "name": "寰宇新闻",
        "url": "https://www.youtube.com/watch?v=6IquAgfvYmc",
        "description": "寰宇新闻24小时线上直播",
        "logo": ""
    },
    {
        "name": "公视新闻",
        "url": "https://www.youtube.com/watch?v=quwqlazU-c8",
        "description": "公视新闻 PTS News 24小时线上直播",
        "logo": ""
    },
    {
        "name": "鏡新闻",
        "url": "https://www.youtube.com/watch?v=5n0y6b0Q25o",
        "description": "镜新闻 线上看 24小时 新闻直播",
        "logo": ""
    },
    {
        "name": "大愛一臺",
        "url": "https://www.youtube.com/watch?v=oV_i3Hsl_zg",
        "description": "大爱一台HD Live 台湾直播",
        "logo": ""
    },
    {
        "name": "大愛二臺",
        "url": "https://www.youtube.com/watch?v=OKvWtVoDR8I",
        "description": "大爱二台HD Live 台湾直播",
        "logo": ""
    },
    {
        "name": "公视台语台",
        "url": "https://www.youtube.com/watch?v=6KlRR_DGhmI",
        "description": "公视台语台网路直播",
        "logo": ""
    },
    {
        "name": "国会频道1",
        "url": "https://www.youtube.com/watch?v=4HysYHJ6GkY",
        "description": "国会频道-立法院议事转播",
        "logo": ""
    },
    {
        "name": "寰宇新闻财经台",
        "url": "https://www.youtube.com/watch?v=7G62ua4RruQ",
        "description": "寰宇新闻财经台 24小时线上直播",
        "logo": ""
    },
    {
        "name": "寰宇新闻台湾台",
        "url": "https://www.youtube.com/watch?v=w87VGpgd90U",
        "description": "寰宇新闻台湾台 24小时直播",
        "logo": ""
    },
    {
        "name": "BBC News",
        "url": "https://www.youtube.com/watch?v=uRXcvMoJrWw",
        "description": "BBC News 24/7",
        "logo": ""
    },
    {
        "name": "CCTV 中文国际亚洲",
        "url": "https://www.youtube.com/watch?v=7j92Myu2wzg",
        "description": "CCTV中文国际 亚洲 24小时直播",
        "logo": ""
    },
]


def load_channels_from_json(json_path: str = "app/templates/channels.json") -> List[dict]:
    """
    从 JSON 文件加载频道配置。

    如果 JSON 文件存在，优先使用 JSON；否则使用默认频道列表。

    Args:
        json_path: JSON 配置文件路径

    Returns:
        频道列表
    """
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                channels = config.get('channels', DEFAULT_CHANNELS)
                return channels
        except Exception:
            # JSON 解析失败，使用默认列表
            return DEFAULT_CHANNELS

    return DEFAULT_CHANNELS


# 初始化频道列表（优先使用 JSON）
CHANNELS = load_channels_from_json()

