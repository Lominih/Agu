const overviewCards = document.querySelector("#overviewCards");
const picksTable = document.querySelector("#picksTable");
const latestDate = document.querySelector("#latestDate");
const statusBox = document.querySelector("#statusBox");
const refreshBtn = document.querySelector("#refreshBtn");
const trainBtn = document.querySelector("#trainBtn");
const syncBtn = document.querySelector("#syncBtn");
const taskState = document.querySelector("#taskState");
const lastRefreshAt = document.querySelector("#lastRefreshAt");
const lastRefreshResult = document.querySelector("#lastRefreshResult");

const defaultSource = "real";
const defaultPool = "hs300";
let refreshPollTimer = null;

function setStatus(message) {
  statusBox.textContent = `${new Date().toLocaleString("zh-CN")}\n${message}`;
}

function formatDateTime(value) {
  if (!value) {
    return "暂无";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("zh-CN");
}

function renderTaskStatus(status) {
  const stateMap = {
    idle: "空闲",
    running: "运行中",
    success: "成功",
    failed: "失败",
  };

  taskState.textContent = stateMap[status.state] || status.state || "未知";
  lastRefreshAt.textContent = formatDateTime(status.finished_at || status.updated_at || status.started_at);

  const details = [];
  if (status.message) {
    details.push(status.message);
  }
  if (status.pool) {
    details.push(`股票池: ${status.pool}`);
  }
  if (status.rows) {
    details.push(`样本行数: ${status.rows}`);
  }
  if (status.symbols) {
    details.push(`股票数量: ${status.symbols}`);
  }
  if (status.error) {
    details.push(`错误: ${status.error}`);
  }
  lastRefreshResult.textContent = details.join(" | ") || "暂无";

  const running = status.state === "running";
  syncBtn.disabled = running;
}

function stopRefreshPolling() {
  if (refreshPollTimer) {
    window.clearInterval(refreshPollTimer);
    refreshPollTimer = null;
  }
}

async function fetchRefreshStatus() {
  const response = await fetch("/api/refresh-real-data/status");
  if (!response.ok) {
    throw new Error("刷新任务状态读取失败");
  }
  return response.json();
}

async function syncRefreshStatus() {
  const status = await fetchRefreshStatus();
  renderTaskStatus(status);
  return status;
}

function startRefreshPolling() {
  stopRefreshPolling();
  refreshPollTimer = window.setInterval(async () => {
    try {
      const status = await syncRefreshStatus();
      if (status.state === "success") {
        stopRefreshPolling();
        setStatus(`真实数据后台刷新完成。\n${JSON.stringify(status.metrics || {}, null, 2)}`);
        await loadDashboard();
      } else if (status.state === "failed") {
        stopRefreshPolling();
        setStatus(`真实数据后台刷新失败: ${status.error || status.message || "未知错误"}`);
      }
    } catch (error) {
      stopRefreshPolling();
      setStatus(`刷新任务状态轮询失败: ${error.message}`);
    }
  }, 3000);
}

function renderCards(overview) {
  const poolNameMap = {
    hs300: "沪深300",
    zz500: "中证500",
    all: "合并股票池",
    sample: "样例池",
  };

  const cards = [
    {
      label: "股票池规模",
      value: `${overview.universe_size} 只`,
      hint: "当前参与训练和打分的股票数量",
    },
    {
      label: "特征数量",
      value: `${overview.feature_count}`,
      hint: "用于训练和打分的基础因子数量",
    },
    {
      label: "训练样本",
      value: `${overview.sample_rows}`,
      hint: "具备标签和特征的有效样本行数",
    },
    {
      label: "数据来源",
      value: overview.data_source === "real" ? "AKShare 本地快照" : "样例数据",
      hint: overview.data_source === "real" ? "页面只读取本地已刷新完成的真实数据文件" : "未检测到真实数据时自动回退",
    },
    {
      label: "股票池",
      value: poolNameMap[overview.pool] || overview.pool,
      hint: "当前训练和打分使用的股票池",
    },
    {
      label: "当前第一名",
      value: `${overview.top_pick.name}`,
      hint: `${overview.top_pick.symbol} | 预测未来5日 ${overview.top_pick.predicted_return_5}%`,
    },
  ];

  overviewCards.innerHTML = cards
    .map(
      (card) => `
        <article class="card">
          <div class="label">${card.label}</div>
          <div class="value">${card.value}</div>
          <div class="hint">${card.hint}</div>
        </article>
      `
    )
    .join("");

  latestDate.textContent = `最新打分日期: ${overview.latest_date}`;
}

function renderPicks(items) {
  picksTable.innerHTML = items
    .map(
      (item) => `
        <tr>
          <td>${item.symbol}</td>
          <td>${item.name}</td>
          <td>${item.close}</td>
          <td>${item.ret_5}</td>
          <td>${item.ret_10}</td>
          <td>${item.predicted_return_5}</td>
        </tr>
      `
    )
    .join("");
}

async function loadDashboard() {
  setStatus("正在加载本地候选股结果...");

  const [overviewRes, picksRes] = await Promise.all([
    fetch(`/api/overview?source=${defaultSource}`),
    fetch(`/api/picks?limit=8&source=${defaultSource}`),
  ]);

  if (!overviewRes.ok || !picksRes.ok) {
    throw new Error("接口请求失败");
  }

  const overview = await overviewRes.json();
  const picks = await picksRes.json();

  renderCards(overview);
  renderPicks(picks.items);

  if (overview.trained_now && overview.training_metrics) {
    setStatus(`首次加载时自动完成训练。\n${JSON.stringify(overview.training_metrics, null, 2)}`);
  } else {
    setStatus(`页面已刷新，当前使用 ${overview.data_source === "real" ? "本地真实数据快照" : "样例数据"} 打分。`);
  }
}

async function retrain() {
  setStatus("正在重新训练模型...");
  trainBtn.disabled = true;
  try {
    const response = await fetch(`/api/train?source=${defaultSource}`, { method: "POST" });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "训练请求失败");
    }
    setStatus(`${payload.message}\n${JSON.stringify(payload.metrics, null, 2)}`);
    await loadDashboard();
  } finally {
    trainBtn.disabled = false;
  }
}

async function refreshRealData() {
  setStatus("正在启动真实数据后台刷新任务...");
  syncBtn.disabled = true;
  try {
    const response = await fetch(`/api/refresh-real-data?pool=${defaultPool}`, { method: "POST" });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "真实数据刷新任务启动失败");
    }

    renderTaskStatus(payload.status);
    setStatus(`${payload.message}\n请等待后台脚本完成抓取和训练。`);

    if (payload.status.state === "running") {
      startRefreshPolling();
    } else {
      syncBtn.disabled = false;
    }
  } catch (error) {
    syncBtn.disabled = false;
    throw error;
  }
}

refreshBtn.addEventListener("click", () => {
  loadDashboard().catch((error) => {
    setStatus(`刷新失败: ${error.message}`);
  });
});

trainBtn.addEventListener("click", () => {
  retrain().catch((error) => {
    setStatus(`训练失败: ${error.message}`);
  });
});

syncBtn.addEventListener("click", () => {
  refreshRealData().catch((error) => {
    setStatus(`真实数据后台刷新失败: ${error.message}`);
  });
});

Promise.all([loadDashboard(), syncRefreshStatus()])
  .then(([, status]) => {
    if (status.state === "running") {
      setStatus("检测到后台刷新任务仍在运行，正在持续轮询状态...");
      startRefreshPolling();
    }
  })
  .catch((error) => {
    setStatus(`初始化失败: ${error.message}`);
  });
