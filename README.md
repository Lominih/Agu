# A股 AI 选股与盯盘

一个本地运行的 A 股 AI 选股演示项目，使用 `FastAPI + LightGBM + 原生前端网页` 构建。  
它支持在本地完成数据准备、特征工程、模型训练、股票打分、实时盯盘和历史回看。

这一版重点解决了两个问题：

- 真实数据刷新不再阻塞页面，而是改成后台脚本任务
- 首页新增盯盘能力，白天看实时快照，晚上和周末也能看最近交易日状态与历史走势

## 功能特点

- 本地网页控制台，直接查看模型候选股结果
- FastAPI 后端接口，提供总览、候选股、训练、后台刷新状态查询
- 使用 `AKShare` 获取真实 A 股历史日线数据
- 使用 `easyquotation` 获取盯盘实时快照
- 使用 `LightGBM` 做基础选股打分模型
- 支持一键重新训练模型
- 支持一键启动后台真实数据刷新任务
- 支持查看模型 Top 候选股的实时盯盘信息
- 支持单股最近 30 个交易日历史回看
- 完全本地运行，不依赖云服务器

## 当前真实数据方案

当前默认使用指数成分股做股票池：

- `hs300` -> 沪深300
- `zz500` -> 中证500

真实数据流程如下：

`指数成分股 -> AKShare 历史日线 -> 特征生成 -> 模型训练 -> 候选股打分 -> 网页展示`

为了提高稳定性，真实数据刷新不再直接跑在 HTTP 请求里，而是通过独立脚本执行。

## 盯盘模式说明

首页已经内置“模型候选股 + 盯盘”模式：

- 模型候选股区域展示当前 Top 候选股
- 实时盯盘区域优先显示实时快照
- 如果当前是非交易时段，或者实时源暂时不可用，会自动回退到最近交易日收盘状态
- 点击“查看历史”可以查看某只股票最近 30 个交易日的本地历史数据

这意味着在类似 `2026-05-24 21:35` 这样的晚上时段，你仍然可以看到：

- 上个交易日的收盘状态
- 最近交易日日期
- 更早历史走势

## 项目结构

```text
Agu/
├─ app/
│  ├─ core/                  # 配置
│  ├─ services/              # 数据处理、训练、刷新状态、盯盘服务
│  └─ main.py                # FastAPI 入口
├─ frontend/                 # 本地网页
├─ scripts/
│  ├─ train.py               # 使用本地已有数据训练模型
│  └─ refresh_real_data.py   # 后台刷新真实 A 股数据并训练
├─ data/                     # 数据目录
├─ models/                   # 模型目录
├─ requirements.txt
├─ start.ps1
└─ README.md
```

## 技术栈

- `FastAPI`
- `Uvicorn`
- `Pandas`
- `NumPy`
- `LightGBM`
- `scikit-learn`
- `AKShare`
- `easyquotation`

## 开源项目与代码说明

当前仓库没有直接复制第三方项目的业务源码文件，主要是基于开源库的公开接口做集成开发。

本项目当前实际使用了这些开源项目：

- `AKShare`
  - 用途：获取 A 股历史日线、指数成分股等训练与回看数据
  - 仓库：<https://github.com/akfamily/akshare>
- `easyquotation`
  - 用途：获取盯盘页的实时行情快照
  - 仓库：<https://github.com/shidenggui/easyquotation>
- `LightGBM`
  - 用途：训练选股排序模型
  - 仓库：<https://github.com/lightgbm-org/LightGBM>
- `FastAPI`
  - 用途：提供本地 Web API 和页面服务
  - 仓库：<https://github.com/fastapi/fastapi>

额外说明：

- 这次“实时盯盘/收盘后回看”功能，实际接入的是 `easyquotation` 的实时行情能力和 `AKShare` 的本地历史数据能力。
- 我调研过 `efinance`、`pytdx`、`vn.py` 这些项目，但当前代码里没有接入它们的实现。
- 如果你后续希望更严格地做开源合规展示，可以继续补一个 `NOTICE` 文件，把依赖名称、仓库地址、许可证统一列出来。

## 快速开始

### 一键启动

```powershell
cd D:\Projects\codex\Agu
.\start.ps1
```

### 手动启动

```powershell
cd D:\Projects\codex\Agu
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

启动后打开：

```text
http://127.0.0.1:8000
```

## 页面行为说明

- `刷新候选股`
  - 重新加载当前本地模型打分结果
- `重新训练模型`
  - 使用当前本地数据重新训练模型
- `后台刷新真实数据`
  - 启动独立后台脚本抓取真实数据并训练
  - 页面会轮询显示运行状态
- `刷新盯盘快照`
  - 重新拉取当前 Top 候选股的盯盘快照
- `查看历史`
  - 查看对应股票最近 30 个交易日的历史回看

## 独立脚本

### 1. 仅使用本地已有数据训练

```powershell
cd D:\Projects\codex\Agu
.venv\Scripts\python scripts\train.py
```

说明：

- 如果 `data/a_share_prices.csv` 存在，就用真实数据训练
- 否则使用样例数据训练
- 不会主动远程抓数

### 2. 刷新真实数据并训练

```powershell
cd D:\Projects\codex\Agu
.venv\Scripts\python scripts\refresh_real_data.py --pool hs300
```

可选参数：

- `--pool hs300`
- `--pool zz500`
- `--start-date 2023-01-01`
- `--workers 6`

## API 概览

- `GET /api/health`
  - 健康检查
- `GET /api/overview`
  - 返回模型总览信息
- `GET /api/picks`
  - 返回候选股列表
- `GET /api/watchlist`
  - 返回当前盯盘列表，优先使用实时快照
- `GET /api/watch-history/{symbol}`
  - 返回单股最近历史回看
- `POST /api/train`
  - 使用本地已有数据重新训练模型
- `POST /api/refresh-real-data`
  - 启动后台真实数据刷新任务
- `GET /api/refresh-real-data/status`
  - 查询后台真实数据刷新状态

## 生成文件说明

以下内容属于运行生成文件，建议忽略提交：

- `.venv/`
- `models/`
- `data/*.csv`
- `data/status/`

## 当前限制

- 当前盯盘快照使用免费行情源，不是券商级专线行情
- 当前还是选股与盯盘页面，不是自动交易系统
- 当前没有回测、收益曲线和组合管理页面
- 当前模型仍然是基础版 LightGBM 回归排序模型

## 后续建议

1. 增加更多特征，比如基本面、行业、风格和成交额因子
2. 把股票池扩展到 `zz500` 切换选择
3. 增加回测和收益曲线页面
4. 接入本地模拟盘执行模块
5. 增加每天定时刷新和定时训练
