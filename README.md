# A-Share Local Lab

一个本地运行的 A 股 AI 选股与盯盘工作台，使用 `FastAPI + LightGBM + 原生前端页面` 构建。

它的目标不是做自动交易，而是把下面几件事放到一个本地网页里统一完成：

- A 股历史数据准备
- 因子构建与模型训练
- 候选股打分与推荐原因展示
- 实时盯盘与自选股管理
- 单股历史回看与多周期图表查看
- 首页市场概览与热点快报聚合

当前项目适合本地研究、演示、模拟观察，不需要部署到服务器，也不依赖数据库。

## 当前版本功能

### 1. 左侧导航式本地工作台

当前页面已经拆成几个固定工作页：

- `首页`
  - 模型概览卡片
  - 上证指数当日分时图
  - 上一交易日纳指涨跌
  - 美股上一交易日领涨行业
  - 后台刷新任务状态
- `模型候选股`
  - 展示模型当前推荐股票
  - 每只股票带推荐摘要、推荐原因、预测依据、风险提示
- `实时盯盘`
  - 查看候选股实时快照
  - 非交易时段回看最近交易日收盘状态
- `自选股票`
  - 从搜索结果添加自选
  - 本地持久化保存
- `热点快报`
  - 聚合同花顺、东方财富、财联社、新浪财经快讯
  - 支持分类筛选
  - 支持向下滚动继续加载

### 2. 右侧固定历史回看

右侧历史区会常驻显示一个图表区：

- 未选择股票时默认展示 `上证指数`
- 点击候选股、盯盘股、自选股、搜索结果里的 `查看`，都可以切换右侧历史回看
- 支持周期：
  - `日`
  - `周`
  - `月`
  - `季`
  - `年`
  - `1分`
  - `5分`
  - `15分`
  - `30分`
  - `60分`
  - `5日`
- 支持：
  - 鼠标悬停查看某时刻价格与涨跌幅
  - 图表缩放
  - 大图模式
  - 从日线切到某一交易日的当日涨跌图后再返回 K 线

### 3. 股票搜索与自选

右侧顶部支持搜索股票代码或名称，例如：

- `600519`
- `300750`
- `茅台`
- `宁德`

搜索结果支持：

- `查看`
  - 切换右侧历史回看
- `添加自选`
  - 加入左侧 `自选股票`

### 4. 模型推荐解释

候选股页面不是只给一个排序结果，还会给出解释：

- 推荐摘要
- 推荐原因
- 预测依据
- 模型提示

当前解释逻辑基于模型特征贡献生成，便于快速看懂“为什么推荐这只票”。

### 5. 市场概览

首页当前包含这些市场模块：

- `上证指数当日分时图`
  - 展示开盘价、当前价、涨跌额、涨跌幅
- `纳斯达克上一交易日涨跌`
- `美股上一交易日领涨行业`
  - 当前口径来自同花顺美股涨幅榜分页 + 同花顺公司概况页所属行业聚合

### 6. 热点快报

热点快报页当前支持：

- 多源聚合
  - 同花顺
  - 东方财富
  - 财联社
  - 新浪财经
- AI 简要归纳
  - 如 `利好半导体`
  - `利好商业航天`
  - `利空黄金原油`
- 分类过滤
  - `全部`
  - `科技`
  - `金融`
  - `新能源`
  - `医药`
  - `地产基建`
  - `资源`
- 滚动到底继续加载

## 技术栈

- `FastAPI`
- `Uvicorn`
- `Pandas`
- `NumPy`
- `scikit-learn`
- `LightGBM`
- `AKShare`
- `easyquotation`
- 原生 `HTML / CSS / JavaScript`

## 数据来源

### A 股历史数据

主要用于训练、打分、历史回看：

- `AKShare`

### A 股实时快照

主要用于实时盯盘：

- `easyquotation`

### 首页市场概览

- 上证指数分时：`AKShare`
- 纳指上一交易日：`AKShare`
- 美股领涨行业：`同花顺美股涨幅榜 + 同花顺公司概况页行业字段聚合`

### 热点快报

- `同花顺`
- `东方财富`
- `财联社`
- `新浪财经`

## 模型说明

当前模型是一个本地可跑的基础选股模型，流程如下：

`历史价格 -> 特征构建 -> LightGBM 回归 -> 预测未来 5 日收益 -> 排序`

当前基础因子包括：

- `ret_5`
- `ret_10`
- `volatility_10`
- `price_vs_ma10`
- `price_vs_ma20`
- `volume_ratio_5`

模型输出的是：

- 每只股票的 `predicted_return_5`
- 推荐解释与因子贡献摘要

这套模型更偏研究与演示用途，适合做本地观察，不应直接当作实盘投资建议。

## 股票池

当前支持的股票池：

- `hs300`
- `zz500`

后台真实数据刷新脚本会从对应指数成分股中抓取数据，再训练和打分。

## 项目结构

```text
Agu/
├─ app/
│  ├─ core/                   # 配置
│  ├─ services/               # 数据、模型、盯盘、市场概览、热点快报
│  └─ main.py                 # FastAPI 入口
├─ frontend/                  # 本地前端页面
├─ scripts/
│  ├─ train.py                # 使用本地已有数据训练模型
│  └─ refresh_real_data.py    # 抓取真实数据并重新训练
├─ data/
├─ models/
├─ requirements.txt
├─ start.ps1
└─ README.md
```

## 快速开始

### 一键启动

```powershell
cd D:\Projects\codex\Agu
.\start.ps1
```

这个脚本会自动：

- 创建虚拟环境
- 安装依赖
- 清理旧的项目 uvicorn 进程
- 自动选择可用端口
- 启动本地服务

启动后打开：

- [http://127.0.0.1:8000](http://127.0.0.1:8000)

如果 `8000` 被占用，脚本会顺延尝试 `8001 / 8002 / 8010`。

### 手动启动

```powershell
cd D:\Projects\codex\Agu
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## 常用脚本

### 1. 使用本地已有数据重新训练

```powershell
cd D:\Projects\codex\Agu
.venv\Scripts\python scripts\train.py
```

说明：

- 如果 `data/a_share_prices.csv` 存在，就使用真实数据训练
- 否则使用示例数据训练
- 这个脚本不会主动远程抓取数据

### 2. 刷新真实 A 股数据并训练

```powershell
cd D:\Projects\codex\Agu
.venv\Scripts\python scripts\refresh_real_data.py --pool hs300
```

可选参数：

- `--pool hs300`
- `--pool zz500`
- `--start-date 2023-01-01`
- `--workers 6`

这个脚本会：

- 读取股票池成分股
- 抓取历史数据
- 生成训练特征
- 训练模型
- 更新本地模型文件与真实数据文件

## 页面按钮说明

### 首页

- `刷新候选股`
  - 重新加载当前模型打分结果
- `重新训练模型`
  - 使用当前本地数据重新训练
- `后台刷新真实数据`
  - 启动后台刷新脚本抓取真实数据并重新训练
- `刷新盯盘快照`
  - 重新拉取盯盘数据

### 候选股 / 盯盘 / 自选 / 搜索

- `查看`
  - 切换右侧历史回看
- `添加自选`
  - 加入自选股票页

### 热点快报

- `刷新快报`
  - 重新抓取热点快报
- 分类按钮
  - 切换不同主题快报

## API 概览

### 基础

- `GET /api/health`
- `GET /api/overview`
- `GET /api/picks`

### 历史与盯盘

- `GET /api/watchlist`
- `GET /api/watch-history/{symbol}`
- `GET /api/history/{symbol}`
- `GET /api/chart-history/{symbol}`
- `GET /api/watch-intraday/{symbol}`

### 搜索与自选

- `GET /api/search`
- `GET /api/favorites`
- `POST /api/favorites`
- `DELETE /api/favorites/{symbol}`

### 模型与数据刷新

- `POST /api/train`
- `POST /api/refresh-real-data`
- `GET /api/refresh-real-data/status`

### 市场概览与热点

- `GET /api/market-overview`
- `GET /api/hot-news`

## 开源依赖说明

当前仓库没有直接复制第三方项目整段业务源码，主要是基于公开库与公开页面能力做集成。

本项目当前明确使用了这些开源项目或服务能力：

- `AKShare`
  - 用途：A 股历史数据、指数分时、纳指上一交易日数据、财经快讯数据接口等
  - 仓库：[akfamily/akshare](https://github.com/akfamily/akshare)
- `easyquotation`
  - 用途：A 股实时行情快照
  - 仓库：[shidenggui/easyquotation](https://github.com/shidenggui/easyquotation)
- `LightGBM`
  - 用途：本地选股排序模型
  - 仓库：[microsoft/LightGBM](https://github.com/microsoft/LightGBM)
- `FastAPI`
  - 用途：本地 Web API 和页面服务
  - 仓库：[fastapi/fastapi](https://github.com/fastapi/fastapi)

额外说明：

- 首页 `美股上一交易日领涨行业` 当前使用的是同花顺页面聚合口径，不是券商终端数据口径
- 热点快报页当前使用的是多源聚合，不保证所有来源发布时间完全一致

## 生成文件与建议忽略项

以下内容属于运行生成文件，通常不建议提交：

- `.venv/`
- `models/`
- `data/*.csv`
- `data/status/`
- `app/__pycache__/`
- `**/__pycache__/`

建议补一个 `.gitignore` 做统一忽略。

## 当前限制

- 当前实时行情与快讯来源不是交易所级专线
- 当前项目是研究 / 观察 / 模拟工作台，不是自动交易系统
- 当前没有接券商账户
- 当前没有回测模块
- 当前没有组合管理与收益归因模块
- 当前模型还是基础因子 + LightGBM 方案

## 后续可以继续升级的方向

1. 增加基本面、行业、风格、资金流等更多特征
2. 增加回测与收益曲线页面
3. 增加模拟盘委托与成交回放
4. 增加本地定时刷新任务
5. 增加多股票池切换与参数配置页
6. 增加模型版本管理与训练日志页面
