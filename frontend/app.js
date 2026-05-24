const overviewCards = document.querySelector("#overviewCards");
const picksTable = document.querySelector("#picksTable");
const latestDate = document.querySelector("#latestDate");
const statusBox = document.querySelector("#statusBox");
const refreshBtn = document.querySelector("#refreshBtn");
const trainBtn = document.querySelector("#trainBtn");
const syncBtn = document.querySelector("#syncBtn");

const defaultSource = "real";
const defaultPool = "hs300";

function setStatus(message) {
  statusBox.textContent = `${new Date().toLocaleString("zh-CN")}\n${message}`;
}

function renderCards(overview) {
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
      value: overview.data_source === "real" ? "AKShare" : "样例数据",
      hint: overview.data_source === "real" ? "真实A股历史日线" : "本地兜底样例数据",
    },
    {
      label: "股票池",
      value: overview.pool === "hs300" ? "沪深300" : overview.pool === "zz500" ? "中证500" : overview.pool === "all" ? "合并池" : "样例池",
      hint: "当前真实数据训练使用的股票池",
    },
    {
      label: "当前第一名",
      value: `${overview.top_pick.name}`,
      hint: `${overview.top_pick.symbol} · 预测未来5日 ${overview.top_pick.predicted_return_5}%`,
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

  latestDate.textContent = `最新打分日期：${overview.latest_date}`;
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
  setStatus("正在加载真实A股选股结果...");

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
    setStatus(`页面已刷新，当前使用 ${overview.data_source === "real" ? "AKShare真实数据" : "样例数据"} 打分。`);
  }
}

async function retrain() {
  setStatus("正在重新训练模型...");
  trainBtn.disabled = true;
  try {
    const response = await fetch(`/api/train?source=${defaultSource}`, { method: "POST" });
    if (!response.ok) {
      throw new Error("训练请求失败");
    }
    const payload = await response.json();
    setStatus(`${payload.message}\n${JSON.stringify(payload.metrics, null, 2)}`);
    await loadDashboard();
  } finally {
    trainBtn.disabled = false;
  }
}

async function refreshRealData() {
  setStatus("正在通过 AKShare 刷新真实A股历史数据...");
  syncBtn.disabled = true;
  try {
    const response = await fetch(`/api/refresh-real-data?pool=${defaultPool}`, { method: "POST" });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "真实数据刷新失败");
    }
    setStatus(`${payload.message}\n股票池: ${payload.pool}\n${JSON.stringify(payload.metrics, null, 2)}`);
    await loadDashboard();
  } finally {
    syncBtn.disabled = false;
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
    setStatus(`真实数据刷新失败: ${error.message}`);
  });
});

loadDashboard().catch((error) => {
  setStatus(`初始化失败: ${error.message}`);
});
