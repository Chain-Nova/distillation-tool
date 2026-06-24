const taxonomyList = document.querySelector("#taxonomyList");
const positiveTaxonomyList = document.querySelector("#positiveTaxonomyList");
const form = document.querySelector("#taskForm");
const taskState = document.querySelector("#taskState");
const taskStatus = document.querySelector("#taskStatus");
const statusDot = document.querySelector("#statusDot");
const downloadLink = document.querySelector("#downloadLink");
const taskList = document.querySelector("#taskList");
const refreshTasks = document.querySelector("#refreshTasks");
const modelConfigSelect = document.querySelector("#modelConfigSelect");
const saveModelConfig = document.querySelector("#saveModelConfig");
const deleteModelConfig = document.querySelector("#deleteModelConfig");
const taskDetail = document.querySelector("#taskDetail");
const detailTitle = document.querySelector("#detailTitle");
const requestPayload = document.querySelector("#requestPayload");
const llmCallList = document.querySelector("#llmCallList");
const backToForm = document.querySelector("#backToForm");
const modeButtons = document.querySelectorAll(".mode-switch button");
const refusalFields = document.querySelector("#refusalFields");
const positiveFields = document.querySelector("#positiveFields");
const submitTask = document.querySelector("#submitTask");

let taxonomy = [];
let positiveTaxonomy = [];
let modelConfigs = [];
let pollTimer = null;
let detailTimer = null;
let activeTaskId = null;
let activeMode = "refusal";

function setStatus(state, status, mode = "") {
  taskState.textContent = state;
  taskStatus.textContent = status || "";
  statusDot.className = `status-dot ${mode}`;
}

function renderTaxonomy(items) {
  taxonomyList.innerHTML = "";
  items.forEach((item, index) => {
    const label = document.createElement("label");
    label.className = "tax-item";
    label.innerHTML = `
      <input type="checkbox" name="taxonomy" value="${index}" ${index === 3 ? "checked" : ""} />
      <span>
        <strong>${item.label_id} · ${item.risk_item}</strong>
        <small>${item.category}</small>
      </span>
    `;
    taxonomyList.appendChild(label);
  });
}

function renderPositiveTaxonomy(items) {
  positiveTaxonomyList.innerHTML = "";
  items.forEach((item, index) => {
    const label = document.createElement("label");
    label.className = "tax-item";
    label.innerHTML = `
      <input type="checkbox" name="positiveTaxonomy" value="${index}" ${index === 0 ? "checked" : ""} />
      <span>
        <strong>${item.name}</strong>
        <small>${item.label_id}</small>
      </span>
    `;
    positiveTaxonomyList.appendChild(label);
  });
}

function setMode(mode) {
  activeMode = mode;
  modeButtons.forEach((button) => button.classList.toggle("active", button.dataset.mode === mode));
  refusalFields.classList.toggle("hidden", mode !== "refusal");
  positiveFields.classList.toggle("hidden", mode !== "positive");
  submitTask.textContent = mode === "positive" ? "生成非拒答题" : "生成评测题";
}

function stateMode(state) {
  if (state === "SUCCESS") return "done";
  if (state === "FAILURE") return "";
  return state && state !== "PENDING" ? "running" : "";
}

function showTask(task) {
  activeTaskId = task.task_id;
  setStatus(task.state, task.status || `任务 ID：${task.task_id}`, stateMode(task.state));
  downloadLink.href = task.state === "SUCCESS" ? `/api/tasks/${task.task_id}/download` : "#";
  downloadLink.classList.toggle("disabled", task.state !== "SUCCESS");
  submitTask.disabled = task.state === "PROGRESS" || task.state === "STARTED" || task.state === "PENDING";
  renderTaskActive();
}

function showFormView() {
  taskDetail.classList.add("hidden");
  form.classList.remove("hidden");
  clearInterval(detailTimer);
}

function showDetailView() {
  form.classList.add("hidden");
  taskDetail.classList.remove("hidden");
}

function renderTaskActive() {
  [...taskList.querySelectorAll(".task-item")].forEach((button) => {
    button.classList.toggle("active", button.dataset.taskId === activeTaskId);
  });
}

function renderTasks(tasks) {
  taskList.innerHTML = "";
  if (!tasks.length) {
    const empty = document.createElement("p");
    empty.className = "empty-history";
    empty.textContent = "暂无任务";
    taskList.appendChild(empty);
    return;
  }
  tasks.forEach((task) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "task-item";
    button.dataset.taskId = task.task_id;
    const rows = task.rows_count ? `${task.rows_count} 行` : "未完成";
    const taskType = task.result_file && task.result_file.includes("positive") ? "非拒答题" : "拒答题";
    const shortId = task.task_id.slice(0, 8);
    button.innerHTML = `
      <div class="task-item-top">
        <strong>${task.state}</strong>
        <span>${rows}</span>
      </div>
      <div class="task-item-meta">${taskType} · ${shortId}</div>
      <div class="task-item-status">${task.status || ""}</div>
    `;
    button.addEventListener("click", () => {
      showTask(task);
      openTaskDetail(task.task_id);
    });
    taskList.appendChild(button);
  });
  renderTaskActive();
}

async function loadTasks({ restoreLatest = false } = {}) {
  const response = await fetch("/api/tasks");
  const tasks = await response.json();
  renderTasks(tasks);
  if (restoreLatest && tasks.length) {
    const latest = tasks[0];
    showTask(latest);
    if (latest.state !== "SUCCESS" && latest.state !== "FAILURE") {
      clearInterval(pollTimer);
      pollTimer = setInterval(() => pollTask(latest.task_id), 2500);
      pollTask(latest.task_id);
    }
  }
}

function renderTaskDetails(detail) {
  const { task, request, llm_calls: calls } = detail;
  const pageScroll = { x: window.scrollX, y: window.scrollY };
  const blockScroll = new Map(
    [...llmCallList.querySelectorAll("[data-scroll-key]")].map((block) => [
      block.dataset.scrollKey,
      { top: block.scrollTop, left: block.scrollLeft },
    ]),
  );

  showTask(task);
  detailTitle.textContent = task.task_id;
  requestPayload.textContent = JSON.stringify(request || {}, null, 2);

  if (!calls.length) {
    if (!llmCallList.querySelector(".empty-history")) {
      llmCallList.innerHTML = "";
      const empty = document.createElement("p");
      empty.className = "empty-history";
      empty.textContent = "暂无大模型请求。任务开始执行后会自动出现。";
      llmCallList.appendChild(empty);
    }
    window.scrollTo(pageScroll.x, pageScroll.y);
    return;
  }

  llmCallList.querySelector(".empty-history")?.remove();
  const seen = new Set();

  calls.forEach((call) => {
    seen.add(String(call.id));
    let item = llmCallList.querySelector(`[data-call-id="${call.id}"]`);
    if (!item) {
      item = document.createElement("article");
      item.className = "llm-call";
      item.dataset.callId = call.id;
      item.innerHTML = `
        <div class="llm-call-head">
          <strong></strong>
          <span></span>
        </div>
        <h3>System</h3>
        <pre class="prompt-block" data-role="system"></pre>
        <h3>User</h3>
        <pre class="prompt-block" data-role="user"></pre>
        <h3>Output</h3>
        <pre class="prompt-block" data-role="output"></pre>
      `;
      llmCallList.appendChild(item);
    }

    const output = call.error
      ? `ERROR:\n${call.error}`
      : call.response_text
        ? call.response_text
        : "请求中，等待模型返回...";
    item.querySelector(".llm-call-head strong").textContent = `#${call.id} ${call.step}`;
    item.querySelector(".llm-call-head span").textContent = call.model;

    const systemBlock = item.querySelector('[data-role="system"]');
    const userBlock = item.querySelector('[data-role="user"]');
    const outputBlock = item.querySelector('[data-role="output"]');
    systemBlock.dataset.scrollKey = `${call.id}:system`;
    userBlock.dataset.scrollKey = `${call.id}:user`;
    outputBlock.dataset.scrollKey = `${call.id}:output`;
    if (systemBlock.textContent !== (call.system_prompt || "")) systemBlock.textContent = call.system_prompt || "";
    if (userBlock.textContent !== (call.user_prompt || "")) userBlock.textContent = call.user_prompt || "";
    if (outputBlock.textContent !== output) outputBlock.textContent = output;
    outputBlock.classList.toggle("pending-output", !call.response_text && !call.error);
  });

  [...llmCallList.querySelectorAll(".llm-call")].forEach((item) => {
    if (!seen.has(item.dataset.callId)) item.remove();
  });

  [...llmCallList.querySelectorAll("[data-scroll-key]")].forEach((block) => {
    const saved = blockScroll.get(block.dataset.scrollKey);
    if (saved) {
      block.scrollTop = saved.top;
      block.scrollLeft = saved.left;
    }
  });
  window.scrollTo(pageScroll.x, pageScroll.y);
}

async function loadTaskDetail(taskId) {
  const response = await fetch(`/api/tasks/${taskId}/details`);
  if (!response.ok) {
    setStatus("加载失败", await response.text());
    return null;
  }
  const detail = await response.json();
  renderTaskDetails(detail);
  return detail;
}

async function openTaskDetail(taskId) {
  activeTaskId = taskId;
  showDetailView();
  clearInterval(pollTimer);
  clearInterval(detailTimer);
  const detail = await loadTaskDetail(taskId);
  const state = detail?.task?.state;
  if (state && state !== "SUCCESS" && state !== "FAILURE") {
    detailTimer = setInterval(() => loadTaskDetail(taskId), 2500);
  }
}

async function loadTaxonomy() {
  const response = await fetch("/api/taxonomy");
  taxonomy = await response.json();
  renderTaxonomy(taxonomy);
}

async function loadPositiveTaxonomy() {
  const response = await fetch("/api/positive-taxonomy");
  positiveTaxonomy = await response.json();
  renderPositiveTaxonomy(positiveTaxonomy);
}

function currentModelConfig() {
  const data = new FormData(form);
  return {
    base_url: data.get("baseUrl") || null,
    api_key: data.get("apiKey") || null,
    model: data.get("model") || null,
    judge_model: data.get("judgeModel") || null,
    temperature: Number(data.get("temperature")),
    max_tokens: Number(data.get("maxTokens")),
  };
}

function applyModelConfig(saved) {
  form.elements.configName.value = saved.name || "";
  form.elements.baseUrl.value = saved.config.base_url || "";
  form.elements.apiKey.value = saved.config.api_key || "";
  form.elements.model.value = saved.config.model || "";
  form.elements.judgeModel.value = saved.config.judge_model || "";
  form.elements.temperature.value = saved.config.temperature ?? 0.2;
  form.elements.maxTokens.value = saved.config.max_tokens ?? 1200;
}

function renderModelConfigs(items) {
  modelConfigs = items;
  const selected = modelConfigSelect.value;
  modelConfigSelect.innerHTML = '<option value="">选择配置</option>';
  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = item.name;
    modelConfigSelect.appendChild(option);
  });
  if (selected && items.some((item) => String(item.id) === selected)) {
    modelConfigSelect.value = selected;
  }
}

async function loadModelConfigs() {
  const response = await fetch("/api/model-configs");
  renderModelConfigs(await response.json());
}

function selectedTaxonomy() {
  return [...document.querySelectorAll('input[name="taxonomy"]:checked')].map((input) => taxonomy[Number(input.value)]);
}

function selectedPositiveLabels() {
  return [...document.querySelectorAll('input[name="positiveTaxonomy"]:checked')].map(
    (input) => positiveTaxonomy[Number(input.value)].label_id,
  );
}

function payloadFromForm() {
  const data = new FormData(form);
  return {
    test_type: data.get("testType"),
    seed_prompts: data.get("seedPrompts"),
    selected_taxonomy: selectedTaxonomy(),
    expansion_constraints: data.get("constraints"),
    variants_per_seed: Number(data.get("variantsPerSeed")),
    max_samples: Number(data.get("maxSamples")),
    max_concurrency: Number(data.get("maxConcurrency")),
    model_config: currentModelConfig(),
  };
}

function positivePayloadFromForm() {
  const data = new FormData(form);
  return {
    selected_labels: selectedPositiveLabels(),
    generation_prompt: data.get("positivePrompt"),
    questions_per_label: Number(data.get("positiveQuestionsPerLabel")),
    max_samples: Number(data.get("positiveMaxSamples")),
    max_concurrency: Number(data.get("positiveMaxConcurrency")),
    model_config: currentModelConfig(),
  };
}

async function pollTask(taskId) {
  const response = await fetch(`/api/tasks/${taskId}`);
  const task = await response.json();
  showTask(task);
  if (task.state === "SUCCESS") {
    setStatus("完成", `生成成功，可以下载 Excel。`, "done");
    downloadLink.href = `/api/tasks/${taskId}/download`;
    downloadLink.classList.remove("disabled");
    clearInterval(pollTimer);
    clearInterval(detailTimer);
    submitTask.disabled = false;
    loadTasks();
    return;
  }
  if (task.state === "FAILURE") {
    setStatus("失败", task.error || "任务执行失败，请检查 worker 日志。");
    clearInterval(pollTimer);
    clearInterval(detailTimer);
    submitTask.disabled = false;
    loadTasks();
    return;
  }
  setStatus(task.state, task.status || "任务执行中。", "running");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const isPositive = activeMode === "positive";
  const payload = isPositive ? positivePayloadFromForm() : payloadFromForm();
  if (!isPositive && !payload.seed_prompts.trim()) {
    setStatus("缺少母题", "请至少填写一条母题。");
    return;
  }
  if (!isPositive && !payload.selected_taxonomy.length) {
    setStatus("缺少标签", "请至少选择一个标签。");
    return;
  }
  if (isPositive && !payload.selected_labels.length) {
    setStatus("缺少标签", "请至少选择一个非拒答题标签。");
    return;
  }

  submitTask.disabled = true;
  downloadLink.classList.add("disabled");
  setStatus("提交中", "正在创建 Celery 任务。", "running");

  const response = await fetch(isPositive ? "/api/positive-tasks" : "/api/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.text();
    setStatus("提交失败", error);
    submitTask.disabled = false;
    return;
  }

  const { task_id: taskId } = await response.json();
  activeTaskId = taskId;
  await loadTasks();
  setStatus("已入队", `任务 ID：${taskId}`, "running");
  clearInterval(pollTimer);
  pollTimer = setInterval(() => pollTask(taskId), 2500);
  openTaskDetail(taskId);
  pollTask(taskId);
});

refreshTasks.addEventListener("click", () => loadTasks());
backToForm.addEventListener("click", showFormView);
modeButtons.forEach((button) => button.addEventListener("click", () => setMode(button.dataset.mode)));

saveModelConfig.addEventListener("click", async () => {
  const name = form.elements.configName.value.trim();
  if (!name) {
    setStatus("缺少配置名称", "请先填写模型配置名称。");
    return;
  }
  const response = await fetch("/api/model-configs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, config: currentModelConfig() }),
  });
  if (!response.ok) {
    setStatus("保存失败", await response.text());
    return;
  }
  const saved = await response.json();
  await loadModelConfigs();
  modelConfigSelect.value = saved.id;
  setStatus("配置已保存", `已保存模型配置：${saved.name}`);
});

modelConfigSelect.addEventListener("change", async () => {
  if (!modelConfigSelect.value) return;
  const response = await fetch(`/api/model-configs/${modelConfigSelect.value}`);
  if (!response.ok) {
    setStatus("加载失败", await response.text());
    return;
  }
  const saved = await response.json();
  applyModelConfig(saved);
  setStatus("配置已加载", `已加载模型配置：${saved.name}`);
});

deleteModelConfig.addEventListener("click", async () => {
  if (!modelConfigSelect.value) {
    setStatus("未选择配置", "请先选择要删除的模型配置。");
    return;
  }
  const selectedName = modelConfigSelect.options[modelConfigSelect.selectedIndex].textContent;
  const response = await fetch(`/api/model-configs/${modelConfigSelect.value}`, { method: "DELETE" });
  if (!response.ok) {
    setStatus("删除失败", await response.text());
    return;
  }
  modelConfigSelect.value = "";
  await loadModelConfigs();
  setStatus("配置已删除", `已删除模型配置：${selectedName}`);
});

Promise.all([loadTaxonomy(), loadPositiveTaxonomy(), loadTasks(), loadModelConfigs()]).catch((error) => {
  setStatus("加载失败", String(error));
});
