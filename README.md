# A股 AI 选股模型

一个本地运行的 A 股 AI 选股演示项目，使用 `FastAPI + LightGBM + 原生前端网页` 构建。  
它支持在本地完成数据准备、特征工程、模型训练、股票打分和结果展示。

这一版重点解决了“真实数据刷新容易卡页面、不够稳”的问题：

- 页面默认只读取本地已有数据，不会在普通请求里偷偷触发远程抓数
- 真实 A 股数据刷新改成后台脚本任务
- 前端可以看到刷新任务的运行中、成功、失败状态
- 就算 AKShare 抓取失败，页面也仍然可以继续使用本地已有结果或样例数据

## 功能特点

- 本地网页控制台，直接查看候选股结果
- FastAPI 后端接口，提供总览、候选股、训练、后台刷新状态查询
- 使用 `AKShare` 获取真实 A 股历史日线数据
- 使用 `LightGBM` 做基础选股打分模型
- 支持一键重新训练模型
- 支持一键启动后台真实数据刷新任务
- 完全本地运行，不依赖云服务器

## 当前真实数据方案

当前默认使用指数成分股做股票池：

- `hs300` -> 沪深300
- `zz500` -> 中证500

真实数据流程如下：

`指数成分股 -> AKShare 历史日线 -> 特征生成 -> 模型训练 -> 网页展示`

为了提高稳定性，真实数据刷新不再直接跑在 HTTP 请求里，而是通过独立脚本执行。

## 项目结构

```text
Agu/
├─ app/
│  ├─ core/                  # 配置
│  ├─ services/              # 数据处理、训练、刷新状态
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
  - 重新加载当前本地结果
- `重新训练模型`
  - 使用当前本地数据重新训练模型
- `后台刷新真实数据`
  - 启动独立后台脚本抓取真实数据并训练
  - 页面会轮询显示运行状态

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
- `POST /api/train`
  - 使用本地已有数据重新训练模型
- `POST /api/refresh-real-data`
  - 启动后台真实数据刷新任务
- `GET /api/refresh-real-data/status`
  - 查询后台真实数据刷新状态

## 生成文件说明

以下内容属于运行生成文件，已建议忽略提交：

- `.venv/`
- `models/`
- `data/*.csv`
- `data/status/`

如果你还没有把 `data/status/` 加进 `.gitignore`，建议下一次一起补上。

## 当前限制

- 当前还是历史日线级别选股，不是盘中实时策略
- 当前还没有接入真实撮合或模拟盘交易引擎
- 当前模型仍然是基础版 LightGBM 回归排序模型
- 当前没有收益曲线、回测和组合管理页面

## 后续建议

1. 增加更多特征，比如基本面、行业、风格和成交额因子
2. 把股票池扩展到 `zz500` 切换选择
3. 增加回测和收益曲线页面
4. 接入本地模拟盘执行模块
5. 增加每天定时刷新和定时训练
