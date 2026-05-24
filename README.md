# A股选股模型

这是一个本地运行的 A 股选股模型 Demo，包含：

- 本地网页控制台
- FastAPI 后端接口
- 本地样例股票数据
- LightGBM 训练与打分流程

## 启动

直接启动：

```powershell
cd D:\Projects\codex\Agu
.\start.ps1
```

或者手动启动：

```powershell
cd D:\Projects\codex\Agu
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

打开浏览器访问：

```text
http://127.0.0.1:8000
```

## 当前版本说明

- 默认会自动生成一份本地样例数据并完成训练。
- 页面可查看候选股、训练样本、特征数量和模型状态。
- 点击“重新训练模型”会重新训练当前模型。
- 这版还没有接入真实 A 股实时行情，也还没有接 `vn.py PaperAccount`。
- `scripts/train.py` 可以单独运行，用来手动训练模型。

## 下一步适合接入的能力

1. 用 `AKShare` 或 `Tushare Pro` 替换样例数据
2. 增加更多特征，如基本面、行业和风格因子
3. 生成每日信号文件
4. 接 `vn.py + PaperAccount` 做实时模拟盘
