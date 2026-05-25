# A-Share Local Lab

一个本地运行的 A 股 AI 选股与盯盘工作台，基于 `FastAPI + LightGBM + 原生前端`。

## 功能

- 首页：模型概览、上证分时、纳指上一交易日、美国领涨行业、刷新状态
- 模型候选股：候选股打分、推荐摘要、推荐原因、预测依据、风险提示
- 实时盯盘：实时快照、涨跌颜色、失败回退到最近收盘
- 自选股票：本地保存、搜索添加、查看历史
- 模拟盘 / 纸交易：本地现金、持仓、成交、盈亏
- 历史回看：日/周/月/季/年 + 1/5/15/30/60 分钟 + 5 日，支持缩放和悬停
- 热点快报：多源聚合、AI 总结、分类筛选、滚动加载

## 本地运行

```powershell
cd D:\Projects\codex\Agu
.\start.ps1
```

或手动启动：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

打开：

- [http://127.0.0.1:8000](http://127.0.0.1:8000)

## 数据与回退

- 历史数据优先用本地真实文件
- 失败时回退到缓存或示例数据
- 盯盘优先实时快照，失败时回退到最近收盘
- 热点快报和市场概览都有本地缓存兜底

## 模拟盘

- 本地 JSON 持久化
- 默认初始资金 `1,000,000`
- 支持买入、卖出、手工价、实时价、收盘价
- 仅做纸交易，不连券商

## 搜索与历史

- 支持代码和名称搜索
- 搜索结果可直接查看历史、加入自选、下模拟单
- 未选股时，右侧默认显示上证指数

## 热点快报

- 聚合同花顺、东方财富、财联社、新浪财经
- 支持科技、金融、新能源、医药、地产基建、资源等分类
- 滚动到底自动继续加载
- 每条快报带 AI 简要归因

## 接口

- `GET /api/overview`
- `GET /api/picks`
- `GET /api/watchlist`
- `GET /api/history/{symbol}`
- `GET /api/search`
- `GET /api/favorites`
- `GET /api/portfolio`
- `POST /api/portfolio/orders`
- `POST /api/portfolio/reset`
- `GET /api/market-overview`
- `GET /api/hot-news`

## 开源依赖

- `FastAPI`
- `LightGBM`
- `AKShare`
- `easyquotation`

## 当前限制

- 不是自动交易系统
- 不是交易所级行情专线
- 模拟盘仅用于本地观察和纸交易
