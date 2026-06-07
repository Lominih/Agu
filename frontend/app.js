const overviewCards = document.querySelector("#overviewCards");
const modelMetricsCards = document.querySelector("#modelMetricsCards");
const picksTable = document.querySelector("#picksTable");
const watchTable = document.querySelector("#watchTable");
const watchlistTable = document.querySelector("#watchlistTable");
const watchlistSummary = document.querySelector("#watchlistSummary");
const historyTable = document.querySelector("#historyTable");
const historyTitle = document.querySelector("#historyTitle");
const historyMeta = document.querySelector("#historyMeta");
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
const marketWarnings = document.querySelector("#marketWarnings");
const marketNasdaqCard = document.querySelector("#marketNasdaqCard");
const marketNasdaqPct = document.querySelector("#marketNasdaqPct");
const marketNasdaqMeta = document.querySelector("#marketNasdaqMeta");
const marketShanghaiDate = document.querySelector("#marketShanghaiDate");
const marketOpen = document.querySelector("#marketOpen");
const marketCurrent = document.querySelector("#marketCurrent");
const marketChange = document.querySelector("#marketChange");
const marketChangePct = document.querySelector("#marketChangePct");
const hotNewsList = document.querySelector("#hotNewsList");
const hotNewsScroll = hotNewsList?.closest(".hot-news-scroll");
const hotNewsPageMeta = document.querySelector("#hotNewsPageMeta");
const hotNewsFilters = document.querySelector("#hotNewsFilters");
const hotNewsRefreshBtnPage = document.querySelector("#hotNewsRefreshBtnPage");
const hotNewsLoadMoreHint = document.querySelector("#hotNewsLoadMoreHint");
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
const portfolioSummaryCards = document.querySelector("#portfolioSummaryCards");
const portfolioMeta = document.querySelector("#portfolioMeta");
const portfolioPositionsTable = document.querySelector("#portfolioPositionsTable");
const portfolioTradesTable = document.querySelector("#portfolioTradesTable");
const portfolioForm = document.querySelector("#portfolioForm");
const portfolioSettingsForm = document.querySelector("#portfolioSettingsForm");
const portfolioResetBtn = document.querySelector("#portfolioResetBtn");
const portfolioExportBtn = document.querySelector("#portfolioExportBtn");
const portfolioImportBtn = document.querySelector("#portfolioImportBtn");
const portfolioImportFile = document.querySelector("#portfolioImportFile");
const portfolioSymbol = document.querySelector("#portfolioSymbol");
const portfolioName = document.querySelector("#portfolioName");
const portfolioSide = document.querySelector("#portfolioSide");
const portfolioQty = document.querySelector("#portfolioQty");
const portfolioPriceMode = document.querySelector("#portfolioPriceMode");
const portfolioPrice = document.querySelector("#portfolioPrice");
const portfolioCommissionRate = document.querySelector("#portfolioCommissionRate");
const portfolioMinCommission = document.querySelector("#portfolioMinCommission");
const portfolioStampDutyRate = document.querySelector("#portfolioStampDutyRate");
const portfolioSlippageBps = document.querySelector("#portfolioSlippageBps");
const screenList = document.querySelector("#screenList");
const rotationList = document.querySelector("#rotationList");
const prepostList = document.querySelector("#prepostList");
const stockAnalysisResult = document.querySelector("#stockAnalysisResult");
const timelineSymbolInput = document.querySelector("#timelineSymbolInput");
const alertsList = document.querySelector("#alertsList");
const toastStack = document.querySelector("#toastStack");
const backtestChart = document.querySelector("#backtestChart");
const backtestAggregate = document.querySelector("#backtestAggregate");
const backtestWindows = document.querySelector("#backtestWindows");
const backtestRunBtn = document.querySelector("#backtestRunBtn");
const backtestStatus = document.querySelector("#backtestStatus");
const backtestTrainWindow = document.querySelector("#backtestTrainWindow");
const backtestTestWindow = document.querySelector("#backtestTestWindow");
const backtestTopN = document.querySelector("#backtestTopN");


const defaultSource = "real";
const defaultPool = "hs300";
const defaultPicksLimit = 18;
const defaultWatchLimit = 20;
const hotNewsPageSize = 24;

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
  searchSeq: 0,
  historySeq: 0,
  picks: [],
  watch: [],
  favorites: [],
  portfolio: null,
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
  hotNews: [],
  hotNewsOffset: 0,
  hotNewsTotal: 0,
  hotNewsHasMore: true,
  hotNewsLoading: false,
  hotNewsCategory: "all",
  hotNewsAvailableCategories: {
    all: "全部",
    tech: "科技",
    finance: "金融",
    new_energy: "新能源",
    medicine: "医药",
    infrastructure: "地产基建",
    resources: "资源",
  },
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

function pushToast(message, tone = "success") {
  if (!(toastStack instanceof HTMLElement) || !message) {
    return;
  }
  const toast = document.createElement("div");
  toast.className = `toast toast-${tone}`;
  toast.textContent = message;
  toastStack.appendChild(toast);
  window.setTimeout(() => {
    toast.classList.add("is-visible");
  }, 10);
  window.setTimeout(() => {
    toast.classList.remove("is-visible");
    window.setTimeout(() => toast.remove(), 220);
  }, 2600);
}

function switchPage(pageName) {
  navItems.forEach((item) => {
    item.classList.toggle("active", item.dataset.page === pageName);
  });
  pages.forEach((page) => {
    page.classList.toggle("active", page.dataset.page === pageName);
  });
  const activePage = document.querySelector(`.page[data-page="${pageName}"]`);
  const removeLoading = () => { if (activePage) activePage.classList.remove("page-loading"); };
  if (activePage) activePage.classList.add("page-loading");
  if (pageName === "portfolio") {
    loadPortfolio().catch(() => {}).finally(removeLoading);
  } else if (pageName === "screen") {
    loadScreen().catch((error) => setStatus(`条件选股加载失败: ${error.message}`)).finally(removeLoading);
  } else if (pageName === "rotation") {
    loadRotation().catch((error) => setStatus(`行业轮动加载失败: ${error.message}`)).finally(removeLoading);
  } else if (pageName === "prepost") {
    loadPrePost().catch((error) => setStatus(`盘前盘后加载失败: ${error.message}`)).finally(removeLoading);
  } else if (pageName === "backtest") {
    loadBacktest().catch((error) => setStatus(`滚动回测加载失败: ${error.message}`)).finally(removeLoading);
  } else if (pageName === "alerts") {
    loadAlerts().catch((error) => setStatus(`预警加载失败: ${error.message}`)).finally(removeLoading);
  } else {
    removeLoading();
  }
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
  window.setTimeout(() => drawCurrentChart(), 30);
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

function formatCurrency(value) {
  if (value == null || Number.isNaN(Number(value))) {
    return "-";
  }
  return `￥${Number(value).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatPercent(value, digits = 2) {
  if (value == null || Number.isNaN(Number(value))) {
    return "-";
  }
  return `${Number(value).toFixed(digits)}%`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
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

function getHotNewsCategoryLabel(category = state.hotNewsCategory) {
  return state.hotNewsAvailableCategories?.[category] || "全部";
}

function setMetaStrip(element, text, tone = "neutral") {
  if (!(element instanceof HTMLElement)) {
    return;
  }
  element.textContent = text || "暂无状态";
  element.classList.remove("is-positive", "is-negative", "is-warning");
  if (tone === "positive") {
    element.classList.add("is-positive");
  } else if (tone === "negative") {
    element.classList.add("is-negative");
  } else if (tone === "warning") {
    element.classList.add("is-warning");
  }
}

function syncPortfolioPriceMode() {
  if (!(portfolioPriceMode instanceof HTMLSelectElement) || !(portfolioPrice instanceof HTMLInputElement)) {
    return;
  }
  const isManual = portfolioPriceMode.value === "manual";
  portfolioPrice.disabled = !isManual;
  portfolioPrice.required = isManual;
  portfolioPrice.placeholder = isManual ? "仅手工价时填写" : "手工价仅在手工模式下生效";
}

function buildPortfolioExportFilename(exportedAt) {
  const stamp = exportedAt ? new Date(exportedAt) : new Date();
  if (Number.isNaN(stamp.getTime())) {
    return "paper-portfolio-export.json";
  }
  return `paper-portfolio-export-${stamp.toISOString().replace(/[:.]/g, "-")}.json`;
}

function downloadJsonFile(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

function readJsonFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        resolve(JSON.parse(String(reader.result || "")));
      } catch (error) {
        reject(error);
      }
    };
    reader.onerror = () => reject(reader.error || new Error("读取文件失败"));
    reader.readAsText(file, "utf-8");
  });
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
  if (status.message) parts.push(status.message);
  if (status.pool) parts.push(`股票池: ${status.pool}`);
  if (status.rows) parts.push(`样本行数: ${status.rows}`);
  if (status.symbols) parts.push(`股票数量: ${status.symbols}`);
  if (status.error) parts.push(`错误: ${status.error}`);
  lastRefreshResult.textContent = parts.join(" | ") || "暂无";
  syncBtn.disabled = status.state === "running";
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
  const dataHealth = overview?.data_health || {};
  const healthSummary = dataHealth.summary || {};
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
    {
      label: "数据健康",
      value: dataHealth.status === "healthy" ? "正常" : dataHealth.status === "warn" ? "需检查" : "未知",
      hint: healthSummary.latest_date ? `最新数据 ${healthSummary.latest_date} | 问题 ${dataHealth.issues?.length || 0} 项` : "等待数据健康报告",
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

function renderModelMetrics(overview) {
  if (!(modelMetricsCards instanceof HTMLElement)) {
    return;
  }
  const meta = overview?.model_meta || {};
  const metrics = meta.metrics || overview?.training_metrics || {};
  const backtest = meta.backtest || metrics.backtest || {};
  const rolling = metrics.rolling_backtest || meta.metrics?.rolling_backtest || {};
  const version = meta.version || (Array.isArray(meta.history) && meta.history.length ? meta.history[meta.history.length - 1].version : "-");
  const cards = [
    {
      label: "模型版本",
      value: version || "-",
      hint: "每次训练都会写入一个可追踪版本号",
    },
    {
      label: "测试集 R²",
      value: metrics.test_r2 != null ? Number(metrics.test_r2).toFixed(4) : "-",
      hint: "越高越好，用于观察回归拟合能力",
    },
    {
      label: "方向命中率",
      value: metrics.direction_accuracy != null ? formatSignedPercent(Number(metrics.direction_accuracy) * 100) : "-",
      hint: "预测涨跌方向与真实方向一致的比例",
    },
    {
      label: "Top10 超额收益",
      value: backtest.excess_return_5 != null ? formatSignedPercent(Number(backtest.excess_return_5) * 100) : "-",
      hint: "按测试阶段每天选 Top10 后的平均 5 日超额收益",
    },
    {
      label: "Top10 胜率",
      value: backtest.hit_rate != null ? formatSignedPercent(Number(backtest.hit_rate) * 100) : "-",
      hint: "测试阶段 Top10 候选中未来 5 日为正收益的平均比例",
    },
    {
      label: "滚动年化",
      value: rolling.annualized_return != null ? formatSignedPercent(Number(rolling.annualized_return) * 100) : "-",
      hint: "按滚动测试区间估算的策略年化收益",
    },
    {
      label: "最大回撤",
      value: rolling.max_drawdown != null ? formatSignedPercent(Number(rolling.max_drawdown) * 100) : "-",
      hint: "滚动测试区间内的最大回撤",
    },
    {
      label: "Sharpe",
      value: rolling.sharpe != null ? Number(rolling.sharpe).toFixed(3) : "-",
      hint: "滚动测试区间的收益风险比",
    },
    {
      label: "RankIC",
      value: rolling.rank_ic != null ? Number(rolling.rank_ic).toFixed(3) : "-",
      hint: "预测排序与未来收益排序的一致性",
    },
  ];
  modelMetricsCards.innerHTML = cards
    .map(
      (card) => `
        <article class="card card-compact">
          <div class="label">${card.label}</div>
          <div class="value">${card.value}</div>
          <div class="hint">${card.hint}</div>
        </article>
      `
    )
    .join("");
}

function renderPicks(items) {
  state.picks = items;
  if (!picksTable) {
    return;
  }
  picksTable.innerHTML = items
    .map((item) => {
      const reasonTags = Array.isArray(item.reason_tags) ? item.reason_tags : [];
      const reasonTexts = Array.isArray(item.reason_texts) ? item.reason_texts : [];
      const basisItems = Array.isArray(item.basis_items) ? item.basis_items : [];
      const riskTexts = Array.isArray(item.risk_texts) ? item.risk_texts : [];
      const confidenceScore = item.confidence_score != null ? Math.round(Number(item.confidence_score) * 100) : null;
      const riskScore = item.risk_score != null ? Math.round(Number(item.risk_score) * 100) : null;
      const tagsMarkup = reasonTags.length ? reasonTags.map((tag) => `<span class="pick-tag">${escapeHtml(tag)}</span>`).join("") : `<span class="pick-tag">综合因子占优</span>`;
      const reasonsMarkup = reasonTexts.length
        ? `<div class="pick-detail-block">
            <div class="pick-detail-title">推荐原因</div>
            <ul class="pick-detail-list">${reasonTexts.map((text) => `<li>${escapeHtml(text)}</li>`).join("")}</ul>
          </div>`
        : "";
      const basisMarkup = basisItems.length
        ? `<div class="pick-detail-block">
            <div class="pick-detail-title">预测依据</div>
            <div class="pick-basis-list">
              ${basisItems
                .map(
                  (basis) => `
                    <div class="pick-basis-item ${basis.is_positive ? "is-positive" : "is-negative"}">
                      <div class="pick-basis-main">
                        <span class="pick-basis-label">${escapeHtml(basis.label)}</span>
                        <span class="pick-basis-value">${escapeHtml(basis.value_display)}</span>
                      </div>
                      <span class="pick-basis-contrib">${escapeHtml(basis.contribution_display)}</span>
                    </div>
                  `
                )
                .join("")}
            </div>
          </div>`
        : "";
      const riskMarkup = riskTexts.length
        ? `<div class="pick-detail-block">
            <div class="pick-detail-title">模型提示</div>
            <ul class="pick-detail-list pick-detail-list-risk">${riskTexts.map((text) => `<li>${escapeHtml(text)}</li>`).join("")}</ul>
          </div>`
        : `<div class="pick-detail-block pick-detail-block-empty">
            <div class="pick-detail-title">模型提示</div>
            <div class="pick-detail-empty">当前未识别到明显拖累因子，整体因子结构偏正面。</div>
          </div>`;
      return `
        <tr class="pick-main-row">
          <td>${item.symbol}</td>
          <td>${escapeHtml(item.name)}</td>
          <td>${formatNumber(item.close)}</td>
          <td>${formatSignedPercent(item.ret_5)}</td>
          <td>${formatSignedPercent(item.ret_10)}</td>
          <td>${formatSignedPercent(item.ret_20)}</td>
          <td>${formatSignedPercent(item.predicted_return_5)}</td>
          <td>
            <div class="pick-summary-cell">
              <div class="pick-summary-text">${escapeHtml(item.reason_summary || "综合因子占优")}</div>
              <div class="pick-tags">${tagsMarkup}</div>
              <div class="pick-meta-row">
                <span class="pick-meta-chip">置信度 ${item.confidence_label || "-"}${confidenceScore != null ? ` ${confidenceScore}%` : ""}</span>
                <span class="pick-meta-chip">风险 ${item.risk_level || "-"}${riskScore != null ? ` ${riskScore}%` : ""}</span>
              </div>
            </div>
          </td>
          <td>
            <div class="table-actions">
              <button class="mini-btn" data-action="view" data-symbol="${item.symbol}" data-name="${escapeHtml(item.name || "")}" type="button">查看</button>
              <button class="mini-btn mini-btn-strong" data-action="buy-paper" data-symbol="${item.symbol}" data-name="${escapeHtml(item.name || "")}" type="button">买100</button>
            </div>
          </td>
        </tr>
        <tr class="pick-detail-row">
          <td colspan="9">
            <div class="pick-detail-card">
              <div class="pick-detail-column pick-detail-column-main">${reasonsMarkup}</div>
              <div class="pick-detail-column pick-detail-column-side">${basisMarkup}${riskMarkup}</div>
            </div>
          </td>
        </tr>
      `;
    })
    .join("");
}

function renderWatch(payload) {
  const items = Array.isArray(payload?.items) ? payload.items : [];
  state.watch = items;
  if (!watchTable || !watchSource) {
    return;
  }
  const meta = payload?.meta || {};
  const warnings = Array.isArray(meta.warnings) ? meta.warnings.filter(Boolean) : [];
  watchSource.textContent = [meta.source_label, warnings.length ? `回退 ${meta.fallback_count || 0} 只` : null].filter(Boolean).join(" | ") || "暂无盯盘数据";
  watchTable.innerHTML = items.length
    ? items
        .map((item) => {
          const toneClass = getToneClass(item.change_pct);
          return `
            <tr class="${toneClass}">
              <td>${item.symbol}</td>
              <td>${escapeHtml(item.name || "-")}</td>
              <td>${item.mode === "live" ? "实时" : "收盘"}</td>
              <td>${item.trade_date || "-"}</td>
              <td>${item.trade_time || "-"}</td>
              <td>${formatNumber(item.price)}</td>
              <td>${formatSignedPercent(item.change_pct)}</td>
              <td>${formatNumber(item.pre_close ?? item.fallback_close)}</td>
              <td>
                <div class="table-actions">
                  <button class="mini-btn" data-action="view" data-symbol="${item.symbol}" data-name="${escapeHtml(item.name || "")}" type="button">查看</button>
                  <button class="mini-btn mini-btn-ghost" data-action="buy-paper" data-symbol="${item.symbol}" data-name="${escapeHtml(item.name || "")}" type="button">买100</button>
                </div>
              </td>
            </tr>
          `;
        })
        .join("")
    : `<tr class="placeholder-row"><td colspan="9">暂无盯盘数据</td></tr>`;
}

function renderWatchlist(payload) {
  const items = Array.isArray(payload?.items) ? payload.items : [];
  state.favorites = items;
  if (!watchlistTable || !watchlistSummary) {
    return;
  }
  const meta = payload?.meta || {};
  watchlistSummary.textContent = items.length
    ? `当前共 ${items.length} 只自选股，最近更新时间 ${formatDateTime(payload?.updated_at)}`
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
          <td>${escapeHtml(item.name || "-")}</td>
          <td>${item.mode === "live" ? "实时" : "收盘"}</td>
          <td>${item.trade_date || "-"}</td>
          <td>${item.trade_time || "-"}</td>
          <td>${formatNumber(item.price)}</td>
          <td>${formatSignedPercent(item.change_pct)}</td>
          <td>${item.added_at ? formatDateTime(item.added_at) : "-"}</td>
          <td>
            <div class="table-actions">
              <button class="mini-btn" data-action="view" data-symbol="${item.symbol}" data-name="${escapeHtml(item.name || "")}" type="button">查看</button>
              <button class="mini-btn mini-btn-ghost" data-action="buy-paper" data-symbol="${item.symbol}" data-name="${escapeHtml(item.name || "")}" type="button">买100</button>
              <button class="danger-btn" data-action="remove-favorite" data-symbol="${item.symbol}" data-kind="${item.kind || "stock"}" type="button">删除</button>
            </div>
          </td>
        </tr>
      `;
    })
    .join("");
  if (meta?.source_label) {
    setStatus(`自选快照更新完成: ${meta.source_label}`);
  }
}

function renderSearchResults(payload) {
  if (!(searchResults instanceof HTMLElement)) {
    return;
  }
  const mode = payload?.state || "success";
  if (mode === "idle") {
    searchResults.innerHTML = "";
    return;
  }
  if (mode === "loading") {
    searchResults.innerHTML = `<div class="search-empty">正在搜索 ${escapeHtml(payload?.query || "")} ...</div>`;
    return;
  }
  if (mode === "error") {
    searchResults.innerHTML = `<div class="search-empty">搜索失败: ${escapeHtml(payload?.error || "未知错误")}</div>`;
    return;
  }
  const items = Array.isArray(payload?.items) ? payload.items : [];
  if (!items.length) {
    searchResults.innerHTML = `<div class="search-empty">没有匹配结果</div><div class="search-suggestions"><span class="search-suggestions-label">试试搜索：</span><button class="search-suggestion-chip" data-suggestion="600519" type="button">600519</button><button class="search-suggestion-chip" data-suggestion="茅台" type="button">茅台</button><button class="search-suggestion-chip" data-suggestion="比亚迪" type="button">比亚迪</button></div>`;
    return;
  }
  searchResults.innerHTML = items
    .map((item) => {
      const availability = escapeHtml(item.history_label || "可查询");
      const latestDate = item.latest_date ? `最近数据 ${escapeHtml(item.latest_date)}` : availability;
      return `
        <div class="search-result-row" data-action="view-row" data-symbol="${item.symbol}" data-name="${escapeHtml(item.name || "")}">
          <div class="search-result-main">
            <span class="search-symbol">${item.symbol}</span>
            <span class="search-name">${escapeHtml(item.name || "-")}</span>
            <span class="search-extra">${latestDate}</span>
          </div>
          <div class="search-result-actions">
            <button class="search-action-btn" data-action="view-search" data-symbol="${item.symbol}" data-name="${escapeHtml(item.name || "")}" type="button">查看</button>
            <button class="search-action-btn search-action-btn-ghost ${item.is_favorite ? "is-added" : ""}" data-action="add-favorite" data-symbol="${item.symbol}" data-name="${escapeHtml(item.name || "")}" data-kind="${item.kind || "stock"}" ${item.is_favorite ? "disabled" : ""} type="button">
              ${item.is_favorite ? "已添加" : "加自选"}
            </button>
            <button class="search-action-btn search-action-btn-strong" data-action="buy-paper" data-symbol="${item.symbol}" data-name="${escapeHtml(item.name || "")}" type="button">买100</button>
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
  const map = { day: 80, week: 64, month: 60, quarter: 50, year: 24, "1m": 140, "5m": 120, "15m": 100, "30m": 90, "60m": 80, "5d": 220 };
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
  if (total <= 8) return;
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
  if (total <= 8) return;
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
  if (!state.chartItems.length || !state.chartGeometry) return;
  event.preventDefault();
  const rect = historyChart.getBoundingClientRect();
  const margin = state.chartGeometry.margin;
  const ratio = Math.max(0, Math.min(1, (event.clientX - rect.left - margin.left) / Math.max(state.chartGeometry.plotWidth, 1)));
  zoomChart(event.deltaY < 0 ? 0.85 : 1.18, ratio);
}

function applyMarketMouseWheelZoom(event) {
  if (!state.marketChartItems.length || !state.marketChartGeometry || !(marketChart instanceof HTMLCanvasElement)) return;
  event.preventDefault();
  const rect = marketChart.getBoundingClientRect();
  const margin = state.marketChartGeometry.margin;
  const ratio = Math.max(0, Math.min(1, (event.clientX - rect.left - margin.left) / Math.max(state.marketChartGeometry.plotWidth, 1)));
  zoomMarketChart(event.deltaY < 0 ? 0.85 : 1.18, ratio);
}

function setupCanvas() {
  if (!(historyChart instanceof HTMLCanvasElement)) return null;
  const ctx = historyChart.getContext("2d");
  if (!ctx) return null;
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
  if (!(marketChart instanceof HTMLCanvasElement)) return null;
  const ctx = marketChart.getContext("2d");
  if (!ctx) return null;
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
  if (!setup) return;
  setup.ctx.fillStyle = "#8ea0b8";
  setup.ctx.font = "14px Segoe UI";
  setup.ctx.fillText(text, 24, 32);
  state.chartGeometry = null;
  hideHistoryTooltip();
}

function drawEmptyMarketChart(text) {
  const setup = setupMarketCanvas();
  if (!setup) return;
  setup.ctx.fillStyle = "#8ea0b8";
  setup.ctx.font = "12px Segoe UI";
  setup.ctx.fillText(text, 16, 26);
  state.marketChartGeometry = null;
  hideMarketTooltip();
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
  if (!setup) return;
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
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
  const latestIndex = items.length - 1;
  ctx.fillStyle = values[latestIndex] >= 0 ? "#ff6b66" : "#2dd36f";
  ctx.beginPath();
  ctx.arc(xForIndex(latestIndex), valueToY(Number(items[latestIndex].change_pct ?? 0)), 3, 0, Math.PI * 2);
  ctx.fill();
  const labelIndexes = [0, Math.floor(items.length / 2), items.length - 1].filter((value, index, array) => array.indexOf(value) === index);
  ctx.fillStyle = "#8ea0b8";
  labelIndexes.forEach((index) => {
    ctx.fillText(items[index].time || "", xForIndex(index) - 14, height - 6);
  });
  state.marketChartGeometry = { type: "market-line", margin, plotWidth, plotHeight, width, height, items, xForIndex, yForValue: valueToY };
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

function drawCandlesChart() {
  const setup = setupCanvas();
  if (!setup) return;
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
  const labelIndexes = [0, Math.floor(items.length / 2), items.length - 1].filter((value, index, array) => array.indexOf(value) === index);
  ctx.fillStyle = "#8ea0b8";
  labelIndexes.forEach((index) => {
    const item = items[index];
    const label = item.time ? item.time : String(item.date || "").slice(5);
    ctx.fillText(label, xForIndex(index) - 18, height - 8);
  });
  state.chartGeometry = { type: "candles", margin, plotWidth, plotHeight, width, height, items, xForIndex, yForValue: priceToY };
  if (Number.isInteger(state.chartHoverIndex) && state.chartHoverIndex < items.length) {
    const hoverItem = items[state.chartHoverIndex];
    const x = xForIndex(state.chartHoverIndex);
    const y = priceToY(Number(hoverItem.close ?? 0));
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

function drawIntradayLineChart() {
  const setup = setupCanvas();
  if (!setup) return;
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
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
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
  const labelIndexes = [0, Math.floor(items.length / 2), items.length - 1].filter((value, index, array) => array.indexOf(value) === index);
  ctx.fillStyle = "#8ea0b8";
  labelIndexes.forEach((index) => {
    ctx.fillText(items[index].time || "", xForIndex(index) - 16, height - 8);
  });
  state.chartGeometry = { type: "intraday-line", margin, plotWidth, plotHeight, width, height, items, xForIndex, yForValue: valueToY };
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
  if (!(historyTooltip instanceof HTMLElement) || !(historyChart instanceof HTMLCanvasElement)) return;
  const rect = historyChart.getBoundingClientRect();
  historyTooltip.hidden = false;
  historyTooltip.style.left = `${Math.min(x + 14, rect.width - 148)}px`;
  historyTooltip.style.top = `${Math.max(y - 72, 12)}px`;
}

function hideHistoryTooltip() {
  if (historyTooltip instanceof HTMLElement) historyTooltip.hidden = true;
}

function hideMarketTooltip() {
  if (marketTooltip instanceof HTMLElement) marketTooltip.hidden = true;
}

function positionMarketTooltip(x, y) {
  if (!(marketTooltip instanceof HTMLElement) || !(marketChart instanceof HTMLCanvasElement)) return;
  const rect = marketChart.getBoundingClientRect();
  marketTooltip.hidden = false;
  marketTooltip.style.left = `${Math.min(x + 12, rect.width - 150)}px`;
  marketTooltip.style.top = `${Math.max(y - 64, 8)}px`;
}

function renderTooltipForIndex(index) {
  if (!state.chartGeometry || !(historyTooltip instanceof HTMLElement) || !(historyChart instanceof HTMLCanvasElement)) return;
  const item = state.chartGeometry.items[index];
  if (!item) {
    hideHistoryTooltip();
    return;
  }
  state.chartHoverIndex = index;
  drawCurrentChart();
  if (state.chartGeometry.type === "candles") {
    historyTooltip.innerHTML = `
      <div>${item.datetime || item.date}</div>
      <div>开 ${formatNumber(item.open)}</div>
      <div>高 ${formatNumber(item.high)} 低 ${formatNumber(item.low)}</div>
      <div>收 ${formatNumber(item.close)} 涨幅 ${formatSignedPercent(item.change_pct)}</div>
    `;
    positionTooltip(state.chartGeometry.xForIndex(index), state.chartGeometry.yForValue(Number(item.close ?? 0)));
    return;
  }
  historyTooltip.innerHTML = `
    <div>${state.intradayPayload?.date || ""} ${item.time || ""}</div>
    <div>价格 ${formatNumber(item.price)}</div>
    <div>涨幅 ${formatSignedPercent(item.change_pct)}</div>
  `;
  positionTooltip(state.chartGeometry.xForIndex(index), state.chartGeometry.yForValue(Number(item.change_pct ?? 0)));
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
  renderTooltipForIndex(index);
}

function renderMarketTooltipForIndex(index) {
  if (!state.marketChartGeometry || !(marketTooltip instanceof HTMLElement)) return;
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
  positionMarketTooltip(state.marketChartGeometry.xForIndex(index), state.marketChartGeometry.yForValue(Number(item.change_pct ?? 0)));
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
  const stepX = state.marketChartGeometry.items.length > 1 ? state.marketChartGeometry.plotWidth / (state.marketChartGeometry.items.length - 1) : 1;
  const index = Math.max(0, Math.min(state.marketChartGeometry.items.length - 1, Math.round(relative / stepX)));
  renderMarketTooltipForIndex(index);
}

function applyToneText(element, value, digits = 2, withPercent = false, withSign = false) {
  if (!(element instanceof HTMLElement)) return;
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
  if (!shanghai || typeof shanghai !== "object") return shanghai;
  const normalized = { ...shanghai };
  const previousClose = Number.isFinite(Number(normalized.prev_close)) && Number(normalized.prev_close) !== 0 ? Number(normalized.prev_close) : null;
  const openPrice = Number.isFinite(Number(normalized.open)) && Number(normalized.open) !== 0 ? Number(normalized.open) : null;
  const currentPrice = Number.isFinite(Number(normalized.current)) ? Number(normalized.current) : null;
  const baseline = previousClose ?? openPrice;
  if (baseline != null && currentPrice != null) {
    normalized.change = Number((currentPrice - baseline).toFixed(2));
    normalized.change_pct = Number((((currentPrice / baseline) - 1) * 100).toFixed(2));
  }
  if (Array.isArray(normalized.items) && baseline != null) {
    normalized.items = normalized.items.map((item) => {
      const price = Number(item?.price);
      if (!Number.isFinite(price) || baseline === 0) return item;
      return { ...item, change_pct: Number((((price / baseline) - 1) * 100).toFixed(2)) };
    });
  }
  return normalized;
}

function renderMarketOverview(payload) {
  const normalizedPayload = { ...(payload || {}), shanghai: normalizeShanghaiOverview(payload?.shanghai) };
  state.marketOverview = normalizedPayload;
  state.marketChartItems = normalizedPayload?.shanghai?.items || [];
  resetMarketChartViewport();
  drawMarketChart();
  if (marketUpdatedAt instanceof HTMLElement) {
    marketUpdatedAt.textContent = formatDateTime(normalizedPayload?.updated_at);
  }
  const warningText = Array.isArray(normalizedPayload?.warnings) && normalizedPayload.warnings.length ? normalizedPayload.warnings.join(" | ") : `${normalizedPayload?.meta?.status === "stale-cache" ? "正在使用最近成功缓存" : "行情数据正常"}`;
  setMetaStrip(marketWarnings, warningText, normalizedPayload?.meta?.status === "fresh" ? "positive" : normalizedPayload?.meta?.status === "stale-cache" ? "warning" : "neutral");
  if (marketShanghaiDate instanceof HTMLElement) {
    marketShanghaiDate.textContent = normalizedPayload?.shanghai?.trade_date ? `${normalizedPayload.shanghai.trade_date} 当日分时` : "当日分时";
  }
  if (marketOpen instanceof HTMLElement) marketOpen.textContent = formatNumber(normalizedPayload?.shanghai?.open, 3);
  if (marketCurrent instanceof HTMLElement) marketCurrent.textContent = formatNumber(normalizedPayload?.shanghai?.current, 3);
  applyToneText(marketChange, normalizedPayload?.shanghai?.change, 2, false, true);
  applyToneText(marketChangePct, normalizedPayload?.shanghai?.change_pct, 2, true, true);
  applyToneText(marketNasdaqPct, normalizedPayload?.nasdaq_previous?.change_pct, 2, true, true);
  if (marketNasdaqMeta instanceof HTMLElement) {
    const parts = [];
    if (normalizedPayload?.nasdaq_previous?.trade_date) parts.push(normalizedPayload.nasdaq_previous.trade_date);
    if (normalizedPayload?.nasdaq_previous?.close != null) parts.push(`收 ${formatNumber(normalizedPayload.nasdaq_previous.close)}`);
    marketNasdaqMeta.textContent = parts.join(" | ") || "-";
  }
  if (marketNasdaqCard instanceof HTMLElement) {
    marketNasdaqCard.classList.remove("market-up", "market-down", "market-flat");
    marketNasdaqCard.classList.add(getToneClassName(normalizedPayload?.nasdaq_previous?.change_pct));
  }
}

function syncHotNewsFilterButton() {
  if (!(hotNewsFilters instanceof HTMLElement)) return;
  const categories = state.hotNewsAvailableCategories || { all: "全部" };
  hotNewsFilters.innerHTML = Object.entries(categories)
    .map(
      ([key, label]) => `
        <button
          class="hot-news-filter-btn ${state.hotNewsCategory === key ? "is-active" : ""}"
          data-category="${key}"
          aria-pressed="${state.hotNewsCategory === key ? "true" : "false"}"
          type="button"
        >${label}</button>
      `
    )
    .join("");
}

function renderHotNews(payload) {
  const items = Array.isArray(payload?.items) ? payload.items : [];
  const appendMode = Boolean(payload?._append);
  state.hotNews = appendMode ? [...state.hotNews, ...items] : items;
  state.hotNewsOffset = Number(payload?.next_offset || state.hotNews.length);
  state.hotNewsTotal = Number(payload?.total || state.hotNews.length);
  state.hotNewsHasMore = Boolean(payload?.has_more);
  state.hotNewsCategory = payload?.category || "all";
  if (payload?.available_categories && typeof payload.available_categories === "object") {
    state.hotNewsAvailableCategories = payload.available_categories;
  }
  syncHotNewsFilterButton();
  const metaParts = [];
  if (payload?.source_label) metaParts.push(payload.source_label);
  if (payload?.updated_at) metaParts.push(`更新 ${formatDateTime(payload.updated_at)}`);
  if (payload?.meta?.status === "stale-cache") metaParts.push("使用最近成功缓存");
  if (payload?.errors?.length) metaParts.push(`异常 ${payload.errors.length} 项`);
  const metaText = metaParts.join(" | ") || "暂无快报数据";
  if (hotNewsPageMeta instanceof HTMLElement) {
    hotNewsPageMeta.textContent = `${metaText} | 已加载 ${state.hotNews.length}/${state.hotNewsTotal || state.hotNews.length}`;
  }
  if (!(hotNewsList instanceof HTMLElement)) return;
  hotNewsList.innerHTML = state.hotNews.length
    ? state.hotNews
        .map((item, index) => {
          const tag = escapeHtml(item.tag || "快讯");
          const title = escapeHtml(item.title || "市场热点快报");
          const summary = escapeHtml(item.summary || item.title || "");
          const publishedAt = escapeHtml(item.published_at || "-");
          const source = escapeHtml(item.source || payload?.source_label || "快报");
          const aiSummary = escapeHtml(item.ai_summary || "中性观察");
          const aiTone = item.ai_tone === "positive" ? "news-positive" : item.ai_tone === "negative" ? "news-negative" : "news-neutral";
          const href = item.url ? ` href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer"` : "";
          const wrapperTag = item.url ? "a" : "div";
          return `
            <${wrapperTag} class="brief-item brief-item--neutral" data-index="${index}"${href}>
              <div class="brief-side">
                <div class="brief-time">${publishedAt}</div>
                <div class="brief-ai ${aiTone}">AI总结：${aiSummary}</div>
              </div>
              <div class="brief-main">
                <div class="brief-title-row">
                  <span class="brief-tag">${tag}</span>
                  <span class="brief-source">${source}</span>
                </div>
                <div class="brief-title">${title}</div>
                <div class="brief-summary">${summary}</div>
              </div>
            </${wrapperTag}>
          `;
        })
        .join("")
    : `<div class="placeholder-row hot-news-empty">${state.hotNewsCategory === "tech" ? "暂无科技相关快报" : "暂无热点快报"}</div>`;
  if (hotNewsLoadMoreHint instanceof HTMLElement) {
    if (state.hotNewsLoading) hotNewsLoadMoreHint.textContent = `正在加载更多${getHotNewsCategoryLabel()}快报...`;
    else if (state.hotNewsHasMore) hotNewsLoadMoreHint.textContent = "向下滚动继续加载";
    else hotNewsLoadMoreHint.textContent = `已加载全部 ${state.hotNews.length} 条快报`;
  }
}

function renderHistoryMeta(payload) {
  const meta = payload?.meta || {};
  const availability = payload?.availability || {};
  const parts = [];
  if (meta.source_label) parts.push(meta.source_label);
  if (meta.as_of) parts.push(`截至 ${meta.as_of}`);
  if (availability.history_status === "local") parts.push("本地历史可用");
  if (availability.history_status === "remote") parts.push("本地缺失，远程回退");
  if (availability.history_status === "index") parts.push("指数历史");
  if (Array.isArray(meta.warnings) && meta.warnings.length) parts.push(meta.warnings.join(" | "));
  setMetaStrip(historyMeta, parts.join(" | ") || "历史数据正常", meta.status === "fresh" ? "positive" : meta.status === "stale-cache" || meta.status === "degraded" ? "warning" : "neutral");
}

function updateHistoryHeader() {
  if (!historyTitle || !historyBadge) return;
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
  if (!historyTable) return;
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
      : `<tr><td colspan="6">${escapeHtml(state.intradayPayload.message || "暂无当日涨跌图数据")}</td></tr>`;
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
  if (historyBackBtn) historyBackBtn.hidden = true;
  renderHistoryMeta(payload);
  updateHistoryHeader();
  renderHistoryTable();
  drawCurrentChart();
}

function renderIntradayPayload(payload) {
  state.intradayPayload = payload;
  state.activeChartMode = "intraday-line";
  state.chartItems = payload.items || [];
  resetChartViewport();
  if (historyBackBtn) historyBackBtn.hidden = false;
  setMetaStrip(historyMeta, payload.message || "已切换至当日涨跌图", payload.meta?.status === "fresh" ? "positive" : payload.meta?.status === "estimated" ? "warning" : "neutral");
  updateHistoryHeader();
  renderHistoryTable();
  drawCurrentChart();
}

function renderPortfolio(snapshot) {
  state.portfolio = snapshot;
  if (!(portfolioSummaryCards instanceof HTMLElement) || !(portfolioPositionsTable instanceof HTMLElement) || !(portfolioTradesTable instanceof HTMLElement)) {
    return;
  }
  const summaryCards = [
    { label: "总资产", value: formatCurrency(snapshot?.equity), hint: "现金 + 持仓市值" },
    { label: "可用现金", value: formatCurrency(snapshot?.cash), hint: "可直接继续下单的本地模拟资金" },
    { label: "持仓市值", value: formatCurrency(snapshot?.market_value), hint: "当前持仓按最新价估值" },
    { label: "浮动盈亏", value: formatCurrency(snapshot?.unrealized_pnl), hint: "当前持仓未实现盈亏" },
    { label: "已实现盈亏", value: formatCurrency(snapshot?.realized_pnl), hint: "已完成卖出后记录的盈亏" },
    { label: "成交笔数", value: `${snapshot?.trade_count ?? 0}`, hint: "本地模拟单累计成交笔数" },
    { label: "持仓数量", value: `${snapshot?.position_count ?? 0}`, hint: "当前持仓股票数量" },
    { label: "仓位占比", value: formatPercent(Number(snapshot?.position_ratio_pct ?? Number(snapshot?.position_ratio ?? 0) * 100)), hint: "持仓市值 / 总资产" },
    { label: "现金占比", value: formatPercent(Number(snapshot?.cash_ratio_pct ?? Number(snapshot?.cash_ratio ?? 0) * 100)), hint: "现金 / 总资产" },
    { label: "累计费用", value: formatCurrency(snapshot?.total_fees), hint: "累计佣金、印花税等费用" },
    { label: "胜率", value: formatPercent(snapshot?.win_rate_pct), hint: "已完成卖出中的盈利笔数占比" },
  ];
  portfolioSummaryCards.innerHTML = summaryCards
    .map(
      (card) => `
        <article class="card card-compact">
          <div class="label">${card.label}</div>
          <div class="value">${card.value}</div>
          <div class="hint">${card.hint}</div>
        </article>
      `
    )
    .join("");
  if (portfolioMeta instanceof HTMLElement) {
    portfolioMeta.textContent = `最近快照 ${formatDateTime(snapshot?.updated_at)} | 初始资金 ${formatCurrency(snapshot?.initial_cash)} | 成交 ${snapshot?.trade_count ?? 0} 笔`;
  }
  const settings = snapshot?.settings || {};
  if (portfolioCommissionRate instanceof HTMLInputElement) portfolioCommissionRate.value = settings.commission_rate ?? "";
  if (portfolioMinCommission instanceof HTMLInputElement) portfolioMinCommission.value = settings.min_commission ?? "";
  if (portfolioStampDutyRate instanceof HTMLInputElement) portfolioStampDutyRate.value = settings.stamp_duty_rate ?? "";
  if (portfolioSlippageBps instanceof HTMLInputElement) portfolioSlippageBps.value = settings.slippage_bps ?? "";
  syncPortfolioPriceMode();
  const positions = Array.isArray(snapshot?.positions) ? snapshot.positions : [];
  portfolioPositionsTable.innerHTML = positions.length
    ? positions
        .map((item) => `
          <tr class="${getToneClass(item.unrealized_pnl)}">
            <td>${item.symbol}</td>
            <td>${escapeHtml(item.name || "-")}</td>
            <td>${item.quantity}</td>
            <td>${formatNumber(item.avg_cost)}</td>
            <td>${formatNumber(item.current_price)}</td>
            <td>${formatCurrency(item.market_value)}</td>
            <td>${formatCurrency(item.unrealized_pnl)}</td>
            <td>${formatPercent(item.weight_pct)}</td>
            <td>
              <div class="table-actions">
                <button class="mini-btn" data-action="view" data-symbol="${item.symbol}" data-name="${escapeHtml(item.name || "")}" type="button">查看</button>
                <button class="mini-btn mini-btn-ghost" data-action="sell-paper" data-symbol="${item.symbol}" data-name="${escapeHtml(item.name || "")}" data-quantity="${Math.min(Number(item.quantity) || 0, 100)}" type="button">卖100</button>
              </div>
            </td>
          </tr>
        `)
        .join("")
    : `<tr class="placeholder-row"><td colspan="9">暂无持仓，先从候选股或搜索结果里下第一笔模拟单。</td></tr>`;
  const trades = (Array.isArray(snapshot?.recent_trades) ? snapshot.recent_trades : []).slice(0, 10);
  portfolioTradesTable.innerHTML = trades.length
    ? trades
        .map((trade) => `
          <tr class="${trade.side === "buy" ? "quote-up" : "quote-down"}">
            <td>${formatDateTime(trade.executed_at)}</td>
            <td>${trade.symbol}</td>
            <td>${escapeHtml(trade.name || "-")}</td>
            <td><span class="trade-status trade-status-${escapeHtml(trade.status || "filled")}">${trade.side === "buy" ? "买入" : "卖出"} / ${trade.status || "-"}</span></td>
            <td>${trade.quantity}</td>
            <td>${formatNumber(trade.requested_price ?? trade.price)}</td>
            <td>${formatNumber(trade.price)}</td>
            <td>${formatCurrency(trade.commission)}</td>
            <td>${formatCurrency(trade.fees)}</td>
            <td>${formatCurrency(trade.realized_pnl)}</td>
          </tr>
        `)
        .join("")
    : `<tr class="placeholder-row"><td colspan="10">暂无成交记录</td></tr>`;
}

function renderScreen(payload) {
  const items = Array.isArray(payload?.items) ? payload.items : [];
  if (!(screenList instanceof HTMLElement)) return;
  screenList.innerHTML = items.length
    ? items
        .map(
          (item) => `
            <article class="card card-compact">
              <div class="label">${escapeHtml(item.symbol)} ${escapeHtml(item.name || "")}</div>
              <div class="value">${formatSignedPercent(item.predicted_return_5)}</div>
              <div class="hint">${escapeHtml(item.reason_summary || "模型筛选")}</div>
            </article>
          `
        )
        .join("")
    : `<div class="placeholder-row">暂无符合条件的股票</div>`;
}

function renderRotation(payload) {
  const items = Array.isArray(payload?.items) ? payload.items : [];
  if (!(rotationList instanceof HTMLElement)) return;
  rotationList.innerHTML = items.length
    ? items
        .map(
          (item, idx) => `
            <div class="market-sector-row">
              <div class="market-sector-rank">${idx + 1}</div>
              <div class="market-sector-main">
                <div class="market-sector-name">${escapeHtml(item.name || "-")}</div>
                <div class="market-sector-extra">${escapeHtml(item.leader_name || "-")}${item.leader_change_pct != null ? " (" + formatSignedPercent(item.leader_change_pct) + ")" : ""} | ↑${item.up_count ?? 0} ↓${item.down_count ?? 0}</div>
              </div>
              <div class="market-sector-change ${getToneClassName(item.change_pct)}">${formatSignedPercent(item.change_pct)}</div>
            </div>
          `
        )
        .join("")
    : `<div class="placeholder-row">暂无行业轮动数据</div>`;
}

function renderPrePost(payload) {
  const items = Array.isArray(payload?.items) ? payload.items : [];
  if (!(prepostList instanceof HTMLElement)) return;
  prepostList.innerHTML = items.length
    ? items
        .map(
          (item) => `
            <div class="brief-item">
              <div class="brief-side">
                <div class="brief-time">${escapeHtml(item.time || "-")}</div>
                <div class="brief-ai ${item.tone === "positive" ? "news-positive" : item.tone === "negative" ? "news-negative" : "news-neutral"}">${escapeHtml(item.summary || "-")}</div>
              </div>
              <div class="brief-main">
                <div class="brief-title">${escapeHtml(item.title || "-")}</div>
              </div>
            </div>
          `
        )
        .join("")
    : `<div class="placeholder-row">暂无盘前盘后内容</div>`;
}

function renderStockAnalysis(payload) {
  if (!(stockAnalysisResult instanceof HTMLElement)) { return; }
  if (!payload || !payload.symbol) {
    stockAnalysisResult.innerHTML = '<div class="placeholder-row">输入代码后查看分析</div>';
    return;
  }
  var ret = payload.returns || {};
  var trendMap = {up: '上升趋势', down: '下降趋势', flat: '横盘整理'};
  var trendClassMap = {up: 'news-positive', down: 'news-negative', flat: 'news-neutral'};
  var trendLabel = trendMap[payload.trend] || '未知';
  var trendClass = trendClassMap[payload.trend] || '';

  var bullishHtml = (payload.bullish || []).map(function(b) {
    return '<div class="signal-item signal-bullish">' + escapeHtml(b) + '</div>';
  }).join('');
  var bearishHtml = (payload.bearish || []).map(function(b) {
    return '<div class="signal-item signal-bearish">' + escapeHtml(b) + '</div>';
  }).join('');

  var newsHtml = '';
  if (payload.related_news && payload.related_news.length) {
    newsHtml = payload.related_news.map(function(n) {
      var toneCls = n.tone === 'positive' ? 'news-positive' : (n.tone === 'negative' ? 'news-negative' : 'news-neutral');
      return '<div class="brief-item"><div class="brief-side"><div class="brief-time">' + escapeHtml(n.time || '') + '</div><div class="brief-ai ' + toneCls + '">' + escapeHtml(n.title || '') + '</div></div><div class="brief-main"><div class="brief-summary">' + escapeHtml(n.summary || '') + '</div></div></div>';
    }).join('');
  } else {
    newsHtml = '<div class="placeholder-row" style="padding:8px">暂无相关新闻</div>';
  }

  var modelHtml = '';
  if (payload.model_signal) {
    var ms = payload.model_signal;
    var msTone = ms.predicted_return > 0 ? 'news-positive' : 'news-negative';
    modelHtml = '<div class="analysis-card"><div class="analysis-card-title">模型信号</div><div class="analysis-card-body">'
      + '<div class="model-signal-row"><span>预测排名</span><span class="analysis-value">#' + ms.rank + '</span></div>'
      + '<div class="model-signal-row"><span>预测5日收益</span><span class="analysis-value ' + msTone + '">' + formatSignedPercent(ms.predicted_return) + '</span></div>'
      + (ms.reason ? '<div class="model-signal-reason">' + escapeHtml(ms.reason) + '</div>' : '')
      + '</div></div>';
  } else {
    modelHtml = '<div class="analysis-card"><div class="analysis-card-title">模型信号</div><div class="analysis-card-body"><div class="placeholder-row" style="padding:4px">该股票不在模型候选池中</div></div></div>';
  }

  var retRow = function(label, val) {
    return '<div class="return-row"><span>' + label + '</span><span class="' + getToneClassName(val) + '">' + formatSignedPercent(val) + '</span></div>';
  };

  var headerHtml = '<div class="analysis-header"><div class="analysis-stock-name">' + escapeHtml(payload.name || payload.symbol) + ' <span class="analysis-symbol">' + escapeHtml(payload.symbol) + '</span></div>'
    + (payload.current_price != null ? '<div class="analysis-price">' + payload.current_price + '</div>' : '')
    + '</div>';

    var ret5 = payload.returns && payload.returns['5d'] != null ? payload.returns['5d'] : null;
  var ret10 = payload.returns && payload.returns['10d'] != null ? payload.returns['10d'] : null;
  var ret20 = payload.returns && payload.returns['20d'] != null ? payload.returns['20d'] : null;

  var gridHtml = '<div class="analysis-grid">'
    + '<div class="analysis-card"><div class="analysis-card-title">近期涨幅</div><div class="analysis-card-body">'
    + '<div class="return-row"><span>5日</span><span class="' + getToneClassName(ret5) + '">' + formatSignedPercent(ret5) + '</span></div>'
    + '<div class="return-row"><span>10日</span><span class="' + getToneClassName(ret10) + '">' + formatSignedPercent(ret10) + '</span></div>'
    + '<div class="return-row"><span>20日</span><span class="' + getToneClassName(ret20) + '">' + formatSignedPercent(ret20) + '</span></div>'
    + '</div></div>'
    + '<div class="analysis-card"><div class="analysis-card-title">趋势判断</div><div class="analysis-card-body">'
    + '<div class="trend-badge ' + trendClass + '">' + trendLabel + '</div>'
    + (payload.volatility != null ? '<div class="analysis-meta">日均波动 ' + payload.volatility + '%</div>' : '')
    + '</div></div>'
    + '</div>';
  var signalsHtml = '<div class="analysis-signals">'
    + '<div class="analysis-card"><div class="analysis-card-title signal-title-bullish">利好因素</div><div class="analysis-card-body">' + bullishHtml + '</div></div>'
    + '<div class="analysis-card"><div class="analysis-card-title signal-title-bearish">利空因素</div><div class="analysis-card-body">' + bearishHtml + '</div></div>'
    + '</div>';

  var newsCardHtml = '<div class="analysis-card"><div class="analysis-card-title">相关热点</div><div class="analysis-card-body">' + newsHtml + '</div></div>';

  stockAnalysisResult.innerHTML = headerHtml + gridHtml + signalsHtml + modelHtml + newsCardHtml;
}

function renderAlerts(payload) {
  const items = Array.isArray(payload?.items) ? payload.items : [];
  if (!(alertsList instanceof HTMLElement)) return;
  alertsList.innerHTML = items.length
    ? items
        .map(
          (item) => `
            <div class="brief-item">
              <div class="brief-side">
                <div class="brief-time">${escapeHtml(item.category || "提醒")}</div>
                <div class="brief-ai news-positive">${escapeHtml(item.title || "-")}</div>
              </div>
              <div class="brief-main">
                <div class="brief-summary">${escapeHtml(item.body || "-")}</div>
              </div>
            </div>
          `
        )
        .join("")
    : `<div class="placeholder-row">暂无预警</div>`;
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

async function loadDashboard() {
  const [overview, picksPayload] = await Promise.all([
    fetchJson(`/api/overview?source=${defaultSource}`),
    fetchJson(`/api/picks?limit=${defaultPicksLimit}&source=${defaultSource}`),
  ]);
  renderCards(overview);
  renderModelMetrics(overview);
  renderPicks(picksPayload.items || []);
  if (overview.trained_now && overview.training_metrics) {
    setStatus(`首次加载时自动完成训练。\n${JSON.stringify(overview.training_metrics, null, 2)}`);
  } else {
    setStatus(`页面已刷新，当前使用 ${overview.data_source === "real" ? "本地真实数据" : "样例数据"} 进行打分。`);
  }
}

async function loadWatchlist() {
  const payload = await fetchJson(`/api/watchlist?limit=${defaultWatchLimit}&source=real`);
  renderWatch(payload);
}

async function loadFavorites() {
  const payload = await fetchJson("/api/favorites");
  renderWatchlist(payload);
}

async function loadPortfolio() {
  const payload = await fetchJson("/api/portfolio");
  renderPortfolio(payload);
}

async function loadScreen() {
  const payload = await fetchJson("/api/screener");
  renderScreen(payload);
}

async function loadRotation() {
  const payload = await fetchJson("/api/rotation");
  renderRotation(payload);
}

async function loadPrePost() {
  const payload = await fetchJson("/api/prepost");
  renderPrePost(payload);
}

async function loadAlerts() {
  const payload = await fetchJson("/api/alerts");
  renderAlerts(payload);
}

async function loadMarketOverview() {
  const payload = await fetchJson("/api/market-overview?limit=6");
  renderMarketOverview(payload);
}

async function loadHotNews(forceRefresh = false, append = false) {
  if (state.hotNewsLoading) return;
  if (append && !state.hotNewsHasMore) return;
  state.hotNewsLoading = true;
  syncHotNewsFilterButton();
  if (hotNewsLoadMoreHint instanceof HTMLElement) {
    hotNewsLoadMoreHint.textContent = append ? `正在加载更多${getHotNewsCategoryLabel()}快报...` : `正在加载${getHotNewsCategoryLabel()}快报...`;
  }
  try {
    const offset = append ? state.hotNewsOffset : 0;
    const params = new URLSearchParams({ limit: String(hotNewsPageSize), offset: String(offset) });
    if (state.hotNewsCategory !== "all") params.set("category", state.hotNewsCategory);
    if (forceRefresh) params.set("force_refresh", "true");
    const payload = await fetchJson(`/api/hot-news?${params.toString()}`);
    renderHotNews({ ...payload, _append: append });
  } finally {
    state.hotNewsLoading = false;
    if (hotNewsLoadMoreHint instanceof HTMLElement) {
      hotNewsLoadMoreHint.textContent = state.hotNewsHasMore ? "向下滚动继续加载" : `已加载全部 ${state.hotNews.length} 条快报`;
    }
  }
}

async function selectHotNewsCategory(category) {
  const nextCategory = category || "all";
  if (state.hotNewsCategory === nextCategory && state.hotNews.length) return;
  state.hotNewsCategory = nextCategory;
  state.hotNews = [];
  state.hotNewsOffset = 0;
  state.hotNewsTotal = 0;
  state.hotNewsHasMore = true;
  syncHotNewsFilterButton();
  if (hotNewsScroll instanceof HTMLElement) hotNewsScroll.scrollTop = 0;
  await loadHotNews(false, false);
}



async function loadBacktest() {
  if (backtestStatus instanceof HTMLElement) backtestStatus.textContent = "\u8fd0\u884c\u4e2d...";
  if (backtestRunBtn instanceof HTMLButtonElement) backtestRunBtn.disabled = true;
  try {
    const tw = backtestTrainWindow instanceof HTMLInputElement ? backtestTrainWindow.value : "120";
    const tw2 = backtestTestWindow instanceof HTMLInputElement ? backtestTestWindow.value : "20";
    const tn = backtestTopN instanceof HTMLInputElement ? backtestTopN.value : "10";
    const data = await fetchJson(`/api/backtest?train_window=${tw}&test_window=${tw2}&top_n=${tn}`);
    renderBacktest(data);
    if (backtestStatus instanceof HTMLElement) backtestStatus.textContent = data.status === "ok" ? `\u5b8c\u6210 ${data.aggregate?.prediction_days || 0} \u5929\u9884\u6d4b` : `\u72b6\u6001: ${data.status}`;
  } catch (err) {
    if (backtestStatus instanceof HTMLElement) backtestStatus.textContent = `\u5931\u8d25: ${err.message}`;
  } finally {
    if (backtestRunBtn instanceof HTMLButtonElement) backtestRunBtn.disabled = false;
  }
}

function renderBacktest(data) {
  // Aggregate cards
  if (backtestAggregate instanceof HTMLElement) {
    const agg = data.aggregate || {};
    const cards = [
      { label: "\u7d2f\u8ba1\u6536\u76ca", value: formatSignedPercent(agg.total_return), hint: `\u9884\u6d4b\u5929\u6570 ${agg.prediction_days || 0}` },
      { label: "\u5e74\u5316\u6536\u76ca", value: agg.annualized_return != null ? formatSignedPercent(agg.annualized_return) : "-", hint: "\u6eda\u52a8\u7b56\u7565\u5e74\u5316" },
      { label: "\u6700\u5927\u56de\u64a4", value: agg.max_drawdown != null ? formatSignedPercent(agg.max_drawdown) : "-", hint: "\u5386\u53f2\u6700\u5927\u56de\u64a4" },
      { label: "Sharpe", value: agg.sharpe != null ? Number(agg.sharpe).toFixed(3) : "-", hint: "\u6536\u76ca\u98ce\u9669\u6bd4" },
      { label: "RankIC", value: agg.rank_ic != null ? Number(agg.rank_ic).toFixed(3) : "-", hint: "\u9884\u6d4b\u6392\u5e8f\u4e0e\u6536\u76ca\u6392\u5e8f\u76f8\u5173" },
      { label: "\u80dc\u7387", value: agg.hit_rate != null ? `${agg.hit_rate}%` : "-", hint: "\u6b63\u6536\u76ca\u5929\u6570\u5360\u6bd4" },
    ];
    backtestAggregate.innerHTML = cards.map((c) => `<article class="card card-compact"><div class="label">${c.label}</div><div class="value">${c.value}</div><div class="hint">${c.hint}</div></article>`).join("");
  }

  // Equity curve chart
  if (backtestChart instanceof HTMLCanvasElement && data.equity_curve?.length) {
    drawBacktestChart(data.equity_curve);
  } else if (backtestChart instanceof HTMLCanvasElement) {
    const ctx2 = backtestChart.getContext("2d");
    if (ctx2) { ctx2.clearRect(0, 0, backtestChart.width, backtestChart.height); }
  }

  // Windows table
  if (backtestWindows instanceof HTMLElement) {
    const wins = data.windows || [];
    if (!wins.length) {
      backtestWindows.innerHTML = '<div class="placeholder-row">\u65e0\u7a97\u53e3\u7ed3\u679c</div>';
      return;
    }
    let html = '<table class="data-table"><thead><tr><th>\u7a97\u53e3</th><th>\u8bad\u7ec3\u533a\u95f4</th><th>\u9884\u6d4b\u533a\u95f4</th><th>\u5929\u6570</th><th>\u5e73\u5747\u6536\u76ca</th><th>\u80dc\u7387</th><th>Sharpe</th><th>IC</th><th>RankIC</th></tr></thead><tbody>';
    wins.forEach((w, idx) => {
      const retClass = w.avg_return > 0 ? "tone-positive" : w.avg_return < 0 ? "tone-negative" : "";
      html += `<tr><td>${idx + 1}</td><td>${w.train_start} ~ ${w.train_end}</td><td>${w.test_start} ~ ${w.test_end}</td><td>${w.days}</td><td class="${retClass}">${w.avg_return != null ? w.avg_return.toFixed(2) + "%" : "-"}</td><td>${w.hit_rate != null ? w.hit_rate.toFixed(1) + "%" : "-"}</td><td>${w.sharpe != null ? w.sharpe.toFixed(3) : "-"}</td><td>${w.ic != null ? w.ic.toFixed(3) : "-"}</td><td>${w.rank_ic != null ? w.rank_ic.toFixed(3) : "-"}</td></tr>`;
    });
    html += "</tbody></table>";
    backtestWindows.innerHTML = html;
  }
}

function drawBacktestChart(curve) {
  if (!(backtestChart instanceof HTMLCanvasElement) || !curve.length) return;
  const ctx2 = backtestChart.getContext("2d");
  if (!ctx2) return;
  const dpr = window.devicePixelRatio || 1;
  const w = backtestChart.clientWidth || 760;
  const h = backtestChart.clientHeight || 280;
  backtestChart.width = Math.floor(w * dpr);
  backtestChart.height = Math.floor(h * dpr);
  ctx2.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx2.clearRect(0, 0, w, h);
  ctx2.fillStyle = "#0c1118";
  ctx2.fillRect(0, 0, w, h);

  const margin = { top: 20, right: 20, bottom: 30, left: 60 };
  const pw = w - margin.left - margin.right;
  const ph = h - margin.top - margin.bottom;
  const values = curve.map((c) => c.cumulative);
  const minV = Math.min(...values) * 0.998;
  const maxV = Math.max(...values) * 1.002;
  const range = maxV - minV || 1;
  const stepX = pw / Math.max(curve.length - 1, 1);
  const toY = (v) => margin.top + ((maxV - v) / range) * ph;
  const toX = (i) => margin.left + stepX * i;

  // Grid
  ctx2.strokeStyle = "rgba(255,255,255,0.06)";
  ctx2.lineWidth = 1;
  for (let g = 0; g <= 4; g++) {
    const gy = margin.top + (ph / 4) * g;
    ctx2.beginPath(); ctx2.moveTo(margin.left, gy); ctx2.lineTo(w - margin.right, gy); ctx2.stroke();
    const gv = maxV - (range / 4) * g;
    ctx2.fillStyle = "#6b7a8d"; ctx2.font = "11px monospace"; ctx2.textAlign = "right";
    ctx2.fillText(gv.toFixed(3), margin.left - 6, gy + 4);
  }

  // Line
  ctx2.beginPath();
  ctx2.strokeStyle = "#00d4aa";
  ctx2.lineWidth = 2;
  curve.forEach((c, i) => {
    const x = toX(i), y = toY(c.cumulative);
    i === 0 ? ctx2.moveTo(x, y) : ctx2.lineTo(x, y);
  });
  ctx2.stroke();

  // Fill under
  ctx2.lineTo(toX(curve.length - 1), margin.top + ph);
  ctx2.lineTo(toX(0), margin.top + ph);
  ctx2.closePath();
  ctx2.fillStyle = "rgba(0,212,170,0.08)";
  ctx2.fill();

  // Baseline (1.0)
  const baseY = toY(1.0);
  if (baseY > margin.top && baseY < margin.top + ph) {
    ctx2.strokeStyle = "rgba(255,255,255,0.2)";
    ctx2.lineWidth = 1;
    ctx2.setLineDash([4, 4]);
    ctx2.beginPath(); ctx2.moveTo(margin.left, baseY); ctx2.lineTo(w - margin.right, baseY); ctx2.stroke();
    ctx2.setLineDash([]);
  }

  // X labels
  ctx2.fillStyle = "#6b7a8d"; ctx2.font = "10px monospace"; ctx2.textAlign = "center";
  const labelIdxs = [0, Math.floor(curve.length / 2), curve.length - 1];
  labelIdxs.forEach((idx) => {
    if (idx >= 0 && idx < curve.length) {
      ctx2.fillText(curve[idx].date, toX(idx), h - 8);
    }
  });
}

function startMarketPolling() {
  stopMarketPolling();
  state.marketPollTimer = window.setInterval(() => {
    loadMarketOverview().catch(() => {});
  }, 45000);
}

async function loadHistory(symbol, period = state.selectedPeriod) {
  const requestSeq = ++state.historySeq;
  state.currentHistorySymbol = symbol;
  state.selectedPeriod = period;
  setActivePeriodButton(period);
  const limit = periodLimitMap[period] || 120;
  const payload = await fetchJson(`/api/history/${symbol}?period=${encodeURIComponent(period)}&limit=${limit}`);
  if (requestSeq !== state.historySeq) {
    return null;
  }
  renderHistoryPayload(payload);
  return payload;
}

async function loadIntradayHistory(symbol, tradeDate) {
  const requestSeq = ++state.historySeq;
  const payload = await fetchJson(`/api/watch-intraday/${symbol}?trade_date=${encodeURIComponent(tradeDate)}`);
  if (requestSeq !== state.historySeq) {
    return null;
  }
  renderIntradayPayload(payload);
  return payload;
}

async function searchStocks(query) {
  const keyword = query.trim();
  const searchSeq = ++state.searchSeq;
  if (!keyword) {
    renderSearchResults({ state: "idle" });
    return { items: [], query: keyword };
  }
  renderSearchResults({ state: "loading", query: keyword });
  try {
    const payload = await fetchJson(`/api/search?query=${encodeURIComponent(keyword)}&limit=12`);
    if (searchSeq !== state.searchSeq) return null;
    renderSearchResults({ ...payload, state: "success" });
    return payload;
  } catch (error) {
    if (searchSeq !== state.searchSeq) return null;
    renderSearchResults({ state: "error", query: keyword, error: error.message });
    throw error;
  }
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
  await fetchJson(`/api/favorites/${encodeURIComponent(symbol)}?kind=${encodeURIComponent(kind || "stock")}`, { method: "DELETE" });
  await loadFavorites();
  if (stockSearchInput instanceof HTMLInputElement && stockSearchInput.value.trim()) {
    await searchStocks(stockSearchInput.value);
  }
}

async function submitPaperOrder({ symbol, name, side, quantity, priceMode = "live", price = null }) {
  const payload = await fetchJson("/api/portfolio/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol, name, side, quantity, price_mode: priceMode, price }),
  });
  renderPortfolio(payload.snapshot);
  const trade = payload.trade || {};
  const sideLabel = side === "buy" ? "买入" : "卖出";
  const priceLabel = trade.price != null ? formatNumber(trade.price) : "-";
  const qtyLabel = trade.quantity != null ? `${trade.quantity} 股` : `${quantity} 股`;
  setStatus(`${symbol} ${sideLabel} 模拟单已成交。\n成交价格 ${priceLabel} | 数量 ${qtyLabel}`);
  pushToast(`${symbol} ${sideLabel}成交 ${qtyLabel} @ ${priceLabel}`, "success");
  return payload;
}

async function buyPaperLot(symbol, name, quantity = 100) {
  return submitPaperOrder({ symbol, name, side: "buy", quantity, priceMode: "live" });
}

async function sellPaperLot(symbol, name, quantity = 100) {
  return submitPaperOrder({ symbol, name, side: "sell", quantity, priceMode: "live" });
}

async function resetPortfolio() {
  await fetchJson("/api/portfolio/reset", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({}) });
  await loadPortfolio();
  setStatus("模拟盘已重置。");
}

async function savePortfolioSettings() {
  const payload = {
    commission_rate: portfolioCommissionRate instanceof HTMLInputElement ? Number(portfolioCommissionRate.value || 0) : 0,
    min_commission: portfolioMinCommission instanceof HTMLInputElement ? Number(portfolioMinCommission.value || 0) : 0,
    stamp_duty_rate: portfolioStampDutyRate instanceof HTMLInputElement ? Number(portfolioStampDutyRate.value || 0) : 0,
    slippage_bps: portfolioSlippageBps instanceof HTMLInputElement ? Number(portfolioSlippageBps.value || 0) : 0,
  };
  const snapshot = await fetchJson("/api/portfolio/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  renderPortfolio(snapshot);
  setStatus("模拟盘交易设置已更新。");
}

async function exportPortfolio() {
  const payload = await fetchJson("/api/portfolio/export");
  downloadJsonFile(buildPortfolioExportFilename(payload.exported_at), payload);
  setStatus("模拟盘数据已开始下载。");
}

async function importPortfolio() {
  if (!(portfolioImportFile instanceof HTMLInputElement) || !portfolioImportFile.files?.length) {
    portfolioImportFile?.click?.();
    return;
  }
  const file = portfolioImportFile.files[0];
  const payload = await readJsonFile(file);
  const snapshot = await fetchJson("/api/portfolio/import", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  renderPortfolio(snapshot);
  setStatus("模拟盘数据已导入。");
  portfolioImportFile.value = "";
}

async function initializeDashboard() {
  setStatus("正在加载候选股、实时盯盘、自选股、模拟盘与历史回看...");
  const results = await Promise.allSettled([loadDashboard(), loadWatchlist(), loadFavorites(), loadPortfolio(), loadHistory(state.currentHistorySymbol), loadMarketOverview(), loadHotNews(), syncRefreshStatus()]);
  const rejected = results.filter((result) => result.status === "rejected");
  if (rejected.length) {
    setStatus(`首屏已加载完成，但有 ${rejected.length} 项接口失败。\n${rejected.map((item) => item.reason?.message || "未知错误").join(" | ")}`);
  }
  loadScreen().catch(() => {});
  loadRotation().catch(() => {});
  loadPrePost().catch(() => {});
  loadAlerts().catch(() => {});
}

async function retrain() {
  setStatus("正在重新训练模型...");
  if (trainBtn) {
      trainBtn.disabled = true;
      trainBtn._originalText = trainBtn.textContent;
      trainBtn.textContent = "训练中...";
    }
  try {
    const payload = await fetchJson(`/api/train?source=${defaultSource}`, { method: "POST" });
    setStatus(`${payload.message}\n${JSON.stringify(payload.metrics, null, 2)}`);
    pushToast("模型训练完成", "success");
    await initializeDashboard();
  } finally {
    if (trainBtn) {
      trainBtn.disabled = false;
      trainBtn.textContent = trainBtn._originalText || "重新训练模型";
    }
  }
}

async function refreshRealData() {
  setStatus("正在启动真实数据后台刷新任务...");
  if (syncBtn) {
      syncBtn.disabled = true;
      syncBtn._originalText = syncBtn.textContent;
      syncBtn.textContent = "刷新中...";
    }
  try {
    const payload = await fetchJson(`/api/refresh-real-data?pool=${defaultPool}`, { method: "POST" });
    renderTaskStatus(payload.status);
    setStatus(`${payload.message}\n请等待后台脚本完成抓取和训练。`);
    pushToast("真实数据刷新任务已启动", "success");
    if (payload.status?.state === "running") startRefreshPolling();
  } finally {
    if (syncBtn) {
      syncBtn.disabled = false;
      syncBtn.textContent = syncBtn._originalText || "后台刷新真实数据";
    }
  }
}

function fillPortfolioForm(symbol, name, side = "buy") {
  if (portfolioSymbol instanceof HTMLInputElement) portfolioSymbol.value = symbol || "";
  if (portfolioName instanceof HTMLInputElement) portfolioName.value = name || "";
  if (portfolioSide instanceof HTMLSelectElement) portfolioSide.value = side;
  syncPortfolioPriceMode();
  switchPage("portfolio");
}

function handleHistoryJump(symbol, name) {
  if (searchResults instanceof HTMLElement) searchResults.innerHTML = "";
  if (stockSearchInput instanceof HTMLInputElement) stockSearchInput.blur();
  setStatus(`正在加载 ${symbol}${name ? ` ${name}` : ""} 的历史回看...`);
  loadHistory(symbol, state.selectedPeriod)
    .then((payload) => {
      if (!payload) return;
      setStatus(`已切换到 ${symbol}${name ? ` ${name}` : ""} 的历史回看。`);
    })
    .catch(async (error) => {
      if (state.selectedPeriod !== "day") {
        try {
          const payload = await loadHistory(symbol, "day");
          if (payload) {
            setStatus(`${symbol}${name ? ` ${name}` : ""} 当前周期加载失败，已自动回退到日线。`);
            pushToast("当前周期不可用，已自动回退到日线", "error");
            return;
          }
        } catch (fallbackError) {
          setStatus(`历史回看加载失败: ${fallbackError.message}`);
          pushToast(`历史回看失败: ${fallbackError.message}`, "error");
          return;
        }
      }
      setStatus(`历史回看加载失败: ${error.message}`);
      pushToast(`历史回看失败: ${error.message}`, "error");
    });
}

async function quickBuyFromSearch(symbol, name) {
  await buyPaperLot(symbol, name);
  if (searchResults instanceof HTMLElement) {
    searchResults.innerHTML = "";
  }
  if (stockSearchInput instanceof HTMLInputElement) {
    stockSearchInput.blur();
  }
  fillPortfolioForm(symbol, name, "buy");
  switchPage("portfolio");
}

refreshBtn?.addEventListener("click", () => {
  if (refreshBtn) {
    refreshBtn.disabled = true;
    refreshBtn._originalText = refreshBtn.textContent;
    refreshBtn.textContent = "刷新中...";
  }
  loadDashboard()
    .then(() => pushToast("候选股数据已刷新", "success"))
    .catch((error) => {
      setStatus(`候选股刷新失败: ${error.message}`);
      pushToast(`候选股刷新失败: ${error.message}`, "error");
    })
    .finally(() => {
      if (refreshBtn) {
        refreshBtn.disabled = false;
        refreshBtn.textContent = refreshBtn._originalText || "刷新候选股";
      }
    });
});

watchBtn?.addEventListener("click", () => {
  Promise.all([loadWatchlist(), loadFavorites(), loadPortfolio()])
    .then(() => setStatus("盯盘、自选与模拟盘快照已刷新。"))
    .catch((error) => setStatus(`盯盘刷新失败: ${error.message}`));
});

hotNewsRefreshBtnPage?.addEventListener("click", () => {
  state.hotNewsOffset = 0;
  state.hotNewsHasMore = true;
  loadHotNews(true, false)
    .then(() => setStatus("热点快报已刷新。"))
    .catch((error) => setStatus(`热点快报刷新失败: ${error.message}`));
});

hotNewsFilters?.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;
  const button = target.closest("[data-category]");
  if (!(button instanceof HTMLElement) || !button.dataset.category) return;
  selectHotNewsCategory(button.dataset.category)
    .then(() => setStatus(`热点快报已切换到 ${getHotNewsCategoryLabel(button.dataset.category)}。`))
    .catch((error) => setStatus(`热点快报分类筛选失败: ${error.message}`));
});

hotNewsScroll?.addEventListener("scroll", (event) => {
  const target = event.currentTarget;
  if (!(target instanceof HTMLElement)) return;
  const distanceToBottom = target.scrollHeight - target.scrollTop - target.clientHeight;
  if (distanceToBottom < 160 && !state.hotNewsLoading && state.hotNewsHasMore) {
    loadHotNews(false, true).catch((error) => setStatus(`热点快报继续加载失败: ${error.message}`));
  }
});

trainBtn?.addEventListener("click", () => {
  retrain().catch((error) => setStatus(`训练失败: ${error.message}`));
});

syncBtn?.addEventListener("click", () => {
  refreshRealData().catch((error) => setStatus(`真实数据后台刷新失败: ${error.message}`));
});

picksTable?.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;
  const viewButton = target.closest("[data-action='view']");
  if (viewButton instanceof HTMLElement && viewButton.dataset.symbol) {
    handleHistoryJump(viewButton.dataset.symbol, viewButton.dataset.name || "");
    return;
  }
  const buyButton = target.closest("[data-action='buy-paper']");
  if (buyButton instanceof HTMLElement && buyButton.dataset.symbol) {
    buyPaperLot(buyButton.dataset.symbol, buyButton.dataset.name || "")
      .then(() => fillPortfolioForm(buyButton.dataset.symbol, buyButton.dataset.name || "", "buy"))
      .catch((error) => setStatus(`模拟买入失败: ${error.message}`));
  }
});

watchTable?.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;
  const viewButton = target.closest("[data-action='view']");
  if (viewButton instanceof HTMLElement && viewButton.dataset.symbol) {
    handleHistoryJump(viewButton.dataset.symbol, viewButton.dataset.name || "");
    return;
  }
  const buyButton = target.closest("[data-action='buy-paper']");
  if (buyButton instanceof HTMLElement && buyButton.dataset.symbol) {
    buyPaperLot(buyButton.dataset.symbol, buyButton.dataset.name || "")
      .then(() => fillPortfolioForm(buyButton.dataset.symbol, buyButton.dataset.name || "", "buy"))
      .catch((error) => setStatus(`模拟买入失败: ${error.message}`));
  }
});

watchlistTable?.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;
  const viewButton = target.closest("[data-action='view']");
  if (viewButton instanceof HTMLElement && viewButton.dataset.symbol) {
    handleHistoryJump(viewButton.dataset.symbol, viewButton.dataset.name || "");
    return;
  }
  const buyButton = target.closest("[data-action='buy-paper']");
  if (buyButton instanceof HTMLElement && buyButton.dataset.symbol) {
    buyPaperLot(buyButton.dataset.symbol, buyButton.dataset.name || "")
      .then(() => fillPortfolioForm(buyButton.dataset.symbol, buyButton.dataset.name || "", "buy"))
      .catch((error) => setStatus(`模拟买入失败: ${error.message}`));
    return;
  }
  const removeButton = target.closest("[data-action='remove-favorite']");
  if (removeButton instanceof HTMLElement && removeButton.dataset.symbol) {
    removeFavorite(removeButton.dataset.symbol, removeButton.dataset.kind)
      .then(() => setStatus(`已从自选中移除 ${removeButton.dataset.symbol}。`))
      .catch((error) => setStatus(`移除自选失败: ${error.message}`));
  }
});

portfolioPositionsTable?.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;
  const viewButton = target.closest("[data-action='view']");
  if (viewButton instanceof HTMLElement && viewButton.dataset.symbol) {
    handleHistoryJump(viewButton.dataset.symbol, viewButton.dataset.name || "");
    return;
  }
  const sellButton = target.closest("[data-action='sell-paper']");
  if (sellButton instanceof HTMLElement && sellButton.dataset.symbol) {
    sellPaperLot(sellButton.dataset.symbol, sellButton.dataset.name || "", Number(sellButton.dataset.quantity || 100))
      .catch((error) => setStatus(`模拟卖出失败: ${error.message}`));
  }
});

historyTable?.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;
  const button = target.closest("[data-trade-date]");
  if (!(button instanceof HTMLElement) || !button.dataset.tradeDate) return;
  loadIntradayHistory(state.currentHistorySymbol, button.dataset.tradeDate)
    .then((payload) => {
      if (!payload) return;
      setStatus(payload.message || `已切换到 ${button.dataset.tradeDate} 的当日涨跌图。`);
    })
    .catch((error) => setStatus(`当日涨跌图加载失败: ${error.message}`));
});

// AI Stock Analysis flow
(function() {
  const searchInput = document.querySelector("#timelineSymbolInput");
  const searchBtn = document.querySelector("#analysisSearchBtn");
  const previewDiv = document.querySelector("#analysisStockPreview");
  const progressDiv = document.querySelector("#analysisProgress");
  const progressFill = document.querySelector("#analysisProgressFill");
  const progressText = document.querySelector("#analysisProgressText");
  const resultDiv = document.querySelector("#stockAnalysisResult");

  let currentSymbol = "";

  function doSearch() {
    const code = (searchInput?.value || "").trim();
    if (!code) return;
    currentSymbol = code;
    if (resultDiv) { resultDiv.innerHTML = ""; resultDiv.style.display = "none"; }
    if (previewDiv) { previewDiv.style.display = "block"; previewDiv.innerHTML = '<div class="placeholder-row" style="padding:8px">搜索中...</div>'; }
    if (progressDiv) progressDiv.style.display = "none";
    fetchJson("/api/stock-info/" + encodeURIComponent(code))
      .then((data) => {
        if (data && data.name && previewDiv) {
          const tone = getToneClassName(data.change_pct);
          previewDiv.innerHTML = '<div class="preview-card">'
            + '<div class="preview-left"><div class="preview-name">' + escapeHtml(data.name || code) + '</div><div class="preview-code">' + escapeHtml(data.symbol || code) + (data.date ? ' | ' + data.date : '') + '</div></div>'
            + '<div class="preview-mid"><div class="preview-price ' + tone + '">' + (data.price ?? "-") + '</div><div class="preview-change ' + tone + '">' + formatSignedPercent(data.change_pct) + '</div></div>'
            + '<button id="analysisStartBtn" class="btn btn-accent" type="button">AI 分析</button>'
            + '</div>';
          document.querySelector("#analysisStartBtn")?.addEventListener("click", startAnalysis);
        } else if (previewDiv) {
          previewDiv.innerHTML = '<div class="placeholder-row" style="padding:8px">未找到 "' + escapeHtml(code) + '"，请检查代码</div>';
        }
      })
      .catch(() => { if (previewDiv) previewDiv.innerHTML = '<div class="placeholder-row" style="padding:8px">搜索失败，请检查网络</div>'; });
  }

  function startAnalysis() {
    if (!currentSymbol) return;
    if (resultDiv) resultDiv.innerHTML = "";
    if (previewDiv) previewDiv.style.display = "none";
    if (progressDiv) progressDiv.style.display = "flex";
    const steps = [
      {pct: 10, text: "获取行情数据..."},
      {pct: 30, text: "计算技术指标..."},
      {pct: 50, text: "分析趋势与波动..."},
      {pct: 70, text: "查询模型信号..."},
      {pct: 85, text: "检索相关热点..."},
      {pct: 95, text: "生成分析报告..."},
    ];
    let stepIdx = 0;
    function nextStep() {
      if (stepIdx < steps.length) {
        const s = steps[stepIdx];
        if (progressFill) progressFill.style.width = s.pct + "%";
        if (progressText) progressText.textContent = s.text;
        stepIdx++;
        setTimeout(nextStep, 400 + Math.random() * 300);
      }
    }
    nextStep();

    fetchJson("/api/stock-analysis/" + encodeURIComponent(currentSymbol))
      .then((payload) => {
        // Wait for progress bar to finish
        setTimeout(() => {
          if (progressFill) progressFill.style.width = "100%";
          if (progressText) progressText.textContent = "分析完成";
          setTimeout(() => {
            if (progressDiv) progressDiv.style.display = "none";
            if (previewDiv) previewDiv.style.display = "block";
            if (resultDiv) resultDiv.style.display = "flex";
            renderStockAnalysis(payload);
          }, 500);
        }, 600);
      })
      .catch((error) => {
        if (progressDiv) progressDiv.style.display = "none";
        if (previewDiv) { previewDiv.style.display = "block"; previewDiv.innerHTML = '<div class="placeholder-row" style="padding:8px">分析失败: ' + escapeHtml(error.message) + '</div>'; }
      });
  }

  searchBtn?.addEventListener("click", doSearch);
  searchInput?.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); doSearch(); } });
})();

stockSearchInput?.addEventListener("input", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLInputElement)) return;
  if (state.searchTimer) window.clearTimeout(state.searchTimer);
  state.searchTimer = window.setTimeout(() => {
    state.searchTimer = null;
    searchStocks(target.value).catch((error) => setStatus(`搜索失败: ${error.message}`));
  }, 180);
});

stockSearchInput?.addEventListener("keydown", (event) => {
  if (event.key !== "Enter") return;
  event.preventDefault();
  if (!(event.currentTarget instanceof HTMLInputElement)) return;
  if (state.searchTimer) {
    window.clearTimeout(state.searchTimer);
    state.searchTimer = null;
  }
  searchStocks(event.currentTarget.value).catch((error) => setStatus(`搜索失败: ${error.message}`));
});

window.addEventListener("keydown", (event) => {
  if (event.key === "/" && !event.ctrlKey && !event.metaKey && !(document.activeElement instanceof HTMLInputElement)) {
    event.preventDefault();
    stockSearchInput?.focus();
    stockSearchInput?.select?.();
  }
});

searchResults?.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;
  const chip = target.closest("[data-suggestion]");
  if (chip instanceof HTMLElement && chip.dataset.suggestion) {
    if (stockSearchInput instanceof HTMLInputElement) {
      stockSearchInput.value = chip.dataset.suggestion;
      stockSearchInput.dispatchEvent(new Event("input", { bubbles: true }));
    }
    return;
  }
  const addButton = target.closest("[data-action='add-favorite']");
  if (addButton instanceof HTMLElement && addButton.dataset.symbol) {
    addFavorite(addButton.dataset.symbol, addButton.dataset.name || "", addButton.dataset.kind || "stock")
      .then(() => setStatus(`已添加 ${addButton.dataset.symbol} 到自选股。`))
      .catch((error) => setStatus(`添加自选失败: ${error.message}`));
    return;
  }
  const buyButton = target.closest("[data-action='buy-paper']");
  if (buyButton instanceof HTMLElement && buyButton.dataset.symbol) {
    quickBuyFromSearch(buyButton.dataset.symbol, buyButton.dataset.name || "")
      .then(() => setStatus(`${buyButton.dataset.symbol} 已买入并切到模拟盘。`))
      .catch((error) => {
        pushToast(`买入失败: ${error.message}`, "error");
        setStatus(`模拟买入失败: ${error.message}`);
      });
    return;
  }
  const row = target.closest("[data-action='view-row'], [data-action='view-search']");
  if (row instanceof HTMLElement && row.dataset.symbol) {
    handleHistoryJump(row.dataset.symbol, row.dataset.name || "");
  }
});

portfolioForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  const symbol = portfolioSymbol instanceof HTMLInputElement ? portfolioSymbol.value.trim() : "";
  const name = portfolioName instanceof HTMLInputElement ? portfolioName.value.trim() : "";
  const side = portfolioSide instanceof HTMLSelectElement ? portfolioSide.value : "buy";
  const quantity = portfolioQty instanceof HTMLInputElement ? Number(portfolioQty.value || 0) : 0;
  const priceMode = portfolioPriceMode instanceof HTMLSelectElement ? portfolioPriceMode.value : "live";
  const manualPrice = portfolioPrice instanceof HTMLInputElement && portfolioPrice.value ? Number(portfolioPrice.value) : null;
  submitPaperOrder({
    symbol,
    name,
    side,
    quantity,
    priceMode,
    price: priceMode === "manual" ? manualPrice : null,
  }).catch((error) => {
    pushToast(`提交失败: ${error.message}`, "error");
    setStatus(`提交模拟单失败: ${error.message}`);
  });
});

portfolioSettingsForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  savePortfolioSettings().catch((error) => setStatus(`保存交易设置失败: ${error.message}`));
});

portfolioPriceMode?.addEventListener("change", () => {
  syncPortfolioPriceMode();
});

portfolioResetBtn?.addEventListener("click", () => {
  if (!window.confirm("确定要重置本地模拟盘吗？这会清空当前现金、持仓和成交记录。")) {
    return;
  }
  resetPortfolio().catch((error) => setStatus(`重置模拟盘失败: ${error.message}`));
});

portfolioExportBtn?.addEventListener("click", () => {
  exportPortfolio().catch((error) => setStatus(`导出模拟盘失败: ${error.message}`));
});

portfolioImportBtn?.addEventListener("click", () => {
  importPortfolio().catch((error) => setStatus(`导入模拟盘失败: ${error.message}`));
});

portfolioImportFile?.addEventListener("change", () => {
  if (portfolioImportFile.files?.length) {
    importPortfolio().catch((error) => setStatus(`导入模拟盘失败: ${error.message}`));
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
  if (!(target instanceof HTMLElement)) return;
  const button = target.closest("[data-period]");
  if (!(button instanceof HTMLElement) || !button.dataset.period) return;
  loadHistory(state.currentHistorySymbol, button.dataset.period)
    .then(() => setStatus(`已切换到 ${periodLabelMap[button.dataset.period] || button.dataset.period}。`))
    .catch((error) => setStatus(`切换周期失败: ${error.message}`));
});

historyBackBtn?.addEventListener("click", () => {
  if (state.previousHistoryPayload) {
    renderHistoryPayload(state.previousHistoryPayload);
    setStatus("已返回 K 线图。");
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
  setStatus("历史图表缩放已重置。");
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
syncHotNewsFilterButton();
startMarketPolling();

if (backtestRunBtn instanceof HTMLButtonElement) {
  backtestRunBtn.addEventListener("click", () => { loadBacktest(); });
}

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
