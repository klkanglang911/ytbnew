# YouTube 直播代理服务 v1.2.0 - Web 频道管理功能实现计划

## 📋 需求总结

用户需要一个 Web 前端管理界面，支持：
1. **频道录入**：手工添加单个频道（表单方式）
2. **批量导入**：支持粘贴多个 URL 或 M3U 播放列表内容
3. **URL 识别**：自动从 M3U 格式 (`#EXTINF` 行后) 提取 YouTube URL
4. **异步验证**：导入时不阻塞，后台异步验证频道可用性
5. **存储方案**：使用 JSON 文件存储，支持热加载

## 🏗️ 整体架构设计

```
ytb_new/
├── app/
│   ├── api/
│   │   ├── routes.py               # 现有路由（无修改）
│   │   ├── channels_admin.py       # NEW: 频道管理 API
│   │   └── health.py               # 现有（无修改）
│   ├── services/
│   │   ├── channel_manager.py      # NEW: 频道管理业务逻辑
│   │   ├── url_parser.py           # NEW: URL 解析和识别器
│   │   ├── channel_validator.py    # NEW: 异步频道验证
│   │   └── (其他现有文件)
│   ├── templates/
│   │   ├── channels_config.py      # 修改：支持 JSON 加载
│   │   └── channels.json           # NEW: 频道数据存储
│   ├── models.py                   # 修改：添加验证状态模型
│   ├── schemas.py                  # 修改：添加管理相关数据模型
│   └── main.py                     # 修改：挂载管理路由
├── frontend/                        # NEW: React 前端项目
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChannelForm.tsx      # 单个频道添加表单
│   │   │   ├── ChannelList.tsx      # 频道列表展示
│   │   │   ├── BulkImport.tsx       # 批量导入组件
│   │   │   └── ValidationStatus.tsx # 验证状态指示
│   │   ├── pages/
│   │   │   └── ChannelManager.tsx   # 管理页面
│   │   ├── services/
│   │   │   └── api.ts              # API 调用封装
│   │   ├── styles/
│   │   └── App.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
└── docker-compose.yml              # 修改：添加前端构建/服务

```

## 🔄 核心流程

### 1. URL 解析流程
```
输入：URL 或 M3U 内容
  ↓
URLParser.parse_urls()
  ├─ 检测格式（M3U / 单 URL）
  ├─ 提取所有 YouTube URL
  │  └─ 正则匹配：/watch\?v=|/live/|youtube\.com/
  └─ 返回：List[str] (规范化后的 URL)
```

### 2. 频道添加流程
```
前端：ChannelForm 或 BulkImport
  ↓
API: POST /api/admin/channels/import
  ├─ URLParser.parse_urls(raw_input)
  ├─ 去重 + 验证格式
  ├─ 返回预览列表给前端
  └─ 用户确认
  ↓
API: POST /api/admin/channels/confirm-import
  ├─ ChannelValidator.validate_async(urls)
  │  ├─ 后台异步验证（最多 3 个并发）
  │  ├─ 每个频道执行 yt-dlp 测试
  │  └─ 记录验证状态：valid/invalid/unknown
  ├─ ChannelManager.add_channels(channels_data)
  │  ├─ 加载现有 channels.json
  │  ├─ 合并新频道
  │  ├─ 去重处理
  │  └─ 保存到 channels.json
  ├─ 热加载更新内存配置
  └─ 返回最终结果给前端
```

### 3. 验证状态流程
```
后台异步验证任务
  ├─ 通过 WebSocket 或 Server-Sent Events 实时推送状态
  └─ 前端 ValidationStatus 组件显示进度
     ├─ 验证中...
     ├─ 频道名：已验证 ✓
     ├─ 频道名：验证失败 ✗
     └─ 完成：20/25 频道通过
```

## 📁 文件改动详表

### A. 后端改动

#### 1. `app/services/url_parser.py` (NEW - 约 80 行)
```python
class URLParser:
    @staticmethod
    def parse_urls(raw_input: str) -> List[str]:
        """
        识别并提取 URL
        支持格式：
        1. 单行 URL: https://www.youtube.com/watch?v=...
        2. M3U 格式：#EXTINF 行后的 URL
        3. 多行混合

        返回：标准化的 YouTube URL 列表
        """

    @staticmethod
    def extract_m3u_entries(m3u_content: str) -> List[dict]:
        """从 M3U 内容提取频道信息"""

    @staticmethod
    def normalize_youtube_url(url: str) -> Optional[str]:
        """规范化 YouTube URL，支持多种格式"""
```

#### 2. `app/services/channel_validator.py` (NEW - 约 120 行)
```python
class ChannelValidator:
    @staticmethod
    async def validate_channel(channel_url: str) -> ChannelValidationResult:
        """验证单个频道是否可用"""

    @staticmethod
    async def validate_channels_async(
        channels: List[ChannelInfo],
        progress_callback: Optional[Callable] = None
    ) -> List[ChannelValidationResult]:
        """异步验证多个频道，使用 Semaphore 限流"""
```

#### 3. `app/services/channel_manager.py` (NEW - 约 150 行)
```python
class ChannelManager:
    def __init__(self, config_path: str = "app/templates/channels.json"):
        """初始化频道管理器"""

    def load_channels(self) -> List[ChannelInfo]:
        """从 JSON 加载频道"""

    def add_channels(self, channels: List[ChannelInfo]) -> ChannelOperationResult:
        """添加新频道，去重处理"""

    def update_channel(self, name: str, data: dict) -> ChannelOperationResult:
        """更新频道信息"""

    def delete_channel(self, name: str) -> ChannelOperationResult:
        """删除频道"""

    def save_channels(self) -> bool:
        """保存到 JSON 文件"""

    def reload_channels(self) -> bool:
        """热加载频道配置（重新加载内存）"""

    def is_duplicate_url(self, url: str) -> bool:
        """检查 URL 是否已存在"""
```

#### 4. `app/api/channels_admin.py` (NEW - 约 200 行)
```python
router = APIRouter(prefix="/api/admin/channels", tags=["Channel Management"])

@router.post("/import")
async def preview_import(raw_input: str) -> ImportPreviewResponse:
    """
    预览导入结果
    - 解析输入的 URL 或 M3U 内容
    - 去重
    - 返回待导入的频道列表
    """

@router.post("/confirm-import")
async def confirm_import(request: ConfirmImportRequest) -> ImportResultResponse:
    """
    确认导入，异步验证频道
    - 验证所有 URL 的可用性
    - 保存到 channels.json
    - 热加载配置
    """

@router.get("/list")
async def list_channels() -> List[ChannelWithStatusResponse]:
    """获取所有频道及其验证状态"""

@router.put("/{channel_name}")
async def update_channel(channel_name: str, data: ChannelUpdateRequest) -> ChannelResponse:
    """更新单个频道"""

@router.delete("/{channel_name}")
async def delete_channel(channel_name: str) -> DeleteChannelResponse:
    """删除频道"""

@router.get("/validation-status/{task_id}")
async def get_validation_status(task_id: str) -> ValidationStatusResponse:
    """获取异步验证任务的状态"""
```

#### 5. `app/schemas.py` (MODIFY - 添加 ~100 行)
```python
# 导入相关模型
class ChannelInfo(BaseModel):
    name: str
    url: str
    description: Optional[str] = ""
    logo: Optional[str] = None

class ImportPreviewResponse(BaseModel):
    total_count: int
    new_count: int  # 不重复的新频道数
    duplicate_count: int
    channels: List[ChannelInfo]

class ConfirmImportRequest(BaseModel):
    channels: List[ChannelInfo]
    validate: bool = True  # 是否验证

class ChannelValidationResult(BaseModel):
    url: str
    status: str  # valid/invalid/error
    error_message: Optional[str]
    validated_at: str

class ChannelWithStatusResponse(ChannelInfo):
    validation_status: Optional[ChannelValidationResult]
    created_at: Optional[str]
    updated_at: Optional[str]
```

#### 6. `app/templates/channels_config.py` (MODIFY - ~30 行改动)
```python
# 改为支持 JSON 加载
def load_channels_from_json(json_path: str = "app/templates/channels.json"):
    """从 JSON 文件加载频道配置"""
    # 如果 JSON 存在，使用 JSON；否则使用默认列表

CHANNELS = load_channels_from_json()
```

#### 7. `app/models.py` (MODIFY - 添加验证模型)
```python
class ChannelValidation(BaseModel):
    """频道验证记录"""
    channel_name: str
    validation_status: str  # valid/invalid/pending
    validated_at: datetime
    error_message: Optional[str]
```

#### 8. `app/main.py` (MODIFY - ~10 行)
```python
# 挂载新的管理路由
from app.api import channels_admin
app.include_router(channels_admin.router)

# 在启动时初始化 ChannelManager
@app.on_event("startup")
async def startup():
    global channel_manager
    channel_manager = ChannelManager()
```

### B. 前端改动

#### 1. `frontend/src/components/ChannelForm.tsx` (NEW - ~150 行)
单个频道表单：
- 频道名称输入框
- YouTube URL 输入框
- 描述文本区
- 验证状态显示
- 提交/取消按钮

#### 2. `frontend/src/components/BulkImport.tsx` (NEW - ~200 行)
批量导入：
- 文本框（支持粘贴 URL 或 M3U 内容）
- 预览导入列表
- 去重提示
- 导入按钮
- 异步验证进度条

#### 3. `frontend/src/components/ChannelList.tsx` (NEW - ~250 行)
频道列表：
- 表格展示：名称、URL、描述、验证状态、操作
- 编辑/删除按钮
- 搜索/过滤
- 排序

#### 4. `frontend/src/components/ValidationStatus.tsx` (NEW - ~100 行)
验证状态显示：
- 进度条：x/y 频道已验证
- 实时状态列表（WebSocket/SSE）
- 错误日志展示

#### 5. `frontend/src/pages/ChannelManager.tsx` (NEW - ~100 行)
主管理页面：
- 三个标签页：
  1. 批量导入
  2. 手动添加
  3. 频道列表
- 搜索框
- 刷新按钮

#### 6. `frontend/src/services/api.ts` (NEW - ~80 行)
API 调用封装：
```typescript
const api = {
  channels: {
    previewImport(input: string),
    confirmImport(channels: Channel[], validate: boolean),
    list(),
    update(name: string, data: any),
    delete(name: string),
  }
}
```

#### 7. `frontend/vite.config.ts` (NEW)
代理设置，将 `/api` 请求转发到后端

### C. 数据文件

#### 1. `app/templates/channels.json` (NEW - ~80 行)
```json
{
  "channels": [
    {
      "name": "三立新闻",
      "url": "https://www.youtube.com/watch?v=...",
      "description": "三立新闻直播",
      "logo": "https://...",
      "created_at": "2026-02-04T10:00:00Z",
      "updated_at": "2026-02-04T10:00:00Z",
      "validation_status": "valid"
    },
    // ... 其他频道
  ],
  "metadata": {
    "version": "1.0",
    "last_updated": "2026-02-04T10:00:00Z",
    "total_channels": 20
  }
}
```

### D. 配置文件改动

#### 1. `docker-compose.yml` (MODIFY - 添加 Node.js 构建)
```yaml
services:
  # ...
  ytb_frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3001:5173"  # Vite dev server
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - ytb_app
```

#### 2. `frontend/Dockerfile` (NEW)
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]
```

## 🔌 API 端点详细设计

### 1. 预览导入
```
POST /api/admin/channels/import
Content-Type: application/json

{
  "raw_input": "https://www.youtube.com/watch?v=xxx\nhttps://www.youtube.com/watch?v=yyy"
}

响应：
{
  "total_count": 2,
  "new_count": 2,
  "duplicate_count": 0,
  "channels": [
    {
      "name": "未命名频道 1",
      "url": "https://www.youtube.com/watch?v=xxx",
      "description": ""
    },
    // ...
  ]
}
```

### 2. 确认导入（带异步验证）
```
POST /api/admin/channels/confirm-import
Content-Type: application/json

{
  "channels": [
    {
      "name": "新闻频道",
      "url": "https://www.youtube.com/watch?v=xxx",
      "description": "24小时新闻直播",
      "logo": "https://..."
    }
  ],
  "validate": true
}

响应（立即返回）：
{
  "task_id": "import_12345",
  "status": "validating",
  "message": "正在验证频道，请稍候..."
}

后续通过 WebSocket 或轮询获取进度：
GET /api/admin/channels/validation-status/{task_id}

响应：
{
  "task_id": "import_12345",
  "status": "completed",
  "progress": {
    "total": 5,
    "validated": 5,
    "succeeded": 4,
    "failed": 1
  },
  "results": [
    {
      "url": "https://...",
      "status": "valid",
      "validated_at": "2026-02-04T10:05:00Z"
    }
  ]
}
```

### 3. 获取频道列表
```
GET /api/admin/channels/list

响应：
{
  "channels": [
    {
      "name": "三立新闻",
      "url": "https://...",
      "description": "...",
      "validation_status": {
        "status": "valid",
        "validated_at": "2026-02-04T10:00:00Z"
      }
    }
  ],
  "total": 20
}
```

## 📊 数据模型关系

```
Channel
├── name: str (唯一)
├── url: str (YouTube URL)
├── description: str
├── logo: str (可选)
├── created_at: datetime
├── updated_at: datetime
└── validation_status: ChannelValidationResult
    ├── status: "valid" | "invalid" | "pending"
    ├── error_message: str (可选)
    └── validated_at: datetime
```

## 🔐 安全考虑

1. **API 密钥认证**（可选，v1.2 先不实现）：
   - 简单 API Key 验证
   - 仅限管理员访问

2. **输入验证**：
   - 严格的 URL 格式检查
   - 频道名称长度限制
   - 防止注入攻击

3. **操作日志**：
   - 记录所有频道添加/删除操作
   - 便于审计

## 🚀 实现阶段

### Phase 1: 后端核心功能（优先级 HIGH）
- [ ] 实现 `URLParser` 类
- [ ] 实现 `ChannelValidator` 类
- [ ] 实现 `ChannelManager` 类
- [ ] 创建 `channels_admin.py` API 路由
- [ ] 创建 `channels.json` 模板

### Phase 2: 前端 UI（优先级 HIGH）
- [ ] 搭建 React + Vite 项目结构
- [ ] 实现 `BulkImport` 组件
- [ ] 实现 `ChannelForm` 组件
- [ ] 实现 `ChannelList` 组件
- [ ] 实现 `ChannelManager` 页面

### Phase 3: 集成与测试（优先级 MEDIUM）
- [ ] 前后端联调
- [ ] 单元测试
- [ ] 集成测试
- [ ] WebSocket 实时验证状态

### Phase 4: 部署与优化（优先级 MEDIUM）
- [ ] Docker 构建配置
- [ ] 性能优化
- [ ] 错误处理和恢复
- [ ] 文档编写

## 📝 关键技术细节

### URL 解析规则
```python
# 支持的 YouTube URL 格式
1. https://www.youtube.com/watch?v=<video_id>
2. https://www.youtube.com/live/<video_id>
3. https://youtube.com/watch?v=<video_id>
4. https://youtu.be/<video_id>
5. 从 M3U 的 #EXTINF 行后提取

# M3U 样本
#EXTINF:-1 tvg-id="..." tvg-name="..." group-title="...",频道名
https://www.youtube.com/watch?v=<video_id>
```

### 异步验证流程
```python
# 使用 asyncio.Semaphore 限制并发
semaphore = asyncio.Semaphore(3)

async def validate_with_limit(url):
    async with semaphore:
        return await validate_single_url(url)

# 批量验证
tasks = [validate_with_limit(url) for url in urls]
results = await asyncio.gather(*tasks)
```

### JSON 热加载机制
```python
# 在 FastAPI startup 事件中加载
# 后续通过 ChannelManager.reload_channels() 重新加载
# 避免需要重启应用
```

## 🔍 测试计划

### 后端测试
- [ ] URL 解析测试（各种格式）
- [ ] M3U 提取测试
- [ ] 频道验证测试（模拟 yt-dlp）
- [ ] JSON 加载/保存测试
- [ ] 去重逻辑测试
- [ ] API 端点测试

### 前端测试
- [ ] 组件渲染测试
- [ ] 表单提交测试
- [ ] API 调用测试（Mock）
- [ ] 验证进度显示测试

## 📈 性能目标

- URL 解析：< 100ms（适用于 1000 个 URL）
- 单个频道验证：~30-60s（yt-dlp 耗时）
- 批量导入（10 个频道）：~5-10 分钟（并发 3 个）
- JSON 加载：< 50ms
- 前端响应：< 100ms

## 🎯 成功标准

- ✅ 支持粘贴多个 URL 进行批量导入
- ✅ 支持粘贴 M3U 内容并自动识别 URL
- ✅ 支持单个频道手工添加
- ✅ 异步验证频道可用性，不阻塞 UI
- ✅ 频道数据保存到 JSON 文件
- ✅ 支持频道编辑和删除
- ✅ Web UI 美观易用
- ✅ 所有验证状态实时显示

## 📚 版本信息

- **目标版本**: v1.2.0
- **当前版本**: v1.1.0
- **新增功能数**: 5（URL 解析、批量导入、手动添加、异步验证、Web 管理）
- **修改文件数**: 8
- **新增文件数**: 12+

---

**制定日期**: 2026-02-04
**计划作者**: Claude Code
**审核状态**: 待用户批准
