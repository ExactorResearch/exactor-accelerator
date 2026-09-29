/**
 * Exactor Accelerator — Web Control Center Application
 * Cyber-Logic Glassmorphism Design System Implementation
 */

const API_BASE = "";

// Global State
let currentRuleData = null;
let currentJevSchema = null;
let activeThreshold = 0.80;

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  loadSystemStatus();
  loadExactorRules();
  loadJevSchema();
  refreshLedgerTable();
  fillLiveEventPreset('fraud_high');

  // Initialize View Mode (Business by default)
  const savedMode = localStorage.getItem("exactor_accelerator_view_mode") || "business";
  switchViewMode(savedMode);

  // Periodic ledger refresh every 6 seconds
  setInterval(refreshLedgerTable, 6000);
});

// ----------------------------------------------------------------------------
// VIEW MODE (BUSINESS VIEW VS TECHNICAL VIEW)
// ----------------------------------------------------------------------------
function switchViewMode(mode) {
  const btnBiz = document.getElementById("btn-mode-business");
  const btnTech = document.getElementById("btn-mode-tech");

  if (mode === "business") {
    document.body.classList.remove("view-mode-tech");
    document.body.classList.add("view-mode-business");
    if (btnBiz) {
      btnBiz.className = "mode-btn flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all bg-primary-container text-on-primary-container shadow-[inset_0_1px_0_0_rgba(255,255,255,0.12)] active";
    }
    if (btnTech) {
      btnTech.className = "mode-btn flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold text-on-surface-variant hover:text-on-surface hover:bg-surface-container/30 transition-all";
    }
    localStorage.setItem("exactor_accelerator_view_mode", "business");
  } else {
    document.body.classList.remove("view-mode-business");
    document.body.classList.add("view-mode-tech");
    if (btnTech) {
      btnTech.className = "mode-btn flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all bg-primary-container text-on-primary-container shadow-[inset_0_1px_0_0_rgba(255,255,255,0.12)] active";
    }
    if (btnBiz) {
      btnBiz.className = "mode-btn flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold text-on-surface-variant hover:text-on-surface hover:bg-surface-container/30 transition-all";
    }
    localStorage.setItem("exactor_accelerator_view_mode", "tech");
  }
}

// ----------------------------------------------------------------------------
// TAB & WORKFLOW NAVIGATION
// ----------------------------------------------------------------------------
function switchTab(tabId) {
  const tabBtns = document.querySelectorAll(".tab-btn");
  const stepCards = document.querySelectorAll(".step-card");
  const tabPanes = document.querySelectorAll(".tab-pane");

  tabBtns.forEach((b) => {
    if (b.dataset.tab === tabId) {
      b.className = "tab-btn active h-full flex items-center gap-1.5 px-2 border-b-2 border-primary-container text-primary-container font-semibold transition-colors";
    } else {
      b.className = "tab-btn h-full flex items-center gap-1.5 px-2 border-b-2 border-transparent text-on-surface-variant hover:text-on-surface transition-colors";
    }
  });

  stepCards.forEach((s) => {
    const isTarget = s.dataset.tab === tabId;
    if (isTarget) {
      s.classList.add("active");
      s.classList.remove("bg-surface-container-high/30", "border-outline-variant/30");
      s.classList.add("bg-primary-container/10", "border-primary-container");
    } else {
      s.classList.remove("active", "bg-primary-container/10", "border-primary-container");
      s.classList.add("bg-surface-container-high/30", "border-outline-variant/30");
    }
  });

  tabPanes.forEach((p) => {
    if (p.id === tabId) {
      p.classList.remove("hidden");
      p.classList.add("active");
    } else {
      p.classList.add("hidden");
      p.classList.remove("active");
    }
  });

  window.scrollTo({ top: 0, behavior: "smooth" });
}

function setupTabs() {
  const stepCards = document.querySelectorAll(".step-card");
  stepCards.forEach((card) => {
    card.addEventListener("click", () => {
      switchTab(card.dataset.tab);
    });
  });
}

// ----------------------------------------------------------------------------
// SYSTEM STATUS TELEMETRY
// ----------------------------------------------------------------------------
async function loadSystemStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/system/status`);
    if (!res.ok) return;
    const data = await res.json();

    const engineNameEl = document.getElementById("status-engine-name");
    if (engineNameEl) engineNameEl.textContent = data.engine_type || "EXACTOR Core";

    const modelNameEl = document.getElementById("status-model-name");
    if (modelNameEl) modelNameEl.textContent = data.jev_model.includes("Simulator") ? "Jev (RLCD Sim)" : "Jev (Live API)";

    const ruleVerEl = document.getElementById("status-rule-ver");
    if (ruleVerEl) ruleVerEl.textContent = `v${data.active_rule_version}`;

    const dimEl = document.getElementById("status-engine-dim");
    if (dimEl) dimEl.textContent = `B^${data.rules_count ? Math.max(10, data.rules_count) : 32}`;
  } catch (err) {
    console.error("Error loading status:", err);
  }
}

// ----------------------------------------------------------------------------
// STEP 1: HISTORICAL INGESTION & EXACTOR RULES
// ----------------------------------------------------------------------------
async function loadExactorRules() {
  try {
    const res = await fetch(`${API_BASE}/api/exactor/rules`);
    if (!res.ok) return;
    const data = await res.json();
    currentRuleData = data;

    // Formula & Explanation
    const formulaDisplay = document.getElementById("formula-display");
    if (formulaDisplay) formulaDisplay.textContent = data.formula_expr || "FALSE";

    const explanationDisplay = document.getElementById("explanation-display");
    if (explanationDisplay) explanationDisplay.textContent = data.explanation || "";

    // Metrics
    const kEl = document.getElementById("metric-k");
    if (kEl) kEl.textContent = `${data.variables ? data.variables.length : 32} vars`;

    const initMintermsEl = document.getElementById("metric-initial-minterms");
    if (initMintermsEl) initMintermsEl.textContent = data.initial_minterms;

    const finalTermsEl = document.getElementById("metric-final-terms");
    if (finalTermsEl) finalTermsEl.textContent = data.final_terms;

    const compEl = document.getElementById("metric-compression");
    if (compEl) compEl.textContent = `${(data.compression_ratio * 100).toFixed(1)}%`;

    const xorEl = document.getElementById("metric-xor-count");
    if (xorEl) xorEl.textContent = (data.xor_clauses || []).length;

    const execTimeEl = document.getElementById("metric-exec-time");
    if (execTimeEl) execTimeEl.textContent = `${data.stats ? data.stats.execution_time_ms || 0.4 : 0.4} ms`;

    // Propositions Table
    const tbody = document.getElementById("tbody-propositions");
    if (tbody) {
      tbody.innerHTML = "";
      (data.propositions || []).forEach((prop, idx) => {
        const row = document.createElement("tr");
        row.className = "hover:bg-surface-container-high/30 transition-colors";
        row.innerHTML = `
          <td class="py-2 px-3 font-mono text-secondary font-bold">p<sub>${idx}</sub></td>
          <td class="py-2 px-3 font-mono text-primary font-medium">${prop.name}</td>
          <td class="py-2 px-3 text-on-surface-variant">${prop.source_col}</td>
          <td class="py-2 px-3 font-mono text-xs text-outline">${prop.description}</td>
        `;
        tbody.appendChild(row);
      });
    }

    loadSystemStatus();
  } catch (err) {
    console.error("Error loading Exactor rules:", err);
  }
}

async function loadSamplePreset(presetType) {
  const presetMap = {
    fraud: { id: "btn-preset-fraud", target: "is_fraud", fill: "fraud_high" },
    sre: { id: "btn-preset-sre", target: "trigger_mitigation", fill: "sre_incident" },
    churn: { id: "btn-preset-churn", target: "churn", fill: "churn_risk" },
    soc: { id: "btn-preset-soc", target: "block_ip_address", fill: "soc_attack" },
    triage: { id: "btn-preset-triage", target: "urgent_icu_triage", fill: "triage_icu" },
    conversations: { id: "btn-preset-conversations", target: "escalate_to_supervisor", fill: "chat_angry" },
  };

  // Update button visual styles
  document.querySelectorAll(".btn-preset-rich").forEach((btn) => {
    btn.classList.remove("border-primary-container", "bg-primary-container/10");
  });

  const selected = presetMap[presetType] || presetMap.fraud;
  const activeBtn = document.getElementById(selected.id);
  if (activeBtn) {
    activeBtn.classList.add("border-primary-container", "bg-primary-container/10");
  }

  const targetColInput = document.getElementById("input-target-col");
  if (targetColInput) targetColInput.value = selected.target;

  const discoveryBtn = document.getElementById("btn-run-discovery");
  if (discoveryBtn) {
    discoveryBtn.disabled = true;
    discoveryBtn.innerHTML = `<span class="material-symbols-outlined text-sm animate-spin" data-icon="sync">sync</span> Binarizando a B^32...`;
  }

  const maxVars = document.getElementById("input-max-vars")?.value || 32;
  try {
    const res = await fetch(`${API_BASE}/api/ingest/sample?sample_type=${presetType}&max_variables=${maxVars}`, {
      method: "POST",
    });
    if (!res.ok) throw new Error(await res.text());
    await loadExactorRules();
    await loadJevSchema();
    fillLiveEventPreset(selected.fill);
  } catch (err) {
    alert(`Error al cargar preset: ${err.message}`);
  } finally {
    if (discoveryBtn) {
      discoveryBtn.disabled = false;
      discoveryBtn.innerHTML = `<span class="material-symbols-outlined text-sm" data-icon="bolt">bolt</span> Descubrir Reglas`;
    }
  }
}

async function handleFileUpload(e) {
  e.preventDefault();
  const fileInput = document.getElementById("input-dataset-file");
  const targetCol = document.getElementById("input-target-col").value.trim();
  const maxVars = document.getElementById("input-max-vars").value;

  if (!fileInput.files.length) {
    alert("Por favor selecciona un archivo CSV o JSON.");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  formData.append("target_col", targetCol);
  formData.append("max_variables", maxVars);

  const discoveryBtn = document.getElementById("btn-run-discovery");
  if (discoveryBtn) {
    discoveryBtn.disabled = true;
    discoveryBtn.innerHTML = `<span class="material-symbols-outlined text-sm animate-spin" data-icon="sync">sync</span> Minimizando en Rust HPC...`;
  }

  try {
    const res = await fetch(`${API_BASE}/api/ingest/file`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Error en la carga.");
    }
    await loadExactorRules();
    await loadJevSchema();
    alert("Initial ingestion and EXACTOR logical discovery completed successfully!");
  } catch (err) {
    alert(`Error: ${err.message}`);
  } finally {
    if (discoveryBtn) {
      discoveryBtn.disabled = false;
      discoveryBtn.innerHTML = `<span class="material-symbols-outlined text-sm" data-icon="bolt">bolt</span> Descubrir Reglas`;
    }
  }
}

// ----------------------------------------------------------------------------
// STEP 2: JEV TYPED SCHEMA CONTRACTS & CHOICE CUSTOMIZER
// ----------------------------------------------------------------------------
let currentCustomChoices = {};

async function loadJevSchema() {
  try {
    const res = await fetch(`${API_BASE}/api/jev/schema`);
    if (!res.ok) return;
    const data = await res.json();
    currentJevSchema = data;

    const questions = data.questions_schema || {};

    // Noul (Reserved for EXACTOR governance)
    const noulEl = document.getElementById("preview-noul-instructions");
    if (noulEl && questions.criterio_logico) {
      noulEl.textContent = questions.criterio_logico.instructions || "";
    }

    // Choice
    const choiceEl = document.getElementById("preview-choice-criteria");
    const choicesCriteria = questions.accion_recomendada?.criteria || {};
    if (choiceEl) {
      choiceEl.textContent = JSON.stringify(choicesCriteria, null, 2);
    }

    // Populate custom choices editor
    currentCustomChoices = data.custom_choices || choicesCriteria;
    renderCustomChoicesForm(currentCustomChoices);

    // Score
    const scoreEl = document.getElementById("preview-score-criteria");
    if (scoreEl && questions.calibracion_criticidad) {
      scoreEl.textContent = JSON.stringify(questions.calibracion_criticidad.criteria || {}, null, 2);
    }

    // JSON Payload
    const payloadEl = document.getElementById("jev-payload-preview");
    if (payloadEl) {
      payloadEl.textContent = JSON.stringify(data.sample_payload_preview, null, 2);
    }
  } catch (err) {
    console.error("Error loading Jev schema:", err);
  }
}

function renderCustomChoicesForm(choicesMap) {
  const container = document.getElementById("custom-choices-form-list");
  if (!container) return;

  container.innerHTML = "";
  const entries = Object.entries(choicesMap || {});

  if (entries.length === 0) {
    container.innerHTML = `<div class="p-3 text-center text-on-surface-variant font-sans">No hay opciones personalizadas. Agrega una nueva opción.</div>`;
    return;
  }

  entries.forEach(([name, desc], idx) => {
    const row = document.createElement("div");
    row.className = "choice-row grid grid-cols-1 md:grid-cols-12 gap-2 p-2 rounded-lg bg-surface-container/60 border border-outline-variant/30 items-center";
    row.innerHTML = `
      <div class="md:col-span-4">
        <input type="text" value="${escapeHtml(name)}" placeholder="NOMBRE_ACCION" class="choice-name w-full bg-surface-container-high border border-outline-variant/40 rounded px-2.5 py-1.5 font-bold text-xs text-primary-container focus:border-primary-container focus:outline-none uppercase" />
      </div>
      <div class="md:col-span-7">
        <input type="text" value="${escapeHtml(desc || '')}" placeholder="Business criterion para JEV (ej. Si el riesgo es alto...)" class="choice-desc w-full bg-surface-container-high border border-outline-variant/40 rounded px-2.5 py-1.5 text-xs text-on-surface focus:border-primary-container focus:outline-none font-sans" />
      </div>
      <div class="md:col-span-1 flex justify-end">
        <button type="button" class="text-on-surface-variant hover:text-error p-1 rounded hover:bg-surface-container transition-colors" onclick="removeCustomChoiceRow(this)" title="Eliminar opción">
          <span class="material-symbols-outlined text-sm" data-icon="delete">delete</span>
        </button>
      </div>
    `;
    container.appendChild(row);
  });
}

function addCustomChoiceRow() {
  const container = document.getElementById("custom-choices-form-list");
  if (!container) return;

  const row = document.createElement("div");
  row.className = "choice-row grid grid-cols-1 md:grid-cols-12 gap-2 p-2 rounded-lg bg-surface-container/60 border border-primary-container/40 items-center animate-fade-in";
  row.innerHTML = `
    <div class="md:col-span-4">
      <input type="text" value="NUEVA_ACCION_NEGOCIO" placeholder="NOMBRE_ACCION" class="choice-name w-full bg-surface-container-high border border-outline-variant/40 rounded px-2.5 py-1.5 font-bold text-xs text-primary-container focus:border-primary-container focus:outline-none uppercase" />
    </div>
    <div class="md:col-span-7">
      <input type="text" value="Specific criterion to execute this action" placeholder="Business criterion..." class="choice-desc w-full bg-surface-container-high border border-outline-variant/40 rounded px-2.5 py-1.5 text-xs text-on-surface focus:border-primary-container focus:outline-none font-sans" />
    </div>
    <div class="md:col-span-1 flex justify-end">
      <button type="button" class="text-on-surface-variant hover:text-error p-1 rounded hover:bg-surface-container transition-colors" onclick="removeCustomChoiceRow(this)" title="Eliminar opción">
        <span class="material-symbols-outlined text-sm" data-icon="delete">delete</span>
      </button>
    </div>
  `;
  container.appendChild(row);
}

function removeCustomChoiceRow(btn) {
  const row = btn.closest(".choice-row");
  if (row) {
    row.remove();
  }
}

async function saveCustomChoices() {
  const container = document.getElementById("custom-choices-form-list");
  const msgEl = document.getElementById("custom-choices-save-msg");
  if (!container) return;

  const rows = container.querySelectorAll(".choice-row");
  const choices = {};

  rows.forEach((row) => {
    const name = row.querySelector(".choice-name")?.value.trim().toUpperCase();
    const desc = row.querySelector(".choice-desc")?.value.trim();
    if (name) {
      choices[name] = desc || `Business action: ${name}`;
    }
  });

  if (Object.keys(choices).length === 0) {
    alert("You must define at least one Choice option for Jev.");
    return;
  }

  try {
    if (msgEl) msgEl.textContent = "Updating Choice catalog...";
    const res = await fetch(`${API_BASE}/api/jev/choices`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ choices }),
    });

    if (res.ok) {
      if (msgEl) {
        msgEl.textContent = `✓ ${Object.keys(choices).length} opciones Choice guardadas y calibradas con Jev.`;
        msgEl.className = "text-[11px] text-secondary font-sans font-bold";
      }
      await loadJevSchema();
      setTimeout(() => {
        if (msgEl) msgEl.textContent = "";
      }, 3000);
    } else {
      const err = await res.json();
      if (msgEl) {
        msgEl.textContent = `Error: ${err.detail || 'Fallo al guardar'}`;
        msgEl.className = "text-[11px] text-error font-sans";
      }
    }
  } catch (err) {
    if (msgEl) msgEl.textContent = `Error: ${err.message}`;
  }
}

async function resetDefaultChoices() {
  if (!confirm("Do you want to reset default options for this scenario?")) return;
  // Trigger schema reload by clearing custom choices
  try {
    await fetch(`${API_BASE}/api/jev/choices`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ choices: {} }),
    });
    await loadJevSchema();
  } catch (e) {
    console.error("Error resetting choices:", e);
  }
}

function copyPayloadJson() {
  const code = document.getElementById("jev-payload-preview")?.textContent;
  if (!code) return;
  navigator.clipboard.writeText(code).then(() => {
    alert("Payload JSON de Jev copiado al portapapeles.");
  });
}

// ----------------------------------------------------------------------------
// STEP 3: LIVE DECISION SIMULATOR & EXECUTION
// ----------------------------------------------------------------------------
function updateThresholdLabel(val) {
  activeThreshold = parseFloat(val) / 100.0;
  const lbl = document.getElementById("lbl-threshold");
  if (lbl) lbl.textContent = `${val}%`;
}

function fillLiveEventPreset(type) {
  const textarea = document.getElementById("textarea-event-state");
  if (!textarea) return;

  const presets = {
    chat_angry: {
      user_message: "Me cobraron dos veces la suscripción este mes en mi tarjeta de crédito y nadie me responde los correos. Es una estafa, cancelen mi cuenta y devuélvanme el dinero inmediatamente o voy a defensa del consumidor.",
      channel: "web_chat",
      customer_tier: "VIP"
    },
    chat_friendly: {
      user_message: "Hola, buenos días. ¿Me podrían indicar cuáles son los medios de pago disponibles y los horarios de atención telefónica? Muchas gracias por su ayuda.",
      channel: "whatsapp",
      customer_tier: "STANDARD"
    },
    fraud_high: {
      amount: 3450.00,
      velocity_1h: 6,
      country_risk: "HIGH",
      device_trust: 0.12,
      failed_pin_attempts: 3,
      is_new_device: 1
    },
    fraud_safe: {
      amount: 28.50,
      velocity_1h: 1,
      country_risk: "LOW",
      device_trust: 0.96,
      failed_pin_attempts: 0,
      is_new_device: 0
    },
    sre_incident: {
      latency_ms: 410.0,
      error_rate_pct: 15.2,
      cpu_usage_pct: 93.5,
      retry_bursts: 5,
      service_tier: "TIER_1_CRITICAL"
    },
    churn_risk: {
      tenure_months: 2,
      monthly_charges: 104.50,
      support_tickets_30d: 4,
      contract_type: "MONTH_TO_MONTH",
      has_tech_support: 0,
      payment_method: "ELECTRONIC_CHECK"
    },
    soc_attack: {
      failed_logins_5m: 14,
      packet_rate_kpps: 165.0,
      port_scan_count: 92,
      country_reputation: "MALICIOUS",
      is_tor_exit_node: 1,
      privileged_account_targeted: 1
    },
    triage_icu: {
      heart_rate_bpm: 148,
      systolic_bp: 198,
      spo2_pct: 83,
      pain_score: 9,
      age_group: "GERIATRIC"
    },
    edge_case: {
      amount: 720.00,
      velocity_1h: 2,
      country_risk: "MEDIUM",
      device_trust: 0.52,
      failed_pin_attempts: 1,
      is_new_device: 1
    }
  };

  const selected = presets[type] || presets.fraud_high;
  textarea.value = JSON.stringify(selected, null, 2);
}

let procTimerInterval = null;
let toastTimeout = null;

function showProcessingModal() {
  const modal = document.getElementById("modal-processing");
  if (!modal) return;
  
  modal.classList.add("active");
  const timerEl = document.getElementById("proc-timer");
  const startTime = Date.now();
  if (timerEl) timerEl.textContent = "0.0s";

  if (procTimerInterval) clearInterval(procTimerInterval);
  procTimerInterval = setInterval(() => {
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    if (timerEl) timerEl.textContent = `${elapsed}s`;
  }, 100);

  // Dynamic status rows in modal
  const step1 = document.getElementById("proc-step-row-1");
  const step2 = document.getElementById("proc-step-row-2");
  const step3 = document.getElementById("proc-step-row-3");
  if (step1) step1.className = "flex items-center justify-between text-xs font-mono p-2 rounded bg-surface-container-high/60 border border-secondary/30";
  if (step2) step2.className = "flex items-center justify-between text-xs font-mono p-2 rounded bg-surface-container-high/40 border border-primary/40 text-primary animate-pulse";
  if (step3) step3.className = "flex items-center justify-between text-xs font-mono p-2 rounded bg-surface-container-high/20 border border-outline-variant/10 text-on-surface-variant/40";
}

function hideProcessingModal() {
  const modal = document.getElementById("modal-processing");
  if (modal) modal.classList.remove("active");
  if (procTimerInterval) {
    clearInterval(procTimerInterval);
    procTimerInterval = null;
  }
}

function showCompletionToast(data) {
  const toast = document.getElementById("toast-complete");
  if (!toast) return;

  const actionEl = document.getElementById("toast-action");
  const latencyEl = document.getElementById("toast-latency");
  const iconEl = document.getElementById("toast-icon");

  if (actionEl) actionEl.textContent = data.chosen_action || "EJECUTADO";
  if (latencyEl) latencyEl.textContent = `${Math.round(data.latency_ms || 0)} ms`;

  if (data.autonomous_action_executed) {
    toast.className = "fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-4 rounded-xl bg-surface-container-highest/95 border-l-4 border-l-error border border-error/30 shadow-2xl backdrop-blur-xl transition-all duration-300 show";
    if (iconEl) {
      iconEl.className = "material-symbols-outlined text-error text-2xl animate-pulse";
      iconEl.textContent = "shield";
    }
  } else {
    toast.className = "fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-4 rounded-xl bg-surface-container-highest/95 border-l-4 border-l-secondary border border-secondary/30 shadow-2xl backdrop-blur-xl transition-all duration-300 show";
    if (iconEl) {
      iconEl.className = "material-symbols-outlined text-secondary text-2xl";
      iconEl.textContent = "verified";
    }
  }

  if (toastTimeout) clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {
    dismissToast();
  }, 6000);
}

function dismissToast() {
  const toast = document.getElementById("toast-complete");
  if (toast) toast.classList.remove("show");
  if (toastTimeout) {
    clearTimeout(toastTimeout);
    toastTimeout = null;
  }
}

async function submitLiveQuery() {
  const textarea = document.getElementById("textarea-event-state");
  if (!textarea) return;

  let eventState;
  try {
    eventState = JSON.parse(textarea.value);
  } catch (e) {
    alert("Error en el formato JSON del estado del evento.");
    return;
  }

  const btn = document.getElementById("btn-submit-live-query");
  const originalText = btn ? btn.innerHTML : "";
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="material-symbols-outlined text-base animate-spin" data-icon="sync">sync</span> Evaluando en EXACTOR HPC...`;
  }

  showProcessingModal();

  try {
    const res = await fetch(`${API_BASE}/api/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        state: eventState,
        confidence_threshold: activeThreshold,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Error in evaluation.");
    }

    const data = await res.json();
    renderLiveDecision(data);
    refreshLedgerTable();
    showCompletionToast(data);
  } catch (err) {
    alert(`Error: ${err.message}`);
  } finally {
    hideProcessingModal();
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = originalText;
    }
  }
}

// Alias for stitch prototype onclick compatibility
function runLiveEvaluation() {
  submitLiveQuery();
}

function renderLiveDecision(data) {
  // Latency & Rule Version
  const latEl = document.getElementById("decision-latency");
  if (latEl) latEl.textContent = `${Math.round(data.latency_ms)} ms`;

  const verEl = document.getElementById("decision-rule-ver");
  if (verEl) verEl.textContent = `${data.rule_version}`;

  const prob = data.criterio_logico_prob;

  // Autonomous Banner
  const banner = document.getElementById("banner-autonomous-status");
  const bannerIcon = document.getElementById("banner-icon");
  const bannerTitle = document.getElementById("banner-title");
  const bannerDesc = document.getElementById("banner-desc");

  // Determine state category directly from authoritative backend response
  const status = data.decision_status || (data.exact_boolean_evaluation === 1 ? "CRITICAL" : "SAFE");
  const isCriticalAction = status === "CRITICAL";
  const isReviewAction = status === "REVIEW";
  const isSafeAction = status === "SAFE";

  // Banner dynamic styling
  if (banner) {
    if (isCriticalAction) {
      banner.className = "cyber-glass-active rounded-xl p-5 border-l-4 border-l-error border-y border-r border-outline-variant/30 relative";
      if (bannerIcon) {
        bannerIcon.className = "px-2 py-0.5 text-[10px] font-mono font-bold rounded bg-error-container/60 text-error border border-error/40 uppercase tracking-wider";
        bannerIcon.textContent = data.autonomous_action_executed ? "AUTONOMOUS ACTION: PREVENTIVE BLOCK EXECUTED" : "ALERTA CRÍTICA DE RIESGO";
      }
      if (bannerTitle) {
        bannerTitle.className = "text-lg md:text-xl font-bold text-error tracking-tight";
        bannerTitle.textContent = `Critical Case: [${data.chosen_action}]`;
      }
    } else if (isReviewAction) {
      banner.className = "cyber-glass-active rounded-xl p-5 border-l-4 border-l-primary-container border-y border-r border-outline-variant/30 relative";
      if (bannerIcon) {
        bannerIcon.className = "px-2 py-0.5 text-[10px] font-mono font-bold rounded bg-primary-container/40 text-primary-container border border-primary-container/40 uppercase tracking-wider";
        bannerIcon.textContent = "REVIEW REQUIRED (2FA / MANUAL)";
      }
      if (bannerTitle) {
        bannerTitle.className = "text-lg md:text-xl font-bold text-primary-container tracking-tight";
        bannerTitle.textContent = `Borderline Case: [${data.chosen_action}]`;
      }
    } else {
      banner.className = "cyber-glass-active rounded-xl p-5 border-l-4 border-l-secondary border-y border-r border-outline-variant/30 relative";
      if (bannerIcon) {
        bannerIcon.className = "px-2 py-0.5 text-[10px] font-mono font-bold rounded bg-secondary-container/40 text-secondary border border-secondary/40 uppercase tracking-wider";
        bannerIcon.textContent = data.autonomous_action_executed ? "AUTONOMOUS ACTION: TRANSACTION APPROVED" : "TRANSACCIÓN HABITUAL SEGURA";
      }
      if (bannerTitle) {
        bannerTitle.className = "text-lg md:text-xl font-bold text-secondary tracking-tight";
        bannerTitle.textContent = `Safe Operation: [${data.chosen_action}]`;
      }
    }
    if (bannerDesc) bannerDesc.textContent = data.action_details;
  }

  // Executive Decision Cards
  const cardDiag = document.getElementById("card-exec-diagnosis");
  const cardAct = document.getElementById("card-exec-action");
  const cardReason = document.getElementById("card-exec-reason");

  const execDiagVal = document.getElementById("exec-diagnosis-val");
  const execDiagSub = document.getElementById("exec-diagnosis-sub");
  const execDiagIcon = document.getElementById("exec-diagnosis-icon");
  const execDiagHeaderIcon = document.getElementById("exec-diag-header-icon");

  const execActVal = document.getElementById("exec-action-val");
  const execActSub = document.getElementById("exec-action-sub");
  const execActHeaderIcon = document.getElementById("exec-act-header-icon");
  const execTouchMode = document.getElementById("exec-touch-mode");
  const execEndpoint = document.getElementById("exec-endpoint-val");
  const execImpact = document.getElementById("exec-impact-val");

  const execReasonVal = document.getElementById("exec-reason-val");
  const execCondStatus = document.getElementById("exec-cond-status");
  const execFormalRes = document.getElementById("exec-formal-res");
  const barCerteza = document.getElementById("bar-certeza-progress");

  if (isCriticalAction) {
    // CRITICAL / HIGH RISK
    if (cardDiag) cardDiag.className = "cyber-glass rounded-xl p-4 border-t-2 border-t-error border-x border-b border-outline-variant/30 flex flex-col justify-between group hover:border-error/50 transition-all";
    if (cardAct) cardAct.className = "cyber-glass rounded-xl p-4 border-t-2 border-t-error border-x border-b border-outline-variant/30 flex flex-col justify-between group hover:border-error/50 transition-all";
    if (cardReason) cardReason.className = "cyber-glass rounded-xl p-4 border-t-2 border-t-error border-x border-b border-outline-variant/30 flex flex-col justify-between group hover:border-error/50 transition-all";

    if (execDiagVal) {
      execDiagVal.textContent = "CRITICAL";
      execDiagVal.className = "text-xl font-bold text-error tracking-tight";
    }
    if (execDiagSub) execDiagSub.textContent = `Riesgo Inmediato (${(prob * 100).toFixed(1)}% Certeza)`;
    if (execDiagIcon) execDiagIcon.className = "w-2.5 h-2.5 rounded-full bg-error animate-ping";
    if (execDiagHeaderIcon) {
      execDiagHeaderIcon.className = "material-symbols-outlined text-error text-sm";
      execDiagHeaderIcon.textContent = "traffic";
    }

    if (execActVal) {
      execActVal.textContent = data.chosen_action || "BLOQUEAR_TRANSACCION";
      execActVal.className = "inline-block px-3 py-1 rounded bg-error/15 border border-error text-error font-mono font-bold text-xs tracking-wide glow-pink";
    }
    if (execActSub) execActSub.textContent = `Automatic containment execution (Confidence ${(data.confidence * 100).toFixed(1)}% >= Umbral ${(activeThreshold * 100).toFixed(0)}%).`;
    if (execActHeaderIcon) {
      execActHeaderIcon.className = "material-symbols-outlined text-error text-sm";
      execActHeaderIcon.textContent = "bolt";
    }
    if (execTouchMode) {
      execTouchMode.textContent = "ZERO HUMAN TOUCH";
      execTouchMode.className = "text-[10px] font-mono text-error font-bold";
    }
    if (execEndpoint) execEndpoint.textContent = data.action_endpoint || "POST api.gateway/v1/freeze";
    if (execImpact) {
      execImpact.textContent = "Riesgo Mitigado";
      execImpact.className = "text-error font-bold";
    }

    if (execCondStatus) {
      execCondStatus.textContent = "REGLA DE RIESGO ACTIVA";
      execCondStatus.className = "text-xs font-mono text-error font-bold";
    }
    if (execFormalRes) execFormalRes.textContent = "Verified Disjunction (100%)";
  } else if (isReviewAction) {
    // REVIEW / AMBIGUOUS
    if (cardDiag) cardDiag.className = "cyber-glass rounded-xl p-4 border-t-2 border-t-primary-container border-x border-b border-outline-variant/30 flex flex-col justify-between group hover:border-primary-container/50 transition-all";
    if (cardAct) cardAct.className = "cyber-glass rounded-xl p-4 border-t-2 border-t-primary-container border-x border-b border-outline-variant/30 flex flex-col justify-between group hover:border-primary-container/50 transition-all";
    if (cardReason) cardReason.className = "cyber-glass rounded-xl p-4 border-t-2 border-t-primary-container border-x border-b border-outline-variant/30 flex flex-col justify-between group hover:border-primary-container/50 transition-all";

    if (execDiagVal) {
      execDiagVal.textContent = "MANUAL REVIEW";
      execDiagVal.className = "text-xl font-bold text-primary-container tracking-tight";
    }
    if (execDiagSub) execDiagSub.textContent = `Dual Approval (${(prob * 100).toFixed(1)}% Uncertainty)`;
    if (execDiagIcon) execDiagIcon.className = "w-2.5 h-2.5 rounded-full bg-primary-container animate-pulse";
    if (execDiagHeaderIcon) {
      execDiagHeaderIcon.className = "material-symbols-outlined text-primary-container text-sm";
      execDiagHeaderIcon.textContent = "person_search";
    }

    if (execActVal) {
      execActVal.textContent = data.chosen_action || "REVISION_MANUAL";
      execActVal.className = "inline-block px-3 py-1 rounded bg-primary-container/15 border border-primary-container text-primary-container font-mono font-bold text-xs tracking-wide";
    }
    if (execActSub) execActSub.textContent = `Requires 2FA verification or preventive analyst review (Confianza ${(data.confidence * 100).toFixed(1)}%).`;
    if (execActHeaderIcon) {
      execActHeaderIcon.className = "material-symbols-outlined text-primary-container text-sm";
      execActHeaderIcon.textContent = "security";
    }
    if (execTouchMode) {
      execTouchMode.textContent = "HUMAN IN THE LOOP";
      execTouchMode.className = "text-[10px] font-mono text-primary-container font-bold";
    }
    if (execEndpoint) execEndpoint.textContent = data.action_endpoint || "POST api.gateway/v1/escalate";
    if (execImpact) {
      execImpact.textContent = "En Cola 2FA";
      execImpact.className = "text-primary-container font-bold";
    }

    if (execCondStatus) {
      execCondStatus.textContent = "BORDERLINE CASE";
      execCondStatus.className = "text-xs font-mono text-primary-container font-bold";
    }
    if (execFormalRes) execFormalRes.textContent = "Indeterminate Partial Deduction";
  } else {
    // SAFE / APPROVED
    if (cardDiag) cardDiag.className = "cyber-glass rounded-xl p-4 border-t-2 border-t-secondary border-x border-b border-outline-variant/30 flex flex-col justify-between group hover:border-secondary/50 transition-all";
    if (cardAct) cardAct.className = "cyber-glass rounded-xl p-4 border-t-2 border-t-secondary border-x border-b border-outline-variant/30 flex flex-col justify-between group hover:border-secondary/50 transition-all";
    if (cardReason) cardReason.className = "cyber-glass rounded-xl p-4 border-t-2 border-t-secondary border-x border-b border-outline-variant/30 flex flex-col justify-between group hover:border-secondary/50 transition-all";

    if (execDiagVal) {
      execDiagVal.textContent = data.friendly_label || "APROBADO";
      execDiagVal.className = "text-xl font-bold text-secondary tracking-tight";
    }
    if (execDiagSub) execDiagSub.textContent = `Safe Transaction (${((1 - prob) * 100).toFixed(1)}% Confianza)`;
    if (execDiagIcon) execDiagIcon.className = "w-2.5 h-2.5 rounded-full bg-secondary";
    if (execDiagHeaderIcon) {
      execDiagHeaderIcon.className = "material-symbols-outlined text-secondary text-sm";
      execDiagHeaderIcon.textContent = "verified";
    }

    if (execActVal) {
      execActVal.textContent = data.chosen_action || "APROBAR_TRANSACCION";
      execActVal.className = "inline-block px-3 py-1 rounded bg-secondary/15 border border-secondary text-secondary font-mono font-bold text-xs tracking-wide";
    }
    if (execActSub) execActSub.textContent = "Paso directo sin fricción. No se detectan anomalías ni patrones sospechosos.";
    if (execActHeaderIcon) {
      execActHeaderIcon.className = "material-symbols-outlined text-secondary text-sm";
      execActHeaderIcon.textContent = "check_circle";
    }
    if (execTouchMode) {
      execTouchMode.textContent = "ZERO HUMAN TOUCH (AUTONOMOUS)";
      execTouchMode.className = "text-[10px] font-mono text-secondary font-bold";
    }
    if (execEndpoint) execEndpoint.textContent = data.action_endpoint || "POST api.gateway/v1/authorize";
    if (execImpact) {
      execImpact.textContent = "Autorizada";
      execImpact.className = "text-secondary font-bold";
    }

    if (execCondStatus) {
      execCondStatus.textContent = "NORMAL PARAMETERS";
      execCondStatus.className = "text-xs font-mono text-secondary font-bold";
    }
    if (execFormalRes) execFormalRes.textContent = "Invariante Libre de Riesgo (0/0)";
  }

  if (barCerteza) {
    barCerteza.style.width = `${Math.round(prob * 100)}%`;
  }

  if (execReasonVal) {
    const activeProps = [];
    if (data.propositions_evaluated) {
      Object.entries(data.propositions_evaluated).forEach(([pName, bitVal]) => {
        if (bitVal === 1) activeProps.push(pName);
      });
    }
    let reasonText = "";
    if (activeProps.length > 0) {
      reasonText = `Se detonaron ${activeProps.length} condiciones determinantes: ${activeProps.slice(0, 3).join(", ")}${activeProps.length > 3 ? "..." : ""}. `;
    } else {
      reasonText = "No se detectaron condiciones de riesgo. ";
    }
    reasonText += `EXACTOR evaluó con resultado exacto [${data.exact_boolean_evaluation === 1 ? 'CUMPLE LA REGLA' : 'NO CUMPLE'}] con 100% de consistencia causal sin margen de duda.`;
    execReasonVal.textContent = reasonText;
  }

  // Circular Gauge & Details
  const percent = Math.round(prob * 100);
  const gaugePercent = document.getElementById("gauge-percent");
  if (gaugePercent) gaugePercent.textContent = `${percent}%`;

  const circle = document.getElementById("gauge-circle");
  if (circle) {
    const circumference = 314.15;
    const offset = circumference - (prob * circumference);
    circle.style.strokeDashoffset = offset;
    circle.style.stroke = prob >= 0.70 ? "#ff477e" : (prob <= 0.30 ? "#58df8a" : "#00f2fe");
  }

  const detailNoul = document.getElementById("detail-noul-val");
  if (detailNoul) detailNoul.textContent = `${(prob * 100).toFixed(1)}%`;

  const detailExact = document.getElementById("detail-exact-val");
  if (detailExact) detailExact.textContent = data.exact_boolean_evaluation === 1 ? "1 (CUMPLE)" : "0 (NO CUMPLE)";

  const detailMinterm = document.getElementById("detail-minterm-val");
  if (detailMinterm) detailMinterm.textContent = `0x${data.minterm_val.toString(16).toUpperCase()} (${data.minterm_val})`;

  // Choice Distribution Bars
  const choicesResult = data.jev_response ? data.jev_response.choices?.accion_recomendada?.probabilities || {} : {};
  const barsContainer = document.getElementById("choice-bars-list");
  if (barsContainer) {
    barsContainer.innerHTML = "";
    if (Object.keys(choicesResult).length > 0) {
      Object.entries(choicesResult).forEach(([opt, p]) => {
        const row = document.createElement("div");
        row.className = "choice-bar-row";
        const pPct = (p * 100).toFixed(1);
        row.innerHTML = `
          <div class="bar-meta font-mono text-xs">
            <span class="text-on-surface">${opt}</span>
            <span class="text-secondary font-bold">${pPct}%</span>
          </div>
          <div class="bar-track">
            <div class="bar-fill" style="width: ${pPct}%; ${opt === data.chosen_action ? 'background: #00f2fe;' : 'background: #33353b;'}"></div>
          </div>
        `;
        barsContainer.appendChild(row);
      });
    } else {
      barsContainer.innerHTML = `<div class="text-xs text-on-surface-variant font-mono">Action selected: ${data.chosen_action}</div>`;
    }
  }

  // 32-bit Bitmask Chips Grid
  const bitmaskGrid = document.getElementById("bitmask-chips-grid");
  if (bitmaskGrid) {
    bitmaskGrid.innerHTML = "";
    const propMap = data.propositions_evaluated || {};
    const binStr = data.minterm_binary || "";

    if (Object.keys(propMap).length > 0) {
      Object.entries(propMap).forEach(([pName, bitVal], idx) => {
        const chip = document.createElement("div");
        chip.className = `bit-chip ${bitVal === 1 ? 'bit-on' : 'bit-off'}`;
        chip.title = `${pName} = ${bitVal}`;
        chip.innerHTML = `
          <div>b${idx}: <strong>${bitVal}</strong></div>
          <div class="bit-name">${pName}</div>
        `;
        bitmaskGrid.appendChild(chip);
      });
    } else {
      for (let idx = 0; idx < Math.min(32, binStr.length || 10); idx++) {
        const bitVal = binStr[idx] ? parseInt(binStr[idx]) : 0;
        const chip = document.createElement("div");
        chip.className = `bit-chip ${bitVal === 1 ? 'bit-on' : 'bit-off'}`;
        chip.innerHTML = `<div>b${idx}: <strong>${bitVal}</strong></div>`;
        bitmaskGrid.appendChild(chip);
      }
    }
  }

  // Cache latest evaluation data for DeepSeek Explainer
  window.lastEvaluationData = data;

  // Auto-reset and prepare DeepSeek explanation box with new evaluated action
  const placeholder = document.getElementById("deepseek-placeholder");
  const textBody = document.getElementById("deepseek-text-body");
  const metaBar = document.getElementById("deepseek-meta-bar");
  
  if (textBody) {
    textBody.classList.add("hidden");
    textBody.innerHTML = "";
  }
  if (metaBar) {
    metaBar.classList.add("hidden");
  }
  if (placeholder) {
    placeholder.classList.remove("hidden");
    placeholder.innerHTML = `<span class="material-symbols-outlined text-sm text-primary-container" data-icon="lightbulb">lightbulb</span> Operación evaluada: <strong>[${data.chosen_action}]</strong> (${data.friendly_label || 'COMPLETADO'}). Haz clic en <strong>"Generar Explicación Auditoría"</strong> para consultar a DeepSeek-V3 sobre el motivo exacto de esta decisión.`;
  }
}

async function requestDeepSeekExplanation() {
  const data = window.lastEvaluationData;
  if (!data) {
    alert("Por favor ejecuta primero una evaluación en vivo antes de solicitar la explicación de auditoría.");
    return;
  }

  const btn = document.getElementById("btn-request-deepseek");
  const placeholder = document.getElementById("deepseek-placeholder");
  const textBody = document.getElementById("deepseek-text-body");
  const metaBar = document.getElementById("deepseek-meta-bar");
  const modelTag = document.getElementById("deepseek-model-tag");
  const latTag = document.getElementById("deepseek-latency-tag");

  const originalBtn = btn ? btn.innerHTML : "";
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="material-symbols-outlined text-sm animate-spin" data-icon="sync">sync</span> Consultando DeepSeek...`;
  }

  if (placeholder) {
    placeholder.classList.remove("hidden");
    placeholder.innerHTML = `<span class="material-symbols-outlined text-sm text-primary-container animate-spin" data-icon="sync">sync</span> Analizando premisas booleanas $B^{32}$ y deducción causal con DeepSeek-V3...`;
  }
  if (textBody) textBody.classList.add("hidden");

  try {
    const res = await fetch(`${API_BASE}/api/explain`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        state: data.raw_state || {},
        propositions_evaluated: data.propositions_evaluated || {},
        exact_boolean_evaluation: data.exact_boolean_evaluation || 0,
        criterio_logico_prob: data.criterio_logico_prob || 0.5,
        chosen_action: data.chosen_action || "EVALUADO",
        autonomous_action_executed: data.autonomous_action_executed || false,
      }),
    });

    if (!res.ok) {
      throw new Error(`Error ${res.status}: ${await res.text()}`);
    }

    const exp = await res.json();
    if (placeholder) placeholder.classList.add("hidden");
    if (textBody) {
      textBody.classList.remove("hidden");
      // Format markdown-style bold tags nicely
      let formatted = (exp.explanation || "")
        .replace(/\*\*(.*?)\*\*/g, '<strong class="text-primary-container font-semibold">$1</strong>')
        .replace(/\n\n/g, '<div class="h-2"></div>');
      textBody.innerHTML = formatted;
    }
    if (metaBar) {
      metaBar.classList.remove("hidden");
      if (modelTag) modelTag.textContent = `Motor LLM: ${exp.model || 'deepseek-chat'}`;
      if (latTag) latTag.textContent = `Latencia Explicabilidad: ${Math.round(exp.latency_ms || 0)} ms`;
    }
  } catch (err) {
    if (placeholder) {
      placeholder.classList.remove("hidden");
      placeholder.innerHTML = `<span class="material-symbols-outlined text-sm text-error" data-icon="error">error</span> Error al generar explicación: ${err.message}`;
    }
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = originalBtn;
    }
  }
}

// ----------------------------------------------------------------------------
// STEP 4: LIVE MEMORY & DIFFERENTIAL HOT UPDATE (WAL LEDGER)
// ----------------------------------------------------------------------------
async function refreshLedgerTable() {
  try {
    const res = await fetch(`${API_BASE}/api/ledger?limit=35`);
    if (!res.ok) return;
    const data = await res.json();

    const tbody = document.getElementById("tbody-ledger") || document.getElementById("wal-tbody");
    if (!tbody) return;
    tbody.innerHTML = "";

    (data.entries || []).forEach((row) => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-surface-container-high/30 transition-colors";
      const timeStr = row.timestamp.split("T")[1]?.slice(0, 8) || row.timestamp;
      const noulPct = (row.criterio_logico_prob * 100).toFixed(0);

      const actionBadge = row.autonomous_action_executed === 1
        ? `<span class="px-2 py-0.5 rounded bg-error/15 text-error border border-error/30 font-bold text-[10px]">⚡ AUTÓNOMA</span>`
        : `<span class="px-2 py-0.5 rounded bg-surface-container-highest text-on-surface border border-outline-variant font-bold text-[10px]">🛡️ REVISIÓN</span>`;

      tr.innerHTML = `
        <td class="py-2.5 px-3 font-mono text-primary-container font-medium">${row.query_id.slice(0, 8)}...</td>
        <td class="py-2.5 px-3 font-mono text-on-surface-variant">${timeStr}</td>
        <td class="py-2.5 px-3 font-mono text-secondary font-bold">0x${row.minterm_val.toString(16).toUpperCase()} (${row.minterm_binary})</td>
        <td class="py-2.5 px-3 font-mono text-on-surface">${noulPct}%</td>
        <td class="py-2.5 px-3 font-bold text-on-surface">${row.chosen_action}</td>
        <td class="py-2.5 px-3 font-mono text-secondary">${(row.confidence * 100).toFixed(0)}%</td>
        <td class="py-2.5 px-3">${actionBadge}</td>
        <td class="py-2.5 px-3">
          <div class="flex items-center gap-1">
            <button type="button" class="px-2 py-1 rounded bg-surface-container-high hover:bg-secondary/20 hover:text-secondary border border-outline-variant/30 text-xs transition-colors" onclick="submitFeedback('${row.query_id}', 1)" title="Confirmar Válido">👍</button>
            <button type="button" class="px-2 py-1 rounded bg-surface-container-high hover:bg-error/20 hover:text-error border border-outline-variant/30 text-xs transition-colors" onclick="submitFeedback('${row.query_id}', 0)" title="Marcar Inválido">👎</button>
            ${row.feedback_label !== null && row.feedback_label !== undefined ? `<span class="text-[10px] font-mono px-1.5 py-0.5 rounded ${row.feedback_label === 1 ? 'bg-secondary/20 text-secondary' : 'bg-error/20 text-error'}">fb:${row.feedback_label}</span>` : ''}
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error refreshing ledger:", err);
  }
}

async function submitFeedback(queryId, label) {
  try {
    const res = await fetch(`${API_BASE}/api/ledger/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query_id: queryId, label: label }),
    });
    if (res.ok) {
      refreshLedgerTable();
    }
  } catch (e) {
    console.error("Feedback error:", e);
  }
}

async function triggerDifferentialUpdate() {
  const windowSize = parseInt(document.getElementById("range-window-size").value, 10);
  const btn = document.getElementById("btn-trigger-differential");

  const originalText = btn ? btn.innerHTML : "";
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="material-symbols-outlined text-base animate-spin" data-icon="sync">sync</span> Minimizando N=${windowSize} en Rust HPC...`;
  }

  try {
    const res = await fetch(`${API_BASE}/api/differential/update`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ window_size: windowSize }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Error in differential update.");
    }

    const data = await res.json();

    if (data.status === "UPDATED") {
      const diffBox = document.getElementById("diff-comparison-box");
      if (diffBox) diffBox.style.display = "block";

      const oldVerEl = document.getElementById("diff-old-ver");
      if (oldVerEl) oldVerEl.textContent = data.rule_version - 1;

      const oldFormulaEl = document.getElementById("diff-old-formula");
      if (oldFormulaEl) oldFormulaEl.textContent = data.old_formula;

      const newVerEl = document.getElementById("diff-new-ver");
      if (newVerEl) newVerEl.textContent = data.rule_version;

      const newFormulaEl = document.getElementById("diff-new-formula");
      if (newFormulaEl) newFormulaEl.textContent = data.new_formula;

      await loadExactorRules();
      await loadJevSchema();
      await loadSystemStatus();

      alert(`¡Logical rules updated dynamically to version v${data.rule_version} with zero downtime!`);
    } else {
      alert(`Information: ${data.message || 'No changes in rule'}`);
    }
  } catch (err) {
    alert(`Error: ${err.message}`);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = originalText;
    }
  }
}

// ----------------------------------------------------------------------------
// COLLAPSIBLE CONTROLS
// ----------------------------------------------------------------------------
function toggleExpand(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const isCollapsed = container.classList.contains("collapsed");
  if (isCollapsed) {
    container.classList.remove("collapsed");
    container.classList.add("expanded");
  } else {
    container.classList.remove("expanded");
    container.classList.add("collapsed");
  }
}

function toggleExpandFromContent(containerElement) {
  if (!containerElement || !containerElement.classList.contains("collapsed")) return;
  toggleExpand(containerElement.id);
}

function toggleTextareaExpand(textareaId) {
  const textarea = document.getElementById(textareaId);
  if (!textarea) return;

  if (textarea.rows === 6) {
    textarea.rows = 18;
  } else {
    textarea.rows = 6;
  }
}

// ----------------------------------------------------------------------------
// TOKENS & CREDENTIALS MODAL MANAGEMENT
// ----------------------------------------------------------------------------
async function openTokenConfigModal() {
  const modal = document.getElementById("modal-tokens-config");
  if (modal) {
    modal.classList.remove("hidden");
  }
  await loadTokenConfig();
}

function closeTokenConfigModal() {
  const modal = document.getElementById("modal-tokens-config");
  if (modal) {
    modal.classList.add("hidden");
  }
}

function togglePasswordVisibility(inputId) {
  const input = document.getElementById(inputId);
  if (!input) return;
  input.type = input.type === "password" ? "text" : "password";
}

async function loadTokenConfig() {
  try {
    const res = await fetch(`${API_BASE}/api/config/tokens`);
    if (!res.ok) return;
    const data = await res.json();

    const exactorStatus = document.getElementById("token-status-exactor");
    if (exactorStatus) {
      if (data.exactor.is_configured) {
        exactorStatus.textContent = `Activo (${data.exactor.masked_token})`;
        exactorStatus.className = "text-[10px] px-2 py-0.5 rounded bg-secondary/20 font-mono text-secondary";
      } else {
        exactorStatus.textContent = data.exactor.use_cloud_api ? "Auto-Token Cloud" : "Local Rust HPC";
        exactorStatus.className = "text-[10px] px-2 py-0.5 rounded bg-surface-container font-mono text-on-surface-variant";
      }
    }

    const chkCloud = document.getElementById("chk-use-cloud-exactor");
    if (chkCloud) {
      chkCloud.checked = !!data.exactor.use_cloud_api;
    }

    const jevStatus = document.getElementById("token-status-jev");
    if (jevStatus) {
      if (data.jev.is_configured) {
        jevStatus.textContent = `Activo (${data.jev.masked_token})`;
        jevStatus.className = "text-[10px] px-2 py-0.5 rounded bg-primary-container/20 font-mono text-primary-container";
      } else {
        jevStatus.textContent = "Simulador RLCD";
        jevStatus.className = "text-[10px] px-2 py-0.5 rounded bg-surface-container font-mono text-on-surface-variant";
      }
    }

    const deepseekStatus = document.getElementById("token-status-deepseek");
    if (deepseekStatus) {
      if (data.deepseek.is_configured) {
        deepseekStatus.textContent = `Activo (${data.deepseek.masked_token})`;
        deepseekStatus.className = "text-[10px] px-2 py-0.5 rounded bg-tertiary-container/20 font-mono text-tertiary-container";
      } else {
        deepseekStatus.textContent = "Sin clave";
        deepseekStatus.className = "text-[10px] px-2 py-0.5 rounded bg-surface-container font-mono text-on-surface-variant";
      }
    }
  } catch (e) {
    console.error("Error loading token config:", e);
  }
}

async function saveTokensConfiguration() {
  const exactorToken = document.getElementById("input-token-exactor")?.value.trim();
  const jevToken = document.getElementById("input-token-jev")?.value.trim();
  const deepseekKey = document.getElementById("input-token-deepseek")?.value.trim();
  const useCloudExactor = document.getElementById("chk-use-cloud-exactor")?.checked;
  const msgEl = document.getElementById("tokens-save-msg");

  const payload = {};
  if (exactorToken) payload.exactor_token = exactorToken;
  if (jevToken) payload.jev_token = jevToken;
  if (deepseekKey) payload.deepseek_api_key = deepseekKey;
  if (useCloudExactor !== undefined) payload.use_cloud_exactor = useCloudExactor;

  try {
    if (msgEl) msgEl.textContent = "Guardando credenciales...";
    const res = await fetch(`${API_BASE}/api/config/tokens`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      if (msgEl) {
        msgEl.textContent = "✓ Credenciales guardadas y activas.";
        msgEl.className = "text-[11px] text-secondary font-sans font-bold";
      }
      await loadTokenConfig();
      await loadSystemStatus();
      setTimeout(() => {
        closeTokenConfigModal();
        if (msgEl) msgEl.textContent = "";
      }, 1200);
    } else {
      if (msgEl) {
        msgEl.textContent = "Error al guardar.";
        msgEl.className = "text-[11px] text-error font-sans";
      }
    }
  } catch (err) {
    if (msgEl) msgEl.textContent = `Error: ${err.message}`;
  }
}
