# 频道配置（从 JSON 加载或硬编码）
CHANNELS = [
    {
        "name": "三立新闻",
        "url": "https://www.youtube.com/@setn/live",
        "description": "台湾新闻频道",
        "logo": "https://yt3.googleusercontent.com/xxx"
    },
    {
        "name": "民视新闻",
        "url": "https://www.youtube.com/@ftv/live",
        "description": "台湾新闻频道",
        "logo": "https://yt3.googleusercontent.com/yyy"
    },
    {
        "name": "BBC News",
        "url": "https://www.youtube.com/@BBCNews/live",
        "description": "英国新闻频道",
        "logo": "https://yt3.googleusercontent.com/zzz"
    }
]

def load_channels_from_json(path: str):
    """从 JSON 文件加载频道配置"""
    import json
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
