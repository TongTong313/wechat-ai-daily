// ==================== 全局状态 ====================
const state = {
  mode: "api",
  autoScroll: true,
  running: false,
  logLines: [],
  startTime: null,
  lastRunning: false,
  logClearAt: null,
};

// ==================== DOM 引用 ====================
const dom = {
  navItems: document.querySelectorAll(".nav-item"),
  views: document.querySelectorAll(".view"),
  segmentedItems: document.querySelectorAll(".segmented-item"),
  statusText: document.getElementById("status-text"),
  statusDetail: document.getElementById("status-detail"),
  progressFill: document.getElementById("progress-fill"),
  progressPercent: document.getElementById("progress-percent"),
  elapsedTime: document.getElementById("elapsed-time"),
  logConsole: document.getElementById("log-console"),
  autoScroll: document.getElementById("auto-scroll"),
  clearLogs: document.getElementById("clear-logs"),
  saveConfig: document.getElementById("save-config"),
  stopWorkflow: document.getElementById("stop-workflow"),
  refreshFiles: document.getElementById("refresh-files"),
  mdSelect: document.getElementById("md-file-select"),
  htmlSelect: document.getElementById("html-file-select"),
  mdList: document.getElementById("md-file-list"),
  htmlList: document.getElementById("html-file-list"),
  connectionStatus: document.getElementById("connection-status"),
  toggleTheme: document.getElementById("toggle-theme"),
  showLegal: document.getElementById("show-legal"),
  legalModal: document.getElementById("legal-modal"),
  acceptLegal: document.getElementById("accept-legal"),
  declineLegal: document.getElementById("decline-legal"),
  accountInput: document.getElementById("account-input"),
  accountList: document.getElementById("account-list"),
  accountAdd: document.getElementById("account-add"),
  accountRemove: document.getElementById("account-remove"),
  accountReset: document.getElementById("account-reset"),
  articleUrlInput: document.getElementById("article-url-input"),
  articleUrlList: document.getElementById("article-url-list"),
  articleUrlAdd: document.getElementById("article-url-add"),
  articleUrlRemove: document.getElementById("article-url-remove"),
  articleUrlReset: document.getElementById("article-url-reset"),
  articleUrlError: document.getElementById("article-url-error"),
  tabBtns: document.querySelectorAll(".tab-btn"),
  monitorContents: document.querySelectorAll(".monitor-content"),
  stepCollect: document.getElementById("status-collect"),
  stepGenerate: document.getElementById("status-generate"),
  stepPublish: document.getElementById("status-publish"),
};

// ==================== 基础工具函数 ====================
const $ = (selector) => document.querySelector(selector);

const toLines = (value) =>
  value
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);

const setHidden = (element, hidden) => {
  if (!element) return;
  element.classList.toggle("hidden", hidden);
};

const pad2 = (value) => String(value).padStart(2, "0");

const formatDate = (date) => {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
};

const formatDateTime = (date) => {
  return `${formatDate(date)} ${pad2(date.getHours())}:${pad2(date.getMinutes())}`;
};

const toDateTimeLocal = (value) => {
  if (!value) return "";
  return String(value).replace(" ", "T");
};

const fromDateTimeLocal = (value) => {
  if (!value) return null;
  return String(value).replace("T", " ");
};

// 列表组件：统一管理增删、渲染与校验
const getListValues = (container) => {
  if (!container) return [];
  return Array.from(container.querySelectorAll(".list-item"))
    .map((item) => item.dataset.value)
    .filter((value) => Boolean(value));
};

const renderList = (container, values, emptyText) => {
  if (!container) return;
  container.innerHTML = "";
  if (!values || values.length === 0) {
    const empty = document.createElement("div");
    empty.className = "list-empty";
    empty.textContent = emptyText || "暂无数据";
    container.appendChild(empty);
    return;
  }
  values.forEach((value) => {
    const row = document.createElement("label");
    row.className = "list-item";
    row.dataset.value = value;
    row.innerHTML = `
      <input type="checkbox" />
      <span>${value}</span>
    `;
    container.appendChild(row);
  });
};

const createListManager = ({
  input,
  container,
  addButton,
  removeButton,
  resetButton,
  errorElement,
  emptyText,
  validate,
}) => {
  const setError = (message) => {
    if (!errorElement) return;
    errorElement.textContent = message || "";
  };

  const getValues = () => getListValues(container);

  const setValues = (values) => {
    renderList(container, values, emptyText);
  };

  const addValue = () => {
    if (!input) return;
    const value = input.value.trim();
    if (!value) return;
    if (validate && !validate(value)) {
      setError("仅支持 mp.weixin.qq.com 的公众号文章链接");
      return;
    }
    setError("");
    const values = getValues();
    if (values.includes(value)) {
      input.value = "";
      return;
    }
    values.push(value);
    setValues(values);
    input.value = "";
  };

  const removeSelected = () => {
    if (!container) return;
    const remaining = [];
    container.querySelectorAll(".list-item").forEach((item) => {
      const checkbox = item.querySelector("input[type='checkbox']");
      if (checkbox && checkbox.checked) {
        return;
      }
      remaining.push(item.dataset.value);
    });
    setValues(remaining);
  };

  const resetValues = () => {
    setValues([]);
    setError("");
  };

  addButton?.addEventListener("click", addValue);
  input?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      addValue();
    }
  });
  removeButton?.addEventListener("click", removeSelected);
  resetButton?.addEventListener("click", resetValues);

  return { getValues, setValues, resetValues };
};

// 公众号名称与文章链接列表
const accountListManager = createListManager({
  input: dom.accountInput,
  container: dom.accountList,
  addButton: dom.accountAdd,
  removeButton: dom.accountRemove,
  resetButton: dom.accountReset,
  emptyText: "尚未添加公众号名称",
});

const articleUrlListManager = createListManager({
  input: dom.articleUrlInput,
  container: dom.articleUrlList,
  addButton: dom.articleUrlAdd,
  removeButton: dom.articleUrlRemove,
  resetButton: dom.articleUrlReset,
  errorElement: dom.articleUrlError,
  emptyText: "尚未添加文章链接",
  validate: (value) => value.includes("mp.weixin.qq.com"),
});

// 时间范围快捷按钮
document.querySelectorAll("[data-quick]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const action = btn.dataset.quick;
    const now = new Date();
    if (action === "api-today") {
      const start = new Date(now);
      start.setHours(0, 0, 0, 0);
      const end = new Date(now);
      end.setHours(23, 59, 0, 0);
      $("#start-date").value = toDateTimeLocal(formatDateTime(start));
      $("#end-date").value = toDateTimeLocal(formatDateTime(end));
    }
    if (action === "api-yesterday") {
      const start = new Date(now);
      start.setDate(start.getDate() - 1);
      start.setHours(0, 0, 0, 0);
      const end = new Date(now);
      end.setDate(end.getDate() - 1);
      end.setHours(23, 59, 0, 0);
      $("#start-date").value = toDateTimeLocal(formatDateTime(start));
      $("#end-date").value = toDateTimeLocal(formatDateTime(end));
    }
    if (action === "rpa-today") {
      $("#target-date").value = formatDate(now);
    }
    if (action === "rpa-yesterday") {
      const yesterday = new Date(now);
      yesterday.setDate(yesterday.getDate() - 1);
      $("#target-date").value = formatDate(yesterday);
    }
  });
});

// 敏感字段显隐切换
document.querySelectorAll("[data-toggle]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const targetId = btn.dataset.toggle;
    const input = document.getElementById(targetId);
    if (!input) return;
    const isPassword = input.type === "password";
    input.type = isPassword ? "text" : "password";
    btn.textContent = isPassword ? "隐藏" : "显示";
  });
});

const sourceLabel = (source) => {
  switch (source) {
    case "config":
      return "config.yaml";
    case "env_file":
      return ".env 文件";
    case "system":
      return "系统环境变量";
    default:
      return "未配置";
  }
};

const markDirty = (element) => {
  if (element) {
    element.dataset.changed = "true";
  }
};

const getSensitiveValue = (elementId) => {
  const el = document.getElementById(elementId);
  if (!el) return null;
  if (el.dataset.changed === "true") {
    return el.value.trim();
  }
  return null;
};

// 日志过滤：清空后忽略旧日志（仅前端侧）
const parseLogTime = (value) => {
  if (!value) return null;
  const match = String(value).match(/(\d{2}):(\d{2}):(\d{2})/);
  if (!match) return null;
  const now = new Date();
  const hours = Number(match[1]);
  const minutes = Number(match[2]);
  const seconds = Number(match[3]);
  return new Date(now.getFullYear(), now.getMonth(), now.getDate(), hours, minutes, seconds, 0).getTime();
};

const getLogTimestamp = (entry) => {
  if (!entry) return null;
  if (entry.timestamp) {
    const ts = Date.parse(entry.timestamp);
    return Number.isNaN(ts) ? null : ts;
  }
  return parseLogTime(entry.time) ?? parseLogTime(entry.text);
};

const shouldIgnoreLog = (entry) => {
  if (!state.logClearAt) return false;
  const ts = getLogTimestamp(entry);
  if (!ts) return false;
  return ts <= state.logClearAt;
};

const loadLogClearAt = () => {
  const stored = localStorage.getItem("logClearAt");
  state.logClearAt = stored ? Number(stored) : null;
};

const clearLogHistory = () => {
  state.logLines = [];
  dom.logConsole.innerHTML = "";
  state.logClearAt = Date.now();
  localStorage.setItem("logClearAt", String(state.logClearAt));
};

// ==================== 视图切换 ====================
dom.navItems.forEach((item) => {
  item.addEventListener("click", () => {
    dom.navItems.forEach((btn) => btn.classList.remove("active"));
    item.classList.add("active");
    const view = item.dataset.view;
    dom.views.forEach((section) => {
      section.classList.toggle("active", section.dataset.view === view);
    });
  });
});

// ==================== 监控面板 Tab 切换 ====================
dom.tabBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    dom.tabBtns.forEach((b) => b.classList.remove("active"));
    dom.monitorContents.forEach((c) => c.classList.remove("active"));
    
    btn.classList.add("active");
    const tabId = btn.dataset.tab;
    const content = document.getElementById(`tab-content-${tabId}`);
    if (content) {
      content.classList.add("active");
    }
  });
});

// ==================== 模式切换 ====================
function setMode(mode) {
  state.mode = mode;
  dom.segmentedItems.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.mode === mode);
  });
  document.querySelectorAll(".mode-api").forEach((el) => setHidden(el, mode !== "api"));
  document.querySelectorAll(".mode-rpa").forEach((el) => setHidden(el, mode !== "rpa"));
}

dom.segmentedItems.forEach((btn) => {
  btn.addEventListener("click", () => setMode(btn.dataset.mode));
});

// ==================== 日志控制 ====================
dom.autoScroll.addEventListener("change", (event) => {
  state.autoScroll = event.target.checked;
});

dom.clearLogs.addEventListener("click", () => {
  clearLogHistory();
});

function appendLogLine(entry) {
  if (shouldIgnoreLog(entry)) {
    return;
  }
  state.logLines.push(entry);
  const line = document.createElement("div");
  line.className = `log-line ${entry.level}`;
  const text = entry.text || "";
  const hasPrefix = /^\[\d{2}:\d{2}:\d{2}\]/.test(text);
  line.textContent = hasPrefix ? text : `[${entry.time}] ${text}`;
  dom.logConsole.appendChild(line);
  if (state.autoScroll) {
    dom.logConsole.scrollTop = dom.logConsole.scrollHeight;
  }
}

// ==================== 进度更新 ====================
function updateProgress(data) {
  if (!data) return;
  const progress = Number(data.progress ?? 0);
  const wasRunning = state.running;
  dom.statusText.textContent = data.status || "就绪";
  dom.statusDetail.textContent = data.detail || "等待执行";
  dom.progressFill.style.width = `${progress}%`;
  dom.progressPercent.textContent = `${progress}%`;
  
  state.running = Boolean(data.running);
  
  // 计时：开始时间由后端传入
  if (data.started_at && state.running) {
      // Parse "YYYY-MM-DD HH:mm:ss"
      state.startTime = new Date(data.started_at.replace(" ", "T"));
  } else if (!state.running) {
      state.startTime = null;
      dom.elapsedTime.textContent = "00:00";
  }

  toggleActionButtons(state.running);
  
  // 自动刷新文件列表（任务结束时触发一次）
  if (wasRunning && !state.running) {
    refreshFiles();
  }

  // 更新步骤状态
  updateStepIndicators(data);
}

function updateStepIndicators(data) {
  if (!dom.stepCollect || !dom.stepGenerate || !dom.stepPublish) {
    return;
  }

  const workflow = data.workflow || "";
  const progress = Number(data.progress ?? 0);
  const statusText = data.status || "";
  const running = Boolean(data.running);
  const isError = Boolean(data.error) || statusText.includes("失败");
  const isCancelled = statusText.includes("已取消");
  const isFinished = !running && (progress >= 100 || statusText.includes("全部完成") || statusText === "完成");

  resetStepStatuses();

  // 规则：full 按进度区间分阶段；单独流程将未参与步骤标记为未执行
  if (!workflow) {
    return;
  }

  if (workflow === "full") {
    if (isFinished) {
      setStepStatus("collect", "done");
      setStepStatus("generate", "done");
      setStepStatus("publish", "done");
      return;
    }

    const stage = getStageFromProgress(progress);
    const currentStep = stage === 1 ? "collect" : stage === 2 ? "generate" : "publish";

    if (stage >= 2) {
      setStepStatus("collect", "done");
    }
    if (stage >= 3) {
      setStepStatus("generate", "done");
    }

    const currentState = isError
      ? "error"
      : isCancelled
        ? "cancelled"
        : running
          ? "active"
          : progress > 0
            ? "done"
            : "waiting";
    setStepStatus(currentStep, currentState);
    return;
  }

  const steps = ["collect", "generate", "publish"];
  if (!steps.includes(workflow)) {
    return;
  }

  steps.forEach((step) => {
    setStepStatus(step, step === workflow ? "waiting" : "skipped");
  });

  const finalState = isError
    ? "error"
    : isCancelled
      ? "cancelled"
      : running
        ? "active"
        : !running && (progress >= 100 || statusText.includes("完成"))
          ? "done"
          : "waiting";
  setStepStatus(workflow, finalState);
}

function getStageFromProgress(progress) {
  // full 流程按进度划分阶段
  if (progress >= 66) return 3;
  if (progress >= 33) return 2;
  return 1;
}

const stepLabels = {
  waiting: "等待",
  active: "进行中",
  done: "完成",
  skipped: "未执行",
  error: "失败",
  cancelled: "已取消",
};

const stepClassMap = {
  active: "step-status--active",
  done: "step-status--done",
  skipped: "step-status--skipped",
  error: "step-status--error",
  cancelled: "step-status--warning",
};

function resetStepStatuses() {
  setStepStatus("collect", "waiting");
  setStepStatus("generate", "waiting");
  setStepStatus("publish", "waiting");
}

function setStepStatus(key, stateKey) {
  const elMap = {
    collect: dom.stepCollect,
    generate: dom.stepGenerate,
    publish: dom.stepPublish,
  };
  const el = elMap[key];
  if (!el) return;
  el.textContent = stepLabels[stateKey] || stepLabels.waiting;
  el.className = "step-status";
  const cls = stepClassMap[stateKey];
  if (cls) {
    el.classList.add(cls);
  }
}

function toggleActionButtons(running) {
  document.querySelectorAll('[data-action="start"]').forEach((btn) => {
    btn.disabled = running;
    if (running) {
        btn.style.opacity = "0.5";
        btn.style.cursor = "not-allowed";
    } else {
        btn.style.opacity = "1";
        btn.style.cursor = "pointer";
    }
  });
  dom.stopWorkflow.disabled = !running;
  if (!running) {
      dom.stopWorkflow.style.opacity = "0.5";
      dom.stopWorkflow.style.cursor = "not-allowed";
  } else {
      dom.stopWorkflow.style.opacity = "1";
      dom.stopWorkflow.style.cursor = "pointer";
  }
}

// Timer for elapsed time
setInterval(() => {
    if (state.running && state.startTime) {
        const now = new Date();
        const diff = Math.floor((now - state.startTime) / 1000);
        if (diff >= 0) {
            const mins = Math.floor(diff / 60).toString().padStart(2, '0');
            const secs = (diff % 60).toString().padStart(2, '0');
            dom.elapsedTime.textContent = `${mins}:${secs}`;
        }
    }
}, 1000);


// ==================== 配置读写 ====================
function collectConfigPayload() {
  return {
    target_date: $("#target-date")?.value?.trim() || null,
    start_date: fromDateTimeLocal($("#start-date")?.value?.trim()) || null,
    end_date: fromDateTimeLocal($("#end-date")?.value?.trim()) || null,
    article_urls: getListValues(dom.articleUrlList),
    api_config: {
      token: getSensitiveValue("api-token"),
      cookie: getSensitiveValue("api-cookie"),
      account_names: getListValues(dom.accountList),
    },
    llm: {
      model: $("#llm-model")?.value?.trim() || null,
      api_key: getSensitiveValue("api-key"),
      thinking_budget: $("#thinking-budget")?.value?.trim()
        ? Number($("#thinking-budget").value.trim())
        : null,
      enable_thinking: $("#enable-thinking")?.checked ?? null,
    },
    vlm: {
      model: $("#vlm-model")?.value?.trim() || null,
    },
    publish_config: {
      appid: getSensitiveValue("wechat-appid"),
      appsecret: getSensitiveValue("wechat-appsecret"),
      author: $("#publish-author")?.value?.trim() || null,
      cover_path: $("#cover-path")?.value?.trim() || null,
      default_title: $("#default-title")?.value?.trim() || null,
    },
    gui_config: {
      search_website: $("#template-search")?.value?.trim() || null,
      three_dots: $("#template-dots")?.value?.trim() || null,
      turnback: $("#template-turnback")?.value?.trim() || null,
    },
    save_options: {
      api_key_to_env: $("#save-api-key-env")?.checked || false,
      api_token_to_env: $("#save-token-env")?.checked || false,
      api_cookie_to_env: $("#save-cookie-env")?.checked || false,
      appid_to_env: $("#save-appid-env")?.checked || false,
      appsecret_to_env: $("#save-appsecret-env")?.checked || false,
    },
  };
}

async function loadConfig() {
  const response = await fetch("/api/config");
  const data = await response.json();
  const config = data.config || {};
  const model = config.model_config || {};
  const llm = model.LLM || {};
  const vlm = model.VLM || {};
  const apiConfig = config.api_config || {};
  const publish = config.publish_config || {};
  const guiConfig = config.GUI_config || config.gui_config || {};
  const sources = data.sources || {};

  $("#target-date").value = config.target_date || "";
  $("#start-date").value = toDateTimeLocal(config.start_date || "");
  $("#end-date").value = toDateTimeLocal(config.end_date || "");

  // 敏感字段：按来源填充占位，避免误写入配置文件
  const tokenSource = sources.api_token;
  const cookieSource = sources.api_cookie;
  const apiKeySource = sources.api_key;
  const appidSource = sources.wechat_appid;
  const appsecretSource = sources.wechat_appsecret;

  const tokenInput = $("#api-token");
  tokenInput.value = tokenSource === "config" ? data.masked?.api_token || apiConfig.token || "" : "";
  tokenInput.placeholder = tokenSource ? `已配置（${sourceLabel(tokenSource)}）` : "留空则读取环境变量";
  tokenInput.dataset.changed = "false";

  const cookieInput = $("#api-cookie");
  cookieInput.value = cookieSource === "config" ? data.masked?.api_cookie || apiConfig.cookie || "" : "";
  cookieInput.placeholder = cookieSource ? `已配置（${sourceLabel(cookieSource)}）` : "留空则读取环境变量";
  cookieInput.dataset.changed = "false";

  $("#llm-model").value = llm.model || "";
  $("#vlm-model").value = vlm.model || "";

  const apiKeyInput = $("#api-key");
  apiKeyInput.value = apiKeySource === "config" ? data.masked?.api_key || llm.api_key || "" : "";
  apiKeyInput.placeholder = apiKeySource ? `已配置（${sourceLabel(apiKeySource)}）` : "留空则读取环境变量";
  apiKeyInput.dataset.changed = "false";

  $("#thinking-budget").value = llm.thinking_budget ?? "";
  $("#enable-thinking").checked = llm.enable_thinking ?? true;

  const appidInput = $("#wechat-appid");
  appidInput.value = appidSource === "config" ? data.masked?.wechat_appid || publish.appid || "" : "";
  appidInput.placeholder = appidSource ? `已配置（${sourceLabel(appidSource)}）` : "留空则读取环境变量";
  appidInput.dataset.changed = "false";

  const appsecretInput = $("#wechat-appsecret");
  appsecretInput.value = appsecretSource === "config" ? data.masked?.wechat_appsecret || publish.appsecret || "" : "";
  appsecretInput.placeholder = appsecretSource ? `已配置（${sourceLabel(appsecretSource)}）` : "留空则读取环境变量";
  appsecretInput.dataset.changed = "false";

  $("#publish-author").value = publish.author || "";
  $("#cover-path").value = publish.cover_path || "";
  $("#default-title").value = publish.default_title || "";

  $("#template-search").value = guiConfig.search_website || "";
  $("#template-dots").value = guiConfig.three_dots || "";
  $("#template-turnback").value = guiConfig.turnback || "";

  // 根据来源设置默认保存位置
  $("#save-token-env").checked = tokenSource === "env_file";
  $("#save-cookie-env").checked = cookieSource === "env_file";
  $("#save-api-key-env").checked = apiKeySource === "env_file";
  $("#save-appid-env").checked = appidSource === "env_file";
  $("#save-appsecret-env").checked = appsecretSource === "env_file";

  accountListManager.setValues(apiConfig.account_names || []);
  articleUrlListManager.setValues(config.article_urls || []);
}

dom.saveConfig.addEventListener("click", async () => {
  const payload = collectConfigPayload();
  dom.saveConfig.disabled = true;
  try {
    await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } finally {
    dom.saveConfig.disabled = false;
  }
});

// ==================== 文件列表 ====================
function renderFileList(container, files) {
  container.innerHTML = "";
  if (!files || files.length === 0) {
    const empty = document.createElement("div");
    empty.className = "file-item";
    empty.textContent = "暂无文件";
    empty.style.color = "var(--text-muted)";
    empty.style.justifyContent = "center";
    container.appendChild(empty);
    return;
  }
  files.forEach((file) => {
    const row = document.createElement("div");
    row.className = "file-item";
    row.innerHTML = `
      <div class="file-meta">
        <div class="file-name">${file.name}</div>
        <div class="file-info">${file.mtime} · ${(file.size / 1024).toFixed(1)} KB</div>
      </div>
      <div class="file-actions">
        <button class="ghost-button" data-preview="${file.path}">预览</button>
      </div>
    `;
    row.querySelector("[data-preview]").addEventListener("click", () => {
      window.open(`/api/file?path=${encodeURIComponent(file.path)}`, "_blank");
    });
    container.appendChild(row);
  });
}

function renderFileSelect(select, files) {
  const currentVal = select.value;
  select.innerHTML = `<option value="">请选择文件...</option>`;
  files.forEach((file) => {
    const option = document.createElement("option");
    option.value = file.path;
    option.textContent = file.name;
    select.appendChild(option);
  });
  if (currentVal) {
      select.value = currentVal;
  }
}

async function refreshFiles() {
  const [mdRes, htmlRes] = await Promise.all([
    fetch("/api/files?file_type=markdown"),
    fetch("/api/files?file_type=html"),
  ]);
  const mdData = await mdRes.json();
  const htmlData = await htmlRes.json();
  renderFileList(dom.mdList, mdData.files);
  renderFileList(dom.htmlList, htmlData.files);
  renderFileSelect(dom.mdSelect, mdData.files);
  renderFileSelect(dom.htmlSelect, htmlData.files);
}

dom.refreshFiles.addEventListener("click", refreshFiles);

// ==================== 工作流触发 ====================
document.querySelectorAll('[data-action="start"]').forEach((btn) => {
  btn.addEventListener("click", async () => {
    const workflow = btn.dataset.workflow;
    const payload = {
      workflow,
      mode: state.mode,
      markdown_file: dom.mdSelect.value || null,
      html_file: dom.htmlSelect.value || null,
      title: $("#default-title")?.value?.trim() || null,
      target_date: $("#target-date")?.value?.trim() || null,
      start_time: fromDateTimeLocal($("#start-date")?.value?.trim()) || null,
      end_time: fromDateTimeLocal($("#end-date")?.value?.trim()) || null,
    };

    if (workflow === "generate" && !payload.markdown_file) {
      alert("请先选择 Markdown 文件");
      return;
    }
    if (workflow === "publish" && !payload.html_file) {
      alert("请先选择 HTML 文件");
      return;
    }

    await fetch("/api/workflow/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  });
});

dom.stopWorkflow.addEventListener("click", async () => {
  await fetch("/api/workflow/stop", { method: "POST" });
});

// ==================== 敏感字段变更标记 ====================
["api-token", "api-cookie", "api-key", "wechat-appid", "wechat-appsecret"].forEach((id) => {
  const el = document.getElementById(id);
  if (el) {
    el.addEventListener("input", () => markDirty(el));
  }
});

// ==================== WebSocket 实时更新 ====================
let socket = null;
let retryTimer = null;

function connectSocket() {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(`${protocol}://${window.location.host}/ws/stream`);

  socket.addEventListener("open", () => {
    dom.connectionStatus.textContent = "● 已连接";
    dom.connectionStatus.style.color = "var(--accent)";
  });

  socket.addEventListener("message", (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === "log") {
        appendLogLine(data);
      }
      if (data.type === "progress") {
        updateProgress(data);
      }
    } catch (err) {
      console.warn("解析消息失败", err);
    }
  });

  socket.addEventListener("close", () => {
    dom.connectionStatus.textContent = "● 已断开";
    dom.connectionStatus.style.color = "var(--danger)";
    retryTimer = setTimeout(connectSocket, 2000);
  });
}

// ==================== 法律声明 ====================
function initLegalNotice() {
  const accepted = localStorage.getItem("legalAccepted") === "true";
  if (!accepted) {
    dom.legalModal.classList.remove("hidden");
  }
  dom.showLegal.addEventListener("click", () => {
    dom.legalModal.classList.remove("hidden");
  });
  dom.acceptLegal.addEventListener("click", () => {
    localStorage.setItem("legalAccepted", "true");
    dom.legalModal.classList.add("hidden");
  });
  dom.declineLegal.addEventListener("click", () => {
    dom.legalModal.classList.remove("hidden");
    alert("必须同意法律声明才能继续使用");
  });
}

// ==================== 主题切换 ====================
function initTheme() {
  const saved = localStorage.getItem("theme") || "dark";
  document.body.classList.toggle("theme-light", saved === "light");
  dom.toggleTheme.addEventListener("click", () => {
    const isLight = document.body.classList.toggle("theme-light");
    localStorage.setItem("theme", isLight ? "light" : "dark");
  });
}

// ==================== 初始化 ====================
async function init() {
  initLegalNotice();
  initTheme();
  loadLogClearAt();
  setMode("api");
  toggleActionButtons(false);
  await loadConfig();
  await refreshFiles();
  const statusRes = await fetch("/api/status");
  updateProgress(await statusRes.json());
  connectSocket();
}

init();