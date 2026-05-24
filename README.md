# A股 AI 选股模型

一个本地运行的 A 股 AI 选股 Demo，使用 `FastAPI + LightGBM + 原生前端网页` 构建，支持在本地完成数据准备、特征工程、模型训练、股票打分和结果展示。

当前版本的目标是先打通一条最小可运行链路：

`样例数据 -> 特征生成 -> 模型训练 -> 选股打分 -> 网页展示`

后续可以继续扩展到真实 A 股数据、实时行情和本地模拟盘执行。

## 功能特性

- 本地网页控制台，直接在浏览器查看选股结果
- FastAPI 后端接口，提供总览、候选股、重新训练能力
- 内置样例 A 股数据生成逻辑，首次运行即可体验
- 使用 `LightGBM` 做基础选股打分模型
- 支持手动重新训练模型
- 完全本地运行，不依赖云服务器

## 项目结构

```text
Agu/
├─ app/
│  ├─ core/         # 配置
│  ├─ services/     # 数据处理、特征工程、模型训练与打分
│  └─ main.py       # FastAPI 入口
├─ frontend/        # 本地网页页面与样式
├─ scripts/         # 独立训练脚本
├─ data/            # 数据目录
├─ models/          # 模型目录
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
- `AKShare`（当前已安装，后续可用于接真实 A 股数据）

## 快速开始

### 方式一：一键启动

```powershell
cd D:\Projects\codex\Agu
.\start.ps1
```

### 方式二：手动启动

```powershell
cd D:\Projects\codex\Agu
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

启动后在浏览器打开：

```text
http://127.0.0.1:8000
```

## 页面能力

当前网页支持：

- 查看股票池规模、特征数量、训练样本数量
- 查看最新候选股排名
- 查看当前模型运行状态
- 点击按钮重新训练模型

## 训练脚本

如果你想单独训练模型，可以执行：

```powershell
cd D:\Projects\codex\Agu
.venv\Scripts\python scripts\train.py
```

## 当前版本说明

- 当前默认使用本地样例数据自动生成训练集
- 当前模型是一个基础版 `LightGBM` 回归排序模型
- 当前页面主要用于打通选股模型工作流
- 这版还没有接入真实 A 股实时行情
- 这版还没有接入 `vn.py + PaperAccount` 做模拟盘执行

## 后续可扩展方向

1. 接入 `AKShare` 或 `Tushare Pro` 的真实 A 股历史数据
2. 增加更多因子特征，如基本面、行业、风格和成交量特征
3. 增加每日信号生成与导出功能
4. 接入 `vn.py + PaperAccount` 做本地实时模拟盘
5. 增加收益曲线、分组回测和模型评估页面

## 适合的使用场景

- 想学习 A 股选股模型的完整本地流程
- 想先做一个本地 AI 选股网页原型
- 想在后续继续扩展成真实数据驱动的模拟盘系统

## License

当前仓库未单独添加 License 文件，如需开源发布，建议补充 `MIT` 或你希望使用的许可证。
