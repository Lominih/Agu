const overviewCards = document.querySelector("#overviewCards");
const picksTable = document.querySelector("#picksTable");
const watchTable = document.querySelector("#watchTable");
const watchlistTable = document.querySelector("#watchlistTable");
const watchlistSummary = document.querySelector("#watchlistSummary");
const historyTable = document.querySelector("#historyTable");
const historyTitle = document.querySelector("#historyTitle");
const historyChart = document.querySelector("#historyChart");
const historyBadge = document.querySelector("#historyBadge");
const historyBackBtn = document.querySelector("#historyBackBtn");
const historyExpandBtn = document.querySelector("#historyExpandBtn");
const historyTooltip = document.querySelector("#historyTooltip");
const stockSearchInput = document.querySelector("#stockSearchInput");
const searchResults = document.querySelector("#searchResults");
const latestDate = document.querySelector("#latestDate");
const watchSource = document.querySelector("#watchSource");
const statusBox = document.querySelector("#statusBox");
const refreshBtn = document.querySelector("#refreshBtn");
const trainBtn = document.querySelector("#trainBtn");
const syncBtn = document.querySelector("#syncBtn");
const watchBtn = document.querySelector("#watchBtn");
const taskState = document.querySelector("#taskState");
const lastRefreshAt = document.querySelector("#lastRefreshAt");
const lastRefreshResult = document.querySelector("#lastRefreshResult");
const marketUpdatedAt = document.querySelector("#marketUpdatedAt");
const marketNasdaqCard = document.querySelector("#marketNasdaqCard");
const marketNasdaqPct = document.querySelector("#marketNasdaqPct");
const marketNasdaqMeta = document.querySelector("#marketNasdaqMeta");
const marketShanghaiDate = document.querySelector("#marketShanghaiDate");
const marketOpen = document.querySelector("#marketOpen");
const marketCurrent = document.querySelector("#marketCurrent");
const marketChange = document.querySelector("#marketChange");
const marketChangePct = document.querySelector("#marketChangePct");
const homeUsLeaderList = document.querySelector("#homeUsLeaderList");
const marketChart = document.querySelector("#marketChart");
const marketTooltip = document.querySelector("#marketTooltip");
const marketZoomInBtn = document.querySelector("#marketZoomInBtn");
const marketZoomOutBtn = document.querySelector("#marketZoomOutBtn");
const marketZoomResetBtn = document.querySelector("#marketZoomResetBtn");
const navItems = document.querySelectorAll(".nav-item");
const pages = document.querySelectorAll(".page");
const historyPeriodTabs = document.querySelector("#historyPeriodTabs");
const historyZoomInBtn = document.querySelector("#historyZoomInBtn");
const historyZoomOutBtn = document.querySelector("#historyZoomOutBtn");
const historyZoomResetBtn = document.querySelector("#historyZoomResetBtn");

const defaultSource = "real";
const defaultPool = "hs300";
const defaultPicksLimit = 18;
const defaultWatchLimit = 20;

const periodLimitMap = {
  day: 120,
  week: 90,
  month: 90,
  quarter: 60,
  year: 30,
  "1m": 240,
  "5m": 240,
  "15m": 220,
  "30m": 200,
  "60m": 180,
  "5d": 1200,
};

const periodLabelMap = {
  day: "日线",
  week: "周线",
  month: "月线",
  quarter: "季线",
  year: "年线",
  "1m": "1分",
  "5m": "5分",
  "15m": "15分",
  "30m": "30分",
  "60m": "60分",
  "5d": "5日",
};

const state = {
  refreshPollTimer: null,
  marketPollTimer: null,
  searchTimer: null,
  picks: [],
  watch: [],
  favorites: [],
  currentHistorySymbol: "sh000001",
  currentHistoryName: "上证指数",
  selectedPeriod: "day",
  activeChartMode: "candles",
  historyPayload: null,
  previousHistoryPayload: null,
  intradayPayload: null,
  chartItems: [],
  chartViewport: { start: 0, end: 0 },
  chartGeometry: null,
  chartHoverIndex: null,
  historyExpanded: false,
  marketOverview: null,
  marketChartItems: [],
  marketChartViewport: { start: 0, end: 0 },
  marketChartGeometry: null,
  marketChartHoverIndex: null,
};

function setStatus(message) {
  if (!(statusBox instanceof HTMLElement)) {
    return;
  }
  statusBox.textContent = `${new Date().toLocaleString("zh-CN")}\n${message}`;
}

function switchPage(pageName) {
  navItems.forEach((item) => {
    item.classList.toggle("active", item.dataset.page === pageName);
  });
  pages.forEach((page) => {
    page.classList.toggle("active", page.dataset.page === pageName);
  });
}

function syncHistoryLayout() {
  document.body.classList.toggle("history-expanded", state.historyExpanded);
  if (historyExpandBtn instanceof HTMLButtonElement) {
    historyExpandBtn.classList.toggle("is-active", state.historyExpanded);
    historyExpandBtn.setAttribute("aria-pressed", state.historyExpanded ? "true" : "false");
    historyExpandBtn.textContent = state.historyExpanded ? "退出大图" : "大图模式";
  }
}

function setHistoryExpanded(expanded) {
  state.historyExpanded = Boolean(expanded);
  syncHistoryLayout();
  window.setTimeout(() => {
    drawCurrentChart();
  }, 30);
}

function toggleHistoryExpanded() {
  setHistoryExpanded(!state.historyExpanded);
  setStatus(state.historyExpanded ? "右侧趋势图已切换到大图模式。" : "已退出大图模式，恢复常规工作台布局。");
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

function formatSignedPercent(value) {
  if (value == null || Number.isNaN(Number(value))) {
    return "-";
  }
  const numeric = Number(value);
  return `${numeric > 0 ? "+" : ""}${numeric.toFixed(2)}%`;
}

function formatNumber(value, digits = 2) {
  if (value == null || Number.isNaN(Number(value))) {
    return "-";
  }
  return Number(value).toFixed(digits);
}

function getToneClass(changePct) {
  if (changePct == null || Number.isNaN(Number(changePct))) {
    return "quote-flat";
  }
  if (Number(changePct) > 0) {
    return "quote-up";
  }
  if (Number(changePct) < 0) {
    return "quote-down";
  }
  return "quote-flat";
}

function getToneClassName(changePct) {
  if (changePct == null || Number.isNaN(Number(changePct))) {
    return "market-flat";
  }
  if (Number(changePct) > 0) {
    return "market-up";
  }
  if (Number(changePct) < 0) {
    return "market-down";
  }
  return "market-flat";
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || payload.message || `请求失败: ${response.status}`);
  }
  return payload;
}

function renderTaskStatus(status) {
  if (!taskState || !lastRefreshAt || !lastRefreshResult || !syncBtn) {
    return;
  }

  const stateMap = {
    idle: "空闲",
    running: "运行中",
    success: "成功",
    failed: "失败",
  };

  taskState.textContent = stateMap[status.state] || status.state || "未知";
  lastRefreshAt.textContent = formatDateTime(status.finished_at || status.updated_at || status.started_at);

  const parts = [];
  if (status.message) {
    parts.push(status.message);
  }
  if (status.pool) {
    parts.push(`股票池: ${status.pool}`);
  }
  if (status.rows) {
    parts.push(`样本行数: ${status.rows}`);
  }
  if (status.symbols) {
    parts.push(`股票数量: ${status.symbols}`);
  }
  if (status.error) {
    parts.push(`错误: ${status.error}`);
  }

  lastRefreshResult.textContent = parts.join(" | ") || "暂无";
  syncBtn.disabled = status.state === "running";
}

function stopRefreshPolling() {
  if (state.refreshPollTimer) {
    window.clearInterval(state.refreshPollTimer);
    state.refreshPollTimer = null;
  }
}

function stopMarketPolling() {
  if (state.marketPollTimer) {
    window.clearInterval(state.marketPollTimer);
    state.marketPollTimer = null;
  }
}

async function syncRefreshStatus() {
  const status = await fetchJson("/api/refresh-real-data/status");
  renderTaskStatus(status);
  return status;
}

function startRefreshPolling() {
  stopRefreshPolling();
  state.refreshPollTimer = window.setInterval(async () => {
    try {
      const status = await syncRefreshStatus();
      if (status.state === "success") {
        stopRefreshPolling();
        setStatus(`真实数据后台刷新完成。\n${JSON.stringify(status.metrics || {}, null, 2)}`);
        await initializeDashboard();
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
  if (!overviewCards || !latestDate) {
    return;
  }

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
      hint: "用于训练的有效历史样本行数",
    },
    {
      label: "数据来源",
      value: overview.data_source === "real" ? "本地真实数据" : "样例数据",
      hint: overview.data_source === "real" ? "打分优先使用本地真实数据文件" : "未检测到真实数据时自动回退",
    },
    {
      label: "股票池",
      value: poolNameMap[overview.pool] || overview.pool || "-",
      hint: "当前训练和打分使用的股票池",
    },
    {
      label: "当前第一名",
      value: overview.top_pick?.name || "-",
      hint: `${overview.top_pick?.symbol || "-"} | 预测未来5日 ${overview.top_pick?.predicted_return_5 ?? "-"}%`,
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
  state.picks = items;
  if (!picksTable) {
    return;
  }

  picksTable.innerHTML = items
    .map(
      (item) => `
        <tr>
          <td>${item.symbol}</td>
          <td>${item.name}</td>
          <td>${formatNumber(item.close)}</td>
          <td>${formatSignedPercent(item.ret_5)}</td>
          <td>${formatSignedPercent(item.ret_10)}</td>
          <td>${formatSignedPercent(item.predicted_return_5)}</td>
          <td><button class="mini-btn" data-action="view" data-symbol="${item.symbol}" data-name="${item.name || ""}" type="button">查看历史</button></td>
        </tr>
      `
    )
    .join("");
}

function renderWatch(items) {
  state.watch = items;
  if (!watchTable || !watchSource) {
    return;
  }

  watchSource.textContent = items.some((item) => item.mode === "live")
    ? "当前包含实时快照"
    : "当前显示最近收盘状态";

  watchTable.innerHTML = items
    .map((item) => {
      const toneClass = getToneClass(item.change_pct);
      return `
        <tr class="${toneClass}">
          <td>${item.symbol}</td>
          <td>${item.name || "-"}</td>
          <td>${item.mode === "live" ? "实时" : "收盘"}</td>
          <td>${item.trade_date || "-"}</td>
          <td>${item.trade_time || "-"}</td>
          <td>${formatNumber(item.price)}</td>
          <td>${formatSignedPercent(item.change_pct)}</td>
          <td>${formatNumber(item.pre_close ?? item.fallback_close)}</td>
          <td><button class="mini-btn" data-action="view" data-symbol="${item.symbol}" data-name="${item.name || ""}" type="button">查看历史</button></td>
        </tr>
      `;
    })
    .join("");
}

function renderWatchlist(items, updatedAt) {
  state.favorites = items;
  if (!watchlistTable || !watchlistSummary) {
    return;
  }

  watchlistSummary.textContent = items.length
    ? `当前共 ${items.length} 只自选股，最近更新时间 ${formatDateTime(updatedAt)}。`
    : "本地保存搜索添加的股票，支持实时快照、删除和切到右侧历史回看。";

  if (!items.length) {
    watchlistTable.innerHTML = `<tr class="placeholder-row"><td colspan="9">暂无自选股票，可在右侧搜索结果里添加。</td></tr>`;
    return;
  }

  watchlistTable.innerHTML = items
    .map((item) => {
      const toneClass = getToneClass(item.change_pct);
      return `
        <tr class="${toneClass}">
          <td>${item.symbol}</td>
          <td>${item.name || "-"}</td>
          <td>${item.mode === "live" ? "实时" : "收盘"}</td>
          <td>${item.trade_date || "-"}</td>
          <td>${item.trade_time || "-"}</td>
          <td>${formatNumber(item.price)}</td>
          <td>${formatSignedPercent(item.change_pct)}</td>
          <td>${item.added_at ? formatDateTime(item.added_at) : "-"}</td>
          <td>
            <button class="mini-btn" data-action="view" data-symbol="${item.symbol}" data-name="${item.name || ""}" type="button">查看</button>
            <button class="danger-btn" data-action="remove-favorite" data-symbol="${item.symbol}" data-kind="${item.kind || "stock"}" type="button">删除</button>
          </td>
        </tr>
      `;
    })
    .join("");
}

function renderSearchResults(items) {
  if (!searchResults) {
    return;
  }

  if (!items.length) {
    searchResults.innerHTML = `<div class="search-empty">没有匹配结果</div>`;
    return;
  }

  searchResults.innerHTML = items
    .map((item) => {
      const extra = item.latest_date ? `最近数据 ${item.latest_date}` : item.kind === "index" ? "指数" : "可远程查询";
      return `
        <div class="search-result-row">
          <div class="search-result-main">
            <span class="search-symbol">${item.symbol}</span>
            <span class="search-name">${item.name || "-"}</span>
            <span class="search-extra">${extra}</span>
          </div>
          <div class="search-result-actions">
            <button class="search-action-btn" data-action="view-search" data-symbol="${item.symbol}" data-name="${item.name || ""}" type="button">查看</button>
            <button class="search-action-btn search-action-btn-ghost ${item.is_favorite ? "is-added" : ""}" data-action="add-favorite" data-symbol="${item.symbol}" data-name="${item.name || ""}" data-kind="${item.kind || "stock"}" ${item.is_favorite ? "disabled" : ""} type="button">
              ${item.is_favorite ? "已添加" : "添加自选"}
            </button>
          </div>
        </div>
      `;
    })
    .join("");
}

function setActivePeriodButton(period) {
  historyPeriodTabs?.querySelectorAll("[data-period]").forEach((button) => {
    button.classList.toggle("active", button.dataset.period === period);
  });
}

function getDefaultVisibleCount(period, mode) {
  if (mode === "intraday-line") {
    return 180;
  }
  const map = {
    day: 80,
    week: 64,
    month: 60,
    quarter: 50,
    year: 24,
    "1m": 140,
    "5m": 120,
    "15m": 100,
    "30m": 90,
    "60m": 80,
    "5d": 220,
  };
  return map[period] || 80;
}

function resetChartViewport() {
  const size = getDefaultVisibleCount(state.selectedPeriod, state.activeChartMode);
  const total = state.chartItems.length;
  const visible = Math.min(total, size);
  state.chartViewport.end = total;
  state.chartViewport.start = Math.max(0, total - visible);
  state.chartHoverIndex = null;
}

function resetMarketChartViewport() {
  const total = state.marketChartItems.length;
  const visible = Math.min(total, 180);
  state.marketChartViewport.end = total;
  state.marketChartViewport.start = Math.max(0, total - visible);
  state.marketChartHoverIndex = null;
}

function getVisibleChartItems() {
  return state.chartItems.slice(state.chartViewport.start, state.chartViewport.end);
}

function ensureChartViewport() {
  const total = state.chartItems.length;
  let start = Math.max(0, Math.min(state.chartViewport.start, total));
  let end = Math.max(start, Math.min(state.chartViewport.end, total));
  if (end === start && total > 0) {
    start = 0;
    end = total;
  }
  state.chartViewport.start = start;
  state.chartViewport.end = end;
}

function ensureMarketChartViewport() {
  const total = state.marketChartItems.length;
  let start = Math.max(0, Math.min(state.marketChartViewport.start, total));
  let end = Math.max(start, Math.min(state.marketChartViewport.end, total));
  if (end === start && total > 0) {
    start = 0;
    end = total;
  }
  state.marketChartViewport.start = start;
  state.marketChartViewport.end = end;
}

function zoomChart(factor, anchorRatio = 0.8) {
  const total = state.chartItems.length;
  if (total <= 8) {
    return;
  }

  const currentSize = state.chartViewport.end - state.chartViewport.start;
  const minSize = state.activeChartMode === "intraday-line" ? 24 : 12;
  const nextSize = Math.max(minSize, Math.min(total, Math.round(currentSize * factor)));
  const anchorIndex = state.chartViewport.start + Math.round(currentSize * anchorRatio);
  let nextStart = Math.round(anchorIndex - nextSize * anchorRatio);
  nextStart = Math.max(0, Math.min(nextStart, total - nextSize));
  state.chartViewport.start = nextStart;
  state.chartViewport.end = nextStart + nextSize;
  drawCurrentChart();
}

function zoomMarketChart(factor, anchorRatio = 0.8) {
  const total = state.marketChartItems.length;
  if (total <= 8) {
    return;
  }

  const currentSize = state.marketChartViewport.end - state.marketChartViewport.start;
  const nextSize = Math.max(20, Math.min(total, Math.round(currentSize * factor)));
  const anchorIndex = state.marketChartViewport.start + Math.round(currentSize * anchorRatio);
  let nextStart = Math.round(anchorIndex - nextSize * anchorRatio);
  nextStart = Math.max(0, Math.min(nextStart, total - nextSize));
  state.marketChartViewport.start = nextStart;
  state.marketChartViewport.end = nextStart + nextSize;
  drawMarketChart();
}

function applyMouseWheelZoom(event) {
  if (!state.chartItems.length || !state.chartGeometry) {
    return;
  }

  event.preventDefault();
  const rect = historyChart.getBoundingClientRect();
  const margin = state.chartGeometry.margin;
  const plotLeft = margin.left;
  const plotWidth = state.chartGeometry.plotWidth;
  const ratio = Math.max(0, Math.min(1, (event.clientX - rect.left - plotLeft) / Math.max(plotWidth, 1)));
  zoomChart(event.deltaY < 0 ? 0.85 : 1.18, ratio);
}

function applyMarketMouseWheelZoom(event) {
  if (!state.marketChartItems.length || !state.marketChartGeometry || !(marketChart instanceof HTMLCanvasElement)) {
    return;
  }

  event.preventDefault();
  const rect = marketChart.getBoundingClientRect();
  const margin = state.marketChartGeometry.margin;
  const ratio = Math.max(
    0,
    Math.min(1, (event.clientX - rect.left - margin.left) / Math.max(state.marketChartGeometry.plotWidth, 1))
  );
  zoomMarketChart(event.deltaY < 0 ? 0.85 : 1.18, ratio);
}

function setupCanvas() {
  if (!(historyChart instanceof HTMLCanvasElement)) {
    return null;
  }
  const ctx = historyChart.getContext("2d");
  if (!ctx) {
    return null;
  }
  const dpr = window.devicePixelRatio || 1;
  const width = historyChart.clientWidth || historyChart.width;
  const height = historyChart.clientHeight || historyChart.height;
  historyChart.width = Math.floor(width * dpr);
  historyChart.height = Math.floor(height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#0c1118";
  ctx.fillRect(0, 0, width, height);
  return { ctx, width, height };
}

function setupMarketCanvas() {
  if (!(marketChart instanceof HTMLCanvasElement)) {
    return null;
  }
  const ctx = marketChart.getContext("2d");
  if (!ctx) {
    return null;
  }
  const dpr = window.devicePixelRatio || 1;
  const width = marketChart.clientWidth || marketChart.width;
  const height = marketChart.clientHeight || marketChart.height;
  marketChart.width = Math.floor(width * dpr);
  marketChart.height = Math.floor(height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#09111a";
  ctx.fillRect(0, 0, width, height);
  return { ctx, width, height };
}

function drawEmptyChart(text) {
  const setup = setupCanvas();
  if (!setup) {
    return;
  }
  setup.ctx.fillStyle = "#8ea0b8";
  setup.ctx.font = "14px Segoe UI";
  setup.ctx.fillText(text, 24, 32);
  state.chartGeometry = null;
  hideHistoryTooltip();
}

function drawEmptyMarketChart(text) {
  const setup = setupMarketCanvas();
  if (!setup) {
    return;
  }
  setup.ctx.fillStyle = "#8ea0b8";
  setup.ctx.font = "12px Segoe UI";
  setup.ctx.fillText(text, 16, 26);
  state.marketChartGeometry = null;
  hideMarketTooltip();
}

function drawCurrentChart() {
  ensureChartViewport();
  if (!state.chartItems.length) {
    drawEmptyChart("暂无图表数据");
    return;
  }
  if (state.activeChartMode === "intraday-line") {
    drawIntradayLineChart();
  } else {
    drawCandlesChart();
  }
}

function drawMarketChart() {
  ensureMarketChartViewport();
  const setup = setupMarketCanvas();
  if (!setup) {
    return;
  }

  const items = state.marketChartItems.slice(state.marketChartViewport.start, state.marketChartViewport.end);
  if (!items.length) {
    drawEmptyMarketChart("暂无上证分时数据");
    return;
  }

  const { ctx, width, height } = setup;
  const margin = { top: 14, right: 12, bottom: 24, left: 44 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const values = items.map((item) => Number(item.change_pct ?? 0));
  const minValue = Math.min(...values, 0);
  const maxValue = Math.max(...values, 0);
  const range = Math.max(maxValue - minValue, 0.16);
  const stepX = items.length > 1 ? plotWidth / (items.length - 1) : plotWidth;
  const xForIndex = (index) => margin.left + stepX * index;
  const valueToY = (value) => margin.top + ((maxValue - value) / range) * plotHeight;

  drawGrid(ctx, margin, plotWidth, plotHeight, 4);
  const zeroY = valueToY(0);
  ctx.strokeStyle = "rgba(126, 231, 247, 0.25)";
  ctx.beginPath();
  ctx.moveTo(margin.left, zeroY);
  ctx.lineTo(margin.left + plotWidth, zeroY);
  ctx.stroke();

  ctx.fillStyle = "#8ea0b8";
  ctx.font = "11px Segoe UI";
  for (let row = 0; row <= 4; row += 1) {
    const value = maxValue - (range / 4) * row;
    const y = margin.top + (plotHeight / 4) * row;
    ctx.fillText(formatSignedPercent(value), 4, y + 4);
  }

  ctx.strokeStyle = values[values.length - 1] >= 0 ? "#ff6b66" : "#2dd36f";
  ctx.lineWidth = 2;
  ctx.beginPath();
  items.forEach((item, index) => {
    const x = xForIndex(index);
    const y = valueToY(Number(item.change_pct ?? 0));
    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.stroke();

  const latestIndex = items.length - 1;
  ctx.fillStyle = values[latestIndex] >= 0 ? "#ff6b66" : "#2dd36f";
  ctx.beginPath();
  ctx.arc(xForIndex(latestIndex), valueToY(Number(items[latestIndex].change_pct ?? 0)), 3, 0, Math.PI * 2);
  ctx.fill();

  const labelIndexes = [0, Math.floor(items.length / 2), items.length - 1].filter(
    (value, index, array) => array.indexOf(value) === index
  );
  ctx.fillStyle = "#8ea0b8";
  labelIndexes.forEach((index) => {
    ctx.fillText(items[index].time || "", xForIndex(index) - 14, height - 6);
  });

  state.marketChartGeometry = {
    type: "market-line",
    margin,
    plotWidth,
    plotHeight,
    width,
    height,
    items,
    xForIndex,
    yForValue: valueToY,
  };

  if (Number.isInteger(state.marketChartHoverIndex) && state.marketChartHoverIndex < items.length) {
    const hoverItem = items[state.marketChartHoverIndex];
    const x = xForIndex(state.marketChartHoverIndex);
    const y = valueToY(Number(hoverItem.change_pct ?? 0));
    ctx.strokeStyle = "rgba(126, 231, 247, 0.3)";
    ctx.beginPath();
    ctx.moveTo(x, margin.top);
    ctx.lineTo(x, margin.top + plotHeight);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(margin.left, y);
    ctx.lineTo(margin.left + plotWidth, y);
    ctx.stroke();
  }
}

function drawGrid(ctx, margin, plotWidth, plotHeight, rows) {
  ctx.strokeStyle = "rgba(148, 163, 184, 0.18)";
  ctx.lineWidth = 1;
  for (let index = 0; index <= rows; index += 1) {
    const y = margin.top + (plotHeight / rows) * index;
    ctx.beginPath();
    ctx.moveTo(margin.left, y);
    ctx.lineTo(margin.left + plotWidth, y);
    ctx.stroke();
  }
}

function drawCandlesChart() {
  const setup = setupCanvas();
  if (!setup) {
    return;
  }

  const items = getVisibleChartItems();
  if (!items.length) {
    drawEmptyChart("暂无K线数据");
    return;
  }

  const { ctx, width, height } = setup;
  const margin = { top: 16, right: 18, bottom: 28, left: 56 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const highs = items.map((item) => Number(item.high ?? item.close ?? 0));
  const lows = items.map((item) => Number(item.low ?? item.close ?? 0));
  const maxPrice = Math.max(...highs);
  const minPrice = Math.min(...lows);
  const range = Math.max(maxPrice - minPrice, maxPrice * 0.02, 0.01);
  const stepX = items.length > 1 ? plotWidth / (items.length - 1) : plotWidth;
  const candleWidth = Math.max(4, Math.min(14, stepX * 0.62));
  const priceToY = (price) => margin.top + ((maxPrice - price) / range) * plotHeight;
  const xForIndex = (index) => margin.left + stepX * index;

  drawGrid(ctx, margin, plotWidth, plotHeight, 4);
  ctx.fillStyle = "#8ea0b8";
  ctx.font = "12px Segoe UI";
  for (let row = 0; row <= 4; row += 1) {
    const value = maxPrice - (range / 4) * row;
    const y = margin.top + (plotHeight / 4) * row;
    ctx.fillText(value.toFixed(2), 8, y + 4);
  }

  items.forEach((item, index) => {
    const open = Number(item.open ?? item.close ?? 0);
    const high = Number(item.high ?? item.close ?? 0);
    const low = Number(item.low ?? item.close ?? 0);
    const close = Number(item.close ?? 0);
    const rising = close >= open;
    const color = rising ? "#ff5b57" : "#22c55e";
    const x = xForIndex(index);

    ctx.strokeStyle = color;
    ctx.lineWidth = 1.1;
    ctx.beginPath();
    ctx.moveTo(x, priceToY(high));
    ctx.lineTo(x, priceToY(low));
    ctx.stroke();

    const bodyTop = priceToY(Math.max(open, close));
    const bodyBottom = priceToY(Math.min(open, close));
    const bodyHeight = Math.max(1.5, bodyBottom - bodyTop);
    ctx.fillStyle = color;
    ctx.fillRect(x - candleWidth / 2, bodyTop, candleWidth, bodyHeight);
  });

  const labelIndexes = [0, Math.floor(items.length / 2), items.length - 1].filter(
    (value, index, array) => array.indexOf(value) === index
  );
  ctx.fillStyle = "#8ea0b8";
  labelIndexes.forEach((index) => {
    const item = items[index];
    const label = item.time ? item.time : String(item.date || "").slice(5);
    ctx.fillText(label, xForIndex(index) - 18, height - 8);
  });

  state.chartGeometry = {
    type: "candles",
    margin,
    plotWidth,
    plotHeight,
    width,
    height,
    items,
    xForIndex,
    yForValue: priceToY,
  };

  if (Number.isInteger(state.chartHoverIndex) && state.chartHoverIndex < items.length) {
    drawCandleCrosshair(items[state.chartHoverIndex], state.chartHoverIndex);
  }
}

function drawCandleCrosshair(item, index) {
  const setup = setupCanvas();
  if (!setup || !state.chartGeometry) {
    drawCurrentChart();
    return;
  }
  drawCandlesChartBase(index, item);
}

function drawCandlesChartBase(index, item) {
  const setup = setupCanvas();
  if (!setup) {
    return;
  }
  const { ctx, width, height } = setup;
  const items = getVisibleChartItems();
  const margin = { top: 16, right: 18, bottom: 28, left: 56 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const highs = items.map((entry) => Number(entry.high ?? entry.close ?? 0));
  const lows = items.map((entry) => Number(entry.low ?? entry.close ?? 0));
  const maxPrice = Math.max(...highs);
  const minPrice = Math.min(...lows);
  const range = Math.max(maxPrice - minPrice, maxPrice * 0.02, 0.01);
  const stepX = items.length > 1 ? plotWidth / (items.length - 1) : plotWidth;
  const candleWidth = Math.max(4, Math.min(14, stepX * 0.62));
  const priceToY = (price) => margin.top + ((maxPrice - price) / range) * plotHeight;
  const xForIndex = (value) => margin.left + stepX * value;

  drawGrid(ctx, margin, plotWidth, plotHeight, 4);
  ctx.fillStyle = "#8ea0b8";
  ctx.font = "12px Segoe UI";
  for (let row = 0; row <= 4; row += 1) {
    const value = maxPrice - (range / 4) * row;
    const y = margin.top + (plotHeight / 4) * row;
    ctx.fillText(value.toFixed(2), 8, y + 4);
  }

  items.forEach((entry, itemIndex) => {
    const open = Number(entry.open ?? entry.close ?? 0);
    const high = Number(entry.high ?? entry.close ?? 0);
    const low = Number(entry.low ?? entry.close ?? 0);
    const close = Number(entry.close ?? 0);
    const rising = close >= open;
    const color = rising ? "#ff5b57" : "#22c55e";
    const x = xForIndex(itemIndex);

    ctx.strokeStyle = color;
    ctx.lineWidth = 1.1;
    ctx.beginPath();
    ctx.moveTo(x, priceToY(high));
    ctx.lineTo(x, priceToY(low));
    ctx.stroke();

    const bodyTop = priceToY(Math.max(open, close));
    const bodyBottom = priceToY(Math.min(open, close));
    const bodyHeight = Math.max(1.5, bodyBottom - bodyTop);
    ctx.fillStyle = color;
    ctx.fillRect(x - candleWidth / 2, bodyTop, candleWidth, bodyHeight);
  });

  const labelIndexes = [0, Math.floor(items.length / 2), items.length - 1].filter(
    (value, labelIndex, array) => array.indexOf(value) === labelIndex
  );
  ctx.fillStyle = "#8ea0b8";
  labelIndexes.forEach((value) => {
    const labelItem = items[value];
    const label = labelItem.time ? labelItem.time : String(labelItem.date || "").slice(5);
    ctx.fillText(label, xForIndex(value) - 18, height - 8);
  });

  if (item && Number.isInteger(index)) {
    const x = xForIndex(index);
    const y = priceToY(Number(item.close ?? 0));
    ctx.strokeStyle = "rgba(126, 231, 247, 0.35)";
    ctx.beginPath();
    ctx.moveTo(x, margin.top);
    ctx.lineTo(x, margin.top + plotHeight);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(margin.left, y);
    ctx.lineTo(margin.left + plotWidth, y);
    ctx.stroke();
  }

  state.chartGeometry = {
    type: "candles",
    margin,
    plotWidth,
    plotHeight,
    width,
    height,
    items,
    xForIndex,
    yForValue: priceToY,
  };
}

function drawIntradayLineChart() {
  const setup = setupCanvas();
  if (!setup) {
    return;
  }

  const items = getVisibleChartItems();
  if (!items.length) {
    drawEmptyChart("暂无当日涨跌线数据");
    return;
  }

  const { ctx, width, height } = setup;
  const margin = { top: 16, right: 18, bottom: 28, left: 56 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const values = items.map((item) => Number(item.change_pct ?? 0));
  const minValue = Math.min(...values, 0);
  const maxValue = Math.max(...values, 0);
  const range = Math.max(maxValue - minValue, 0.2);
  const stepX = items.length > 1 ? plotWidth / (items.length - 1) : plotWidth;
  const xForIndex = (index) => margin.left + stepX * index;
  const valueToY = (value) => margin.top + ((maxValue - value) / range) * plotHeight;

  drawGrid(ctx, margin, plotWidth, plotHeight, 4);
  const zeroY = valueToY(0);
  ctx.strokeStyle = "rgba(126, 231, 247, 0.35)";
  ctx.beginPath();
  ctx.moveTo(margin.left, zeroY);
  ctx.lineTo(margin.left + plotWidth, zeroY);
  ctx.stroke();

  ctx.fillStyle = "#8ea0b8";
  ctx.font = "12px Segoe UI";
  for (let row = 0; row <= 4; row += 1) {
    const value = maxValue - (range / 4) * row;
    const y = margin.top + (plotHeight / 4) * row;
    ctx.fillText(formatSignedPercent(value), 6, y + 4);
  }

  ctx.strokeStyle = "#67e8f9";
  ctx.lineWidth = 2.2;
  ctx.beginPath();
  items.forEach((item, index) => {
    const x = xForIndex(index);
    const y = valueToY(Number(item.change_pct ?? 0));
    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.stroke();

  items.forEach((item, index) => {
    const x = xForIndex(index);
    const y = valueToY(Number(item.change_pct ?? 0));
    ctx.fillStyle = Number(item.change_pct ?? 0) >= 0 ? "#ff5b57" : "#22c55e";
    ctx.beginPath();
    ctx.arc(x, y, 2.6, 0, Math.PI * 2);
    ctx.fill();
  });

  const labelIndexes = [0, Math.floor(items.length / 2), items.length - 1].filter(
    (value, index, array) => array.indexOf(value) === index
  );
  ctx.fillStyle = "#8ea0b8";
  labelIndexes.forEach((index) => {
    ctx.fillText(items[index].time || "", xForIndex(index) - 16, height - 8);
  });

  state.chartGeometry = {
    type: "intraday-line",
    margin,
    plotWidth,
    plotHeight,
    width,
    height,
    items,
    xForIndex,
    yForValue: valueToY,
  };

  if (Number.isInteger(state.chartHoverIndex) && state.chartHoverIndex < items.length) {
    const hoverItem = items[state.chartHoverIndex];
    const x = xForIndex(state.chartHoverIndex);
    const y = valueToY(Number(hoverItem.change_pct ?? 0));
    ctx.strokeStyle = "rgba(126, 231, 247, 0.35)";
    ctx.beginPath();
    ctx.moveTo(x, margin.top);
    ctx.lineTo(x, margin.top + plotHeight);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(margin.left, y);
    ctx.lineTo(margin.left + plotWidth, y);
    ctx.stroke();
  }
}

function positionTooltip(x, y) {
  if (!(historyTooltip instanceof HTMLElement) || !(historyChart instanceof HTMLCanvasElement)) {
    return;
  }
  const rect = historyChart.getBoundingClientRect();
  historyTooltip.hidden = false;
  historyTooltip.style.left = `${Math.min(x + 14, rect.width - 148)}px`;
  historyTooltip.style.top = `${Math.max(y - 72, 12)}px`;
}

function hideHistoryTooltip() {
  if (historyTooltip instanceof HTMLElement) {
    historyTooltip.hidden = true;
  }
}

function hideMarketTooltip() {
  if (marketTooltip instanceof HTMLElement) {
    marketTooltip.hidden = true;
  }
}

function positionMarketTooltip(x, y) {
  if (!(marketTooltip instanceof HTMLElement) || !(marketChart instanceof HTMLCanvasElement)) {
    return;
  }
  const rect = marketChart.getBoundingClientRect();
  marketTooltip.hidden = false;
  marketTooltip.style.left = `${Math.min(x + 12, rect.width - 150)}px`;
  marketTooltip.style.top = `${Math.max(y - 64, 8)}px`;
}

function renderTooltipForIndex(index, clientX, clientY) {
  if (!state.chartGeometry || !(historyTooltip instanceof HTMLElement) || !(historyChart instanceof HTMLCanvasElement)) {
    return;
  }
  const item = state.chartGeometry.items[index];
  if (!item) {
    hideHistoryTooltip();
    return;
  }

  state.chartHoverIndex = index;
  drawCurrentChart();

  if (state.chartGeometry.type === "candles") {
    const change = formatSignedPercent(item.change_pct);
    historyTooltip.innerHTML = `
      <div>${item.datetime || item.date}</div>
      <div>开 ${formatNumber(item.open)}</div>
      <div>高 ${formatNumber(item.high)} 低 ${formatNumber(item.low)}</div>
      <div>收 ${formatNumber(item.close)} 涨幅 ${change}</div>
    `;
    const x = state.chartGeometry.xForIndex(index);
    const y = state.chartGeometry.yForValue(Number(item.close ?? 0));
    positionTooltip(x, y);
    return;
  }

  historyTooltip.innerHTML = `
    <div>${state.intradayPayload?.date || ""} ${item.time || ""}</div>
    <div>价格 ${formatNumber(item.price)}</div>
    <div>涨幅 ${formatSignedPercent(item.change_pct)}</div>
  `;
  const x = state.chartGeometry.xForIndex(index);
  const y = state.chartGeometry.yForValue(Number(item.change_pct ?? 0));
  positionTooltip(x, y);
}

function handleChartHover(event) {
  if (!state.chartGeometry || !state.chartGeometry.items.length || !(historyChart instanceof HTMLCanvasElement)) {
    hideHistoryTooltip();
    return;
  }

  const rect = historyChart.getBoundingClientRect();
  const offsetX = event.clientX - rect.left;
  const margin = state.chartGeometry.margin;
  if (offsetX < margin.left - 8 || offsetX > state.chartGeometry.width - margin.right + 8) {
    hideHistoryTooltip();
    return;
  }

  const relative = Math.max(0, Math.min(state.chartGeometry.plotWidth, offsetX - margin.left));
  const stepX = state.chartGeometry.items.length > 1 ? state.chartGeometry.plotWidth / (state.chartGeometry.items.length - 1) : 1;
  const index = Math.max(0, Math.min(state.chartGeometry.items.length - 1, Math.round(relative / stepX)));
  renderTooltipForIndex(index, event.clientX, event.clientY);
}

function renderMarketTooltipForIndex(index) {
  if (!state.marketChartGeometry || !(marketTooltip instanceof HTMLElement)) {
    return;
  }
  const item = state.marketChartGeometry.items[index];
  if (!item) {
    hideMarketTooltip();
    return;
  }
  state.marketChartHoverIndex = index;
  drawMarketChart();
  marketTooltip.innerHTML = `
    <div>${state.marketOverview?.shanghai?.trade_date || ""} ${item.time || ""}</div>
    <div>价格 ${formatNumber(item.price, 3)}</div>
    <div>涨幅 ${formatSignedPercent(item.change_pct)}</div>
  `;
  positionMarketTooltip(
    state.marketChartGeometry.xForIndex(index),
    state.marketChartGeometry.yForValue(Number(item.change_pct ?? 0))
  );
}

function handleMarketChartHover(event) {
  if (!state.marketChartGeometry || !state.marketChartGeometry.items.length || !(marketChart instanceof HTMLCanvasElement)) {
    hideMarketTooltip();
    return;
  }
  const rect = marketChart.getBoundingClientRect();
  const offsetX = event.clientX - rect.left;
  const margin = state.marketChartGeometry.margin;
  if (offsetX < margin.left - 6 || offsetX > state.marketChartGeometry.width - margin.right + 6) {
    hideMarketTooltip();
    return;
  }
  const relative = Math.max(0, Math.min(state.marketChartGeometry.plotWidth, offsetX - margin.left));
  const stepX =
    state.marketChartGeometry.items.length > 1
      ? state.marketChartGeometry.plotWidth / (state.marketChartGeometry.items.length - 1)
      : 1;
  const index = Math.max(0, Math.min(state.marketChartGeometry.items.length - 1, Math.round(relative / stepX)));
  renderMarketTooltipForIndex(index);
}

function applyToneText(element, value, digits = 2, withPercent = false, withSign = false) {
  if (!(element instanceof HTMLElement)) {
    return;
  }
  element.classList.remove("market-up", "market-down", "market-flat");
  element.classList.add(getToneClassName(value));
  if (value == null || Number.isNaN(Number(value))) {
    element.textContent = "-";
    return;
  }
  const numeric = Number(value);
  const prefix = withSign && numeric > 0 ? "+" : "";
  element.textContent = `${prefix}${numeric.toFixed(digits)}${withPercent ? "%" : ""}`;
}

function normalizeShanghaiOverview(shanghai) {
  if (!shanghai || typeof shanghai !== "object") {
    return shanghai;
  }

  const normalized = { ...shanghai };
  const previousClose =
    Number.isFinite(Number(normalized.prev_close)) && Number(normalized.prev_close) !== 0
      ? Number(normalized.prev_close)
      : null;
  const openPrice =
    Number.isFinite(Number(normalized.open)) && Number(normalized.open) !== 0 ? Number(normalized.open) : null;
  const currentPrice = Number.isFinite(Number(normalized.current)) ? Number(normalized.current) : null;
  const baseline = previousClose ?? openPrice;

  if (baseline != null && currentPrice != null) {
    normalized.change = Number((currentPrice - baseline).toFixed(2));
    normalized.change_pct = Number((((currentPrice / baseline) - 1) * 100).toFixed(2));
  }

  if (Array.isArray(normalized.items) && baseline != null) {
    normalized.items = normalized.items.map((item) => {
      const price = Number(item?.price);
      if (!Number.isFinite(price) || baseline === 0) {
        return item;
      }
      return {
        ...item,
        change_pct: Number((((price / baseline) - 1) * 100).toFixed(2)),
      };
    });
  }

  return normalized;
}

function renderMarketOverview(payload) {
  const normalizedPayload = {
    ...(payload || {}),
    shanghai: normalizeShanghaiOverview(payload?.shanghai),
  };

  state.marketOverview = normalizedPayload;
  state.marketChartItems = normalizedPayload?.shanghai?.items || [];
  resetMarketChartViewport();
  drawMarketChart();

  if (marketUpdatedAt instanceof HTMLElement) {
    marketUpdatedAt.textContent = formatDateTime(normalizedPayload?.updated_at);
  }

  if (marketShanghaiDate instanceof HTMLElement) {
    marketShanghaiDate.textContent = normalizedPayload?.shanghai?.trade_date
      ? `${normalizedPayload.shanghai.trade_date} 当日分时`
      : "当日分时";
  }

  if (marketOpen instanceof HTMLElement) {
    marketOpen.textContent = formatNumber(normalizedPayload?.shanghai?.open, 3);
  }
  if (marketCurrent instanceof HTMLElement) {
    marketCurrent.textContent = formatNumber(normalizedPayload?.shanghai?.current, 3);
  }
  applyToneText(marketChange, normalizedPayload?.shanghai?.change, 2, false, true);
  applyToneText(marketChangePct, normalizedPayload?.shanghai?.change_pct, 2, true, true);

  applyToneText(marketNasdaqPct, normalizedPayload?.nasdaq_previous?.change_pct, 2, true, true);
  if (marketNasdaqMeta instanceof HTMLElement) {
    const metaParts = [];
    if (normalizedPayload?.nasdaq_previous?.trade_date) {
      metaParts.push(normalizedPayload.nasdaq_previous.trade_date);
    }
    if (normalizedPayload?.nasdaq_previous?.close != null) {
      metaParts.push(`收 ${formatNumber(normalizedPayload.nasdaq_previous.close)}`);
    }
    marketNasdaqMeta.textContent = metaParts.join(" | ") || "-";
  }
  if (marketNasdaqCard instanceof HTMLElement) {
    marketNasdaqCard.classList.remove("market-up", "market-down", "market-flat");
    marketNasdaqCard.classList.add(getToneClassName(normalizedPayload?.nasdaq_previous?.change_pct));
  }

  if (homeUsLeaderList instanceof HTMLElement) {
    const items = normalizedPayload?.us_industry_leaders || normalizedPayload?.us_sector_leaders || [];
    homeUsLeaderList.innerHTML = items.length
      ? items
          .map(
            (item) => {
              const extraParts = [];
              if (item.trade_date) {
                extraParts.push(item.trade_date);
              }
              if (item.leader_name) {
                const leaderTone = item.leader_change_pct != null ? formatSignedPercent(item.leader_change_pct) : "-";
                extraParts.push(`领涨股 ${item.leader_name} ${leaderTone}`);
              } else if (item.sector || item.name_en) {
                extraParts.push(item.sector || item.name_en);
              }
              if (item.source) {
                extraParts.push("同花顺聚合");
              }
              return `
              <div class="market-sector-row">
                <div class="market-sector-rank">${item.stocks ?? "-"}</div>
                <div class="market-sector-main">
                  <div class="market-sector-name">${item.name}</div>
                  <div class="market-sector-extra">${extraParts.join(" | ") || "-"}</div>
                </div>
                <div class="market-sector-change ${getToneClassName(item.change_pct)}">${formatSignedPercent(item.change_pct)}</div>
              </div>
            `;
            }
          )
          .join("")
      : `<div class="placeholder-row">暂无美股板块数据</div>`;
  }
}

function updateHistoryHeader() {
  if (!historyTitle || !historyBadge) {
    return;
  }

  if (state.activeChartMode === "intraday-line" && state.intradayPayload) {
    const name = state.intradayPayload.name || state.currentHistoryName || state.currentHistorySymbol;
    historyBadge.textContent = `${name} ${state.intradayPayload.date}`;
    historyTitle.textContent = `${name} ${state.intradayPayload.date} 当日涨跌图`;
    return;
  }

  const name = state.historyPayload?.name || state.currentHistoryName || state.currentHistorySymbol;
  historyBadge.textContent = name;
  historyTitle.textContent = `${name} ${periodLabelMap[state.selectedPeriod] || state.selectedPeriod} 历史回看`;
}

function renderHistoryTable() {
  if (!historyTable) {
    return;
  }

  if (state.activeChartMode === "intraday-line" && state.intradayPayload) {
    const rows = (state.intradayPayload.items || []).slice().reverse().slice(0, 80);
    historyTable.innerHTML = rows.length
      ? rows
          .map(
            (item) => `
              <tr class="${getToneClass(item.change_pct)}">
                <td>${state.intradayPayload.date} ${item.time}</td>
                <td>${formatNumber(state.intradayPayload.baseline)}</td>
                <td>${formatNumber(item.price)}</td>
                <td>${formatNumber(item.price)}</td>
                <td>${formatNumber(item.price)}</td>
                <td>${formatSignedPercent(item.change_pct)}</td>
              </tr>
            `
          )
          .join("")
      : `<tr><td colspan="6">${state.intradayPayload.message || "暂无当日涨跌图数据"}</td></tr>`;
    return;
  }

  const items = state.historyPayload?.items || [];
  if (!items.length) {
    historyTable.innerHTML = `<tr><td colspan="6">暂无数据</td></tr>`;
    return;
  }

  const rows = items.slice().reverse().slice(0, 24);
  historyTable.innerHTML = rows
    .map((item) => {
      const dateCell =
        state.selectedPeriod === "day" && item.date
          ? `<button class="date-link" data-trade-date="${item.date}" type="button">${item.date}</button>`
          : item.time
            ? `${item.date} ${item.time}`
            : item.date;
      return `
        <tr class="${getToneClass(item.change_pct)}">
          <td>${dateCell}</td>
          <td>${formatNumber(item.open)}</td>
          <td>${formatNumber(item.high)}</td>
          <td>${formatNumber(item.low)}</td>
          <td>${formatNumber(item.close)}</td>
          <td>${formatSignedPercent(item.change_pct)}</td>
        </tr>
      `;
    })
    .join("");
}

function renderHistoryPayload(payload) {
  state.historyPayload = payload;
  state.previousHistoryPayload = payload;
  state.currentHistorySymbol = payload.symbol || state.currentHistorySymbol;
  state.currentHistoryName = payload.name || state.currentHistoryName;
  state.activeChartMode = "candles";
  state.intradayPayload = null;
  state.chartItems = payload.items || [];
  resetChartViewport();
  historyBackBtn && (historyBackBtn.hidden = true);
  updateHistoryHeader();
  renderHistoryTable();
  drawCurrentChart();
}

function renderIntradayPayload(payload) {
  state.intradayPayload = payload;
  state.activeChartMode = "intraday-line";
  state.chartItems = payload.items || [];
  resetChartViewport();
  historyBackBtn && (historyBackBtn.hidden = false);
  updateHistoryHeader();
  renderHistoryTable();
  drawCurrentChart();
}

async function loadDashboard() {
  const [overview, picks] = await Promise.all([
    fetchJson(`/api/overview?source=${defaultSource}`),
    fetchJson(`/api/picks?limit=${defaultPicksLimit}&source=${defaultSource}`),
  ]);

  renderCards(overview);
  renderPicks(picks.items || []);

  if (overview.trained_now && overview.training_metrics) {
    setStatus(`首次加载时自动完成训练。\n${JSON.stringify(overview.training_metrics, null, 2)}`);
  } else {
    setStatus(`页面已刷新，当前使用 ${overview.data_source === "real" ? "本地真实数据" : "样例数据"} 进行打分。`);
  }
}

async function loadWatchlist() {
  const payload = await fetchJson(`/api/watchlist?limit=${defaultWatchLimit}&source=real`);
  renderWatch(payload.items || []);
}

async function loadFavorites() {
  const payload = await fetchJson("/api/favorites");
  renderWatchlist(payload.items || [], payload.updated_at);
}

async function loadMarketOverview() {
  const payload = await fetchJson("/api/market-overview?limit=6");
  renderMarketOverview(payload);
}

function startMarketPolling() {
  stopMarketPolling();
  state.marketPollTimer = window.setInterval(() => {
    loadMarketOverview().catch(() => {});
  }, 45000);
}

async function loadHistory(symbol, period = state.selectedPeriod) {
  state.currentHistorySymbol = symbol;
  state.selectedPeriod = period;
  setActivePeriodButton(period);
  const limit = periodLimitMap[period] || 120;
  const payload = await fetchJson(`/api/history/${symbol}?period=${encodeURIComponent(period)}&limit=${limit}`);
  renderHistoryPayload(payload);
  return payload;
}

async function loadIntradayHistory(symbol, tradeDate) {
  const payload = await fetchJson(`/api/watch-intraday/${symbol}?trade_date=${encodeURIComponent(tradeDate)}`);
  renderIntradayPayload(payload);
  return payload;
}

async function searchStocks(query) {
  const keyword = query.trim();
  if (!keyword) {
    if (searchResults) {
      searchResults.innerHTML = "";
    }
    return;
  }
  const payload = await fetchJson(`/api/search?query=${encodeURIComponent(keyword)}&limit=12`);
  renderSearchResults(payload.items || []);
}

async function addFavorite(symbol, name, kind) {
  await fetchJson("/api/favorites", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol, name, kind }),
  });
  await loadFavorites();
  if (stockSearchInput instanceof HTMLInputElement && stockSearchInput.value.trim()) {
    await searchStocks(stockSearchInput.value);
  }
}

async function removeFavorite(symbol, kind) {
  await fetchJson(`/api/favorites/${encodeURIComponent(symbol)}?kind=${encodeURIComponent(kind || "stock")}`, {
    method: "DELETE",
  });
  await loadFavorites();
  if (stockSearchInput instanceof HTMLInputElement && stockSearchInput.value.trim()) {
    await searchStocks(stockSearchInput.value);
  }
}

async function initializeDashboard() {
  setStatus("正在加载候选股、实时盯盘、自选股与历史回看...");
  await Promise.all([
    loadDashboard(),
    loadWatchlist(),
    loadFavorites(),
    loadHistory(state.currentHistorySymbol),
    loadMarketOverview(),
    syncRefreshStatus(),
  ]);
}

async function retrain() {
  setStatus("正在重新训练模型...");
  if (trainBtn) {
    trainBtn.disabled = true;
  }
  try {
    const payload = await fetchJson(`/api/train?source=${defaultSource}`, { method: "POST" });
    setStatus(`${payload.message}\n${JSON.stringify(payload.metrics, null, 2)}`);
    await initializeDashboard();
  } finally {
    if (trainBtn) {
      trainBtn.disabled = false;
    }
  }
}

async function refreshRealData() {
  setStatus("正在启动真实数据后台刷新任务...");
  if (syncBtn) {
    syncBtn.disabled = true;
  }
  try {
    const payload = await fetchJson(`/api/refresh-real-data?pool=${defaultPool}`, { method: "POST" });
    renderTaskStatus(payload.status);
    setStatus(`${payload.message}\n请等待后台脚本完成抓取和训练。`);
    if (payload.status?.state === "running") {
      startRefreshPolling();
    }
  } finally {
    if (syncBtn) {
      syncBtn.disabled = false;
    }
  }
}

function handleHistoryJump(symbol, name) {
  loadHistory(symbol, state.selectedPeriod)
    .then(() => {
      setStatus(`已切换到 ${symbol}${name ? ` ${name}` : ""} 的历史回看。`);
    })
    .catch((error) => {
      setStatus(`历史回看加载失败: ${error.message}`);
    });
}

refreshBtn?.addEventListener("click", () => {
  loadDashboard().catch((error) => {
    setStatus(`候选股刷新失败: ${error.message}`);
  });
});

watchBtn?.addEventListener("click", () => {
  loadWatchlist()
    .then(() => setStatus("盯盘快照已刷新。"))
    .catch((error) => {
      setStatus(`盯盘快照刷新失败: ${error.message}`);
    });
});

trainBtn?.addEventListener("click", () => {
  retrain().catch((error) => {
    setStatus(`训练失败: ${error.message}`);
  });
});

syncBtn?.addEventListener("click", () => {
  refreshRealData().catch((error) => {
    setStatus(`真实数据后台刷新失败: ${error.message}`);
  });
});

picksTable?.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }
  const button = target.closest("[data-action='view']");
  if (!(button instanceof HTMLElement) || !button.dataset.symbol) {
    return;
  }
  handleHistoryJump(button.dataset.symbol, button.dataset.name || "");
});

watchTable?.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }
  const button = target.closest("[data-action='view']");
  if (!(button instanceof HTMLElement) || !button.dataset.symbol) {
    return;
  }
  handleHistoryJump(button.dataset.symbol, button.dataset.name || "");
});

watchlistTable?.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }

  const viewButton = target.closest("[data-action='view']");
  if (viewButton instanceof HTMLElement && viewButton.dataset.symbol) {
    handleHistoryJump(viewButton.dataset.symbol, viewButton.dataset.name || "");
    return;
  }

  const removeButton = target.closest("[data-action='remove-favorite']");
  if (removeButton instanceof HTMLElement && removeButton.dataset.symbol) {
    removeFavorite(removeButton.dataset.symbol, removeButton.dataset.kind)
      .then(() => setStatus(`已从自选中移除 ${removeButton.dataset.symbol}。`))
      .catch((error) => {
        setStatus(`移除自选失败: ${error.message}`);
      });
  }
});

historyTable?.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }
  const button = target.closest("[data-trade-date]");
  if (!(button instanceof HTMLElement) || !button.dataset.tradeDate) {
    return;
  }
  loadIntradayHistory(state.currentHistorySymbol, button.dataset.tradeDate)
    .then((payload) => {
      setStatus(payload.message || `已切换到 ${button.dataset.tradeDate} 的当日涨跌图。`);
    })
    .catch((error) => {
      setStatus(`当日涨跌图加载失败: ${error.message}`);
    });
});

stockSearchInput?.addEventListener("input", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLInputElement)) {
    return;
  }
  if (state.searchTimer) {
    window.clearTimeout(state.searchTimer);
  }
  state.searchTimer = window.setTimeout(() => {
    searchStocks(target.value).catch((error) => {
      setStatus(`搜索失败: ${error.message}`);
    });
  }, 180);
});

searchResults?.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }

  const viewButton = target.closest("[data-action='view-search']");
  if (viewButton instanceof HTMLElement && viewButton.dataset.symbol) {
    loadHistory(viewButton.dataset.symbol, state.selectedPeriod)
      .then(() => {
        setStatus(`已切换到 ${viewButton.dataset.symbol} 的历史回看。`);
      })
      .catch((error) => {
        setStatus(`历史回看切换失败: ${error.message}`);
      });
    return;
  }

  const addButton = target.closest("[data-action='add-favorite']");
  if (addButton instanceof HTMLElement && addButton.dataset.symbol) {
    addFavorite(addButton.dataset.symbol, addButton.dataset.name || "", addButton.dataset.kind || "stock")
      .then(() => {
        setStatus(`已添加 ${addButton.dataset.symbol} 到自选股票。`);
      })
      .catch((error) => {
        setStatus(`添加自选失败: ${error.message}`);
      });
  }
});

navItems.forEach((item) => {
  item.addEventListener("click", () => {
    if (item.dataset.page) {
      switchPage(item.dataset.page);
    }
  });
});

historyPeriodTabs?.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }
  const button = target.closest("[data-period]");
  if (!(button instanceof HTMLElement) || !button.dataset.period) {
    return;
  }
  loadHistory(state.currentHistorySymbol, button.dataset.period)
    .then(() => {
      setStatus(`已切换到 ${periodLabelMap[button.dataset.period] || button.dataset.period}。`);
    })
    .catch((error) => {
      setStatus(`切换周期失败: ${error.message}`);
    });
});

historyBackBtn?.addEventListener("click", () => {
  if (state.previousHistoryPayload) {
    renderHistoryPayload(state.previousHistoryPayload);
    setStatus("已返回K线图。");
  }
});

historyExpandBtn?.addEventListener("click", () => {
  toggleHistoryExpanded();
});

historyZoomInBtn?.addEventListener("click", () => {
  zoomChart(0.85, 0.8);
});

historyZoomOutBtn?.addEventListener("click", () => {
  zoomChart(1.18, 0.8);
});

historyZoomResetBtn?.addEventListener("click", () => {
  resetChartViewport();
  drawCurrentChart();
  setStatus("图表缩放已重置。");
});

marketZoomInBtn?.addEventListener("click", () => {
  zoomMarketChart(0.85, 0.8);
});

marketZoomOutBtn?.addEventListener("click", () => {
  zoomMarketChart(1.18, 0.8);
});

marketZoomResetBtn?.addEventListener("click", () => {
  resetMarketChartViewport();
  drawMarketChart();
});

historyChart?.addEventListener("mousemove", (event) => {
  handleChartHover(event);
});

historyChart?.addEventListener("mouseleave", () => {
  state.chartHoverIndex = null;
  hideHistoryTooltip();
  drawCurrentChart();
});

historyChart?.addEventListener("wheel", (event) => {
  applyMouseWheelZoom(event);
});

marketChart?.addEventListener("mousemove", (event) => {
  handleMarketChartHover(event);
});

marketChart?.addEventListener("mouseleave", () => {
  state.marketChartHoverIndex = null;
  hideMarketTooltip();
  drawMarketChart();
});

marketChart?.addEventListener("wheel", (event) => {
  applyMarketMouseWheelZoom(event);
});

window.addEventListener("resize", () => {
  drawCurrentChart();
  drawMarketChart();
});

syncHistoryLayout();
startMarketPolling();

initializeDashboard()
  .then(async () => {
    const status = await syncRefreshStatus();
    if (status.state === "running") {
      setStatus("检测到后台刷新任务仍在运行，正在持续轮询状态...");
      startRefreshPolling();
    }
  })
  .catch((error) => {
    setStatus(`初始化失败: ${error.message}`);
  });
