# A-Share Local Lab

本项目是一个面向 A 股研究场景的本地工作台，集成了 AI 选股、实时盯盘、固定历史回看、自选股管理、热点快报与纸交易模拟盘。整套系统默认面向本地单机运行，不依赖云服务器，打开网页即可在一个界面里完成“看市场、看个股、看候选、做模拟”的完整闭环。

当前版本重点强化了三件事：

- 更像看盘软件的桌面化体验：左侧导航切页，右侧固定历史回看，大图模式、周期切换、缩放和搜索联动都集中在同一块区域
- 更稳的数据回退链路：实时行情优先，失败时回退到最近收盘；历史拉取失败时，回退到本地缓存或最新快照，避免页面直接失效
- 更完整的本地研究流程：从模型候选股、实时盯盘、自选股票，到本地模拟买卖、持仓统计、交易记录，形成连续工作流

技术栈以 `FastAPI + LightGBM + AKShare + easyquotation + 原生前端` 为主，适合继续扩展成更完整的本地量化研究平台。

## 功能概览

- 首页概览：模型摘要、刷新状态、市场概览、上证指数分时、美股上一交易日行业表现
- 模型候选股：未来 5 日收益预测、推荐原因、依据拆解、风险提示、置信度展示
- 实时盯盘：实时快照优先，失败时回退到最近收盘，适合盘中快速筛看
- 自选股票：本地持久化、搜索添加、快速查看、快速模拟买入、删除管理
- 历史回看：固定右侧展示，支持日 / 周 / 月 / 季 / 年 / 1分 / 5分 / 15分 / 30分 / 60分 / 5日
- 图表交互：鼠标悬停提示、K 线与分时切换、单日下钻、缩放、大图模式
- 模拟盘：本地账户、下单、持仓、成交、费用参数、导入导出、收益快照
- 热点快报：多源聚合、分类筛选、滚动加载、AI 摘要
- 条件选股 / 行业轮动 / 盘前盘后 / 事件时间线 / 预警通知：作为研究辅助页面持续扩展

## 目录结构

```text
Agu/
├─ app/                    # FastAPI 入口与服务层
├─ frontend/               # 前端静态资源
├─ scripts/                # 训练、刷新等脚本
├─ data/                   # 本地数据、状态、缓存、模拟盘持久化
├─ models/                 # 训练产出的模型文件
├─ requirements.txt        # Python 依赖
├─ start.ps1               # Windows 本地启动脚本
└─ README.md
```

## 环境要求

- Windows PowerShell
- Python 3.11 及以上
- 可访问外网的数据抓取环境

## 快速启动

```powershell
cd D:\Projects\codex\Agu
.\start.ps1
```

启动脚本会自动：

1. 创建 `.venv`
2. 安装 `requirements.txt`
3. 清理当前项目旧的 uvicorn 进程
4. 在 `8000 / 8001 / 8002 / 8010` 中寻找空闲端口
5. 启动 `uvicorn app.main:app`

启动成功后，访问：

- [http://127.0.0.1:8000](http://127.0.0.1:8000)

如果 `8000` 被占用，脚本会自动切换到其他端口，并在终端打印最终地址。

## 手动运行

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## 配置说明

### 当前实际配置来源

当前项目还没有正式接入 `.env` 读取逻辑。大多数路径与运行文件名都直接定义在：

- `app/core/config.py`

也就是说，当前运行时的主要配置是“代码常量配置”，不是“环境变量配置”。

### 推荐补充的 `.env.example`

虽然当前代码未读取 `.env`，但建议先在本地按下面模板准备，便于后续接线：

```dotenv
# App
AGU_HOST=127.0.0.1
AGU_PORT=8000
AGU_SOURCE=real
AGU_POOL=hs300

# Data paths
AGU_DATA_DIR=./data
AGU_MODELS_DIR=./models
AGU_REAL_DATA_PATH=./data/a_share_prices.csv
AGU_SAMPLE_DATA_PATH=./data/sample_prices.csv

# Runtime behavior
AGU_ENABLE_RELOAD=true
AGU_REFRESH_PORT_CANDIDATES=8000,8001,8002,8010

# Fetch/cache
AGU_HOT_NEWS_TTL_SECONDS=120
AGU_MARKET_CACHE_TTL_SECONDS=1800
```

### 当前可调整项

在不改业务代码的前提下，当前真正可调整的只有：

- `start.ps1` 中的启动端口候选顺序
- `app/core/config.py` 中的数据与模型路径常量
- 手动替换 `data/` 与 `models/` 下的文件

## 运行产物说明

项目运行后，常见产物会写入以下位置：

- `models/stock_ranker.pkl`
  - 训练产出的默认模型文件
- `data/a_share_prices.csv`
  - 本地真实 A 股历史数据
- `data/sample_prices.csv`
  - 样例数据
- `data/custom_watchlist.json`
  - 本地自选股列表
- `data/paper_portfolio.json`
  - 模拟盘账户、持仓、成交与设置
- `data/status/refresh_status.json`
  - 后台刷新任务状态
- `data/status/refresh.log`
  - 后台刷新日志
- `data/status/model_meta.json`
  - 模型训练历史与摘要信息
- `data/status/data_health.json`
  - 数据健康检查结果
- `data/status/dataset_meta.json`
  - 数据集元信息
- `data/status/market_overview_cache.json`
  - 市场概览缓存
- `data/status/hot_news_cache.json`
  - 热点快报缓存
- `data/status/stock_catalog_cache.json`
  - 股票目录缓存
- `data/status/cache/history/`
  - 历史回看相关缓存

## 测试与验证

### 当前现状

当前仓库内没有正式的自动化测试目录，也没有稳定的 `pytest` 用例。

因此目前更接近“手工验证 + 脚本验证”的工程状态。

### 建议的最小验证流程

安装依赖后，至少执行以下检查：

```powershell
.venv\Scripts\python.exe -m compileall app scripts
.venv\Scripts\python.exe scripts\train.py
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

然后手工验证：

1. 打开首页，确认静态资源正常加载
2. 检查 `/api/health` 返回 `{"status":"ok"}`
3. 检查候选股、历史回看、自选股、模拟盘接口是否可访问
4. 在页面上执行一次搜索、一次历史切换、一次模拟买入

### 后续建议补的测试

- `pytest` 基础用例
- FastAPI `TestClient` API 测试
- 数据服务层的离线单元测试
- 前端最小链路冒烟测试

## 常用命令

### 启动服务

```powershell
.\start.ps1
```

### 手动训练模型

```powershell
.venv\Scripts\python.exe scripts\train.py
```

### 刷新真实数据并重训

```powershell
.venv\Scripts\python.exe scripts\refresh_real_data.py --pool hs300
```

### 语法编译检查

```powershell
.venv\Scripts\python.exe -m compileall app scripts
```

## 常用接口

- `GET /api/health`
- `GET /api/overview`
- `GET /api/model-history`
- `GET /api/data-health`
- `GET /api/market-overview`
- `GET /api/hot-news`
- `GET /api/picks`
- `GET /api/watchlist`
- `GET /api/history/{symbol}`
- `GET /api/watch-intraday/{symbol}`
- `GET /api/search`
- `GET /api/favorites`
- `GET /api/portfolio`
- `GET /api/portfolio/export`
- `POST /api/portfolio/import`
- `POST /api/portfolio/orders`
- `POST /api/portfolio/reset`
- `POST /api/train`
- `POST /api/refresh-real-data`
- `GET /api/refresh-real-data/status`

## requirements.txt 说明

当前 `requirements.txt` 主要覆盖：

- Web 服务：`fastapi`, `uvicorn[standard]`, `python-multipart`
- 数据处理：`pandas`, `numpy`
- 建模：`scikit-learn`, `lightgbm`
- 数据源：`akshare`, `easyquotation`

如果后续补自动化测试，建议新增：

- `pytest`
- `httpx`

## 当前限制

- 目前不是自动交易系统，只是本地分析与模拟盘工具
- 当前配置未环境变量化，部署可移植性一般
- 训练、抓取、缓存、前端运行仍高度依赖本地目录结构
- 缺少正式自动化测试、CI 与发布流程
- 多数据源之间仍可能存在口径差异
- 热点快报与市场概览依赖外部源，可能出现限流、超时或回退缓存
- 启动脚本主要面向 Windows PowerShell

## 后续建议

- 正式新增 `.env.example` 文件，并在 `app/core/config.py` 中接入环境变量解析
- 为 `data/` 与 `models/` 做更清晰的初始化与迁移说明
- 补 `pytest + TestClient` 的 API 冒烟测试
- 增加本地开发模式与生产模式的配置区分
- 给 `start.ps1` 增加可选参数，例如 `-Port`、`-NoInstall`、`-Reload`
- 将运行产物与缓存目录做更细粒度忽略与备份策略

## 仅文档说明

本 README 里的 `.env.example` 内容当前是“建议模板”，不是现有代码已经接入的配置机制。若要真正生效，仍需后续把环境变量读取逻辑接入到配置层。
