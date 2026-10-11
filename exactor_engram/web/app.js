// Exactor Engram Associative Memory - Frontend Controller

let currentFile = null;
let currentMode = "image"; // "image" | "text"

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initDropzone();
  initActions();
  loadStats();
  loadSamples();
  loadMemories();
});

// -----------------------------------------------------------------------------
// Tabs
// -----------------------------------------------------------------------------

function initTabs() {
  const tabImage = document.getElementById("tab-image");
  const tabText = document.getElementById("tab-text");
  const boxImage = document.getElementById("input-container-image");
  const boxText = document.getElementById("input-container-text");

  tabImage.addEventListener("click", () => {
    tabImage.classList.add("active");
    tabText.classList.remove("active");
    boxImage.style.display = "block";
    boxText.style.display = "none";
    currentMode = "image";
  });

  tabText.addEventListener("click", () => {
    tabText.classList.add("active");
    tabImage.classList.remove("active");
    boxText.style.display = "block";
    boxImage.style.display = "none";
    currentMode = "text";
  });
}

// -----------------------------------------------------------------------------
// Drag & Drop
// -----------------------------------------------------------------------------

function initDropzone() {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const preview = document.getElementById("dropzone-preview");
  const prompt = document.getElementById("dropzone-prompt");

  dropzone.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  });

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  });

  function handleFile(file) {
    currentFile = file;
    const reader = new FileReader();
    reader.onload = (ev) => {
      preview.src = ev.target.result;
      preview.style.display = "block";
      prompt.style.display = "none";
    };
    reader.readAsDataURL(file);
  }
}

// -----------------------------------------------------------------------------
// Samples
// -----------------------------------------------------------------------------

async function loadSamples() {
  const container = document.getElementById("sample-chips-container");
  try {
    const res = await fetch("/api/demo/samples");
    const samples = await res.json();
    container.innerHTML = "";
    samples.forEach((s) => {
      const chip = document.createElement("div");
      chip.className = "sample-chip";
      chip.innerHTML = `<span>${s.type === "image" ? "🖼️" : "📄"}</span> <span>${s.name}</span>`;
      chip.addEventListener("click", () => selectSample(s));
      container.appendChild(chip);
    });
  } catch (err) {
    container.innerHTML = `<span style="font-size:0.75rem; color: var(--text-faint);">No se pudieron cargar muestras</span>`;
  }
}

function selectSample(sample) {
  if (sample.type === "image") {
    document.getElementById("tab-image").click();
    fetch(sample.data_url)
      .then((res) => res.blob())
      .then((blob) => {
        currentFile = new File([blob], `${sample.name}.png`, { type: sample.mime });
        const preview = document.getElementById("dropzone-preview");
        preview.src = sample.data_url;
        preview.style.display = "block";
        document.getElementById("dropzone-prompt").style.display = "none";
      });
  } else {
    document.getElementById("tab-text").click();
    document.getElementById("text-input").value = sample.text;
  }
}

// -----------------------------------------------------------------------------
// Actions
// -----------------------------------------------------------------------------

function initActions() {
  document.getElementById("btn-recall").addEventListener("click", () => executeRecall(true));
  document.getElementById("btn-perceive-only").addEventListener("click", () => executePerceive());
  document.getElementById("btn-seed-demo").addEventListener("click", handleSeedDemo);
  document.getElementById("btn-run-benchmark").addEventListener("click", handleRunBenchmark);
  document.getElementById("btn-refresh-memories").addEventListener("click", loadMemories);
}

async function executeRecall(allowOracle = true) {
  const labelHint = document.getElementById("label-hint").value.trim() || null;
  const btn = document.getElementById("btn-recall");
  btn.disabled = true;
  btn.innerHTML = `<span>⏳</span> Resolviendo...`;

  try {
    let result;
    if (currentMode === "image") {
      if (!currentFile) {
        alert("Por favor selecciona o sube una imagen primero.");
        btn.disabled = false;
        btn.innerHTML = `<span>⚡</span> Recuperar Recuerdo (Fast-Path)`;
        return;
      }
      const formData = new FormData();
      formData.append("file", currentFile);
      formData.append("allow_oracle", allowOracle ? "true" : "false");
      if (labelHint) formData.append("label_hint", labelHint);

      const res = await fetch("/api/recall/file", { method: "POST", body: formData });
      result = await res.json();
    } else {
      const text = document.getElementById("text-input").value.trim();
      if (!text) {
        alert("Por favor ingresa texto para consultar.");
        btn.disabled = false;
        btn.innerHTML = `<span>⚡</span> Recuperar Recuerdo (Fast-Path)`;
        return;
      }
      const res = await fetch("/api/recall/text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, allow_oracle: allowOracle, label_hint: labelHint }),
      });
      result = await res.json();
    }

    renderRecallResult(result);
    loadStats();
    loadMemories();
  } catch (err) {
    alert("Error al ejecutar recall: " + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>⚡</span> Recuperar Recuerdo (Fast-Path)`;
  }
}

async function executePerceive() {
  try {
    let result;
    if (currentMode === "image") {
      if (!currentFile) return alert("Selecciona una imagen primero.");
      const formData = new FormData();
      formData.append("file", currentFile);
      const res = await fetch("/api/perceive/file", { method: "POST", body: formData });
      result = await res.json();
    } else {
      const text = document.getElementById("text-input").value.trim();
      if (!text) return alert("Ingresa texto primero.");
      const res = await fetch("/api/perceive/text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      result = await res.json();
    }

    // Render hypercube only
    document.getElementById("result-empty").style.display = "none";
    document.getElementById("result-content").style.display = "flex";
    document.getElementById("result-path-hero").className = "path-hero path-identity";
    document.getElementById("result-path-label").innerText = "MODO PERCEPCIÓN";
    document.getElementById("result-path-tag").innerText = "PROYECCIÓN B⁶⁴";
    document.getElementById("result-latency-clock").innerText = "0.01 ms";
    document.getElementById("result-system-badge").style.display = "inline-flex";
    document.getElementById("result-system-badge").className = "badge badge-cyan";
    document.getElementById("result-system-badge").innerText = "PILAR 1";

    document.getElementById("result-memory-display").style.display = "none";
    renderHypercube(result.code);
    document.getElementById("result-formula-card").innerHTML = `<code>${result.sha256} (hash SHA-256)</code>`;
  } catch (err) {
    alert("Error al binarizar: " + err.message);
  }
}

function renderRecallResult(data) {
  document.getElementById("result-empty").style.display = "none";
  document.getElementById("result-content").style.display = "flex";

  const hero = document.getElementById("result-path-hero");
  const pathTag = document.getElementById("result-path-tag");
  const pathLabel = document.getElementById("result-path-label");
  const clock = document.getElementById("result-latency-clock");
  const badge = document.getElementById("result-system-badge");

  badge.style.display = "inline-flex";

  if (data.path === "FAST_PATH" || data.path === "IDENTICO") {
    hero.className = "path-hero path-fast";
    pathLabel.innerText = "RECUPERACIÓN INSTANTÁNEA (SISTEMA 1)";
    pathTag.innerText = data.path === "IDENTICO" ? "OBJETO IDÉNTICO" : "FAST-PATH DETERMINISTA";
    badge.className = "badge badge-emerald";
    badge.innerText = "COSTO CERO (0.05 ms)";
    clock.style.color = "var(--accent-emerald)";
    clock.innerText = `${(data.timing.fastpath_us / 1000).toFixed(3)} ms`;
  } else if (data.path === "COLD_START" || data.path === "AMBIGUO" || data.path === "ENSENANZA") {
    hero.className = "path-hero path-cold";
    pathLabel.innerText = "FRICCIÓN COGNITIVA (SISTEMA 2)";
    pathTag.innerText = `CONSOLIDACIÓN ORÁCULO (${data.oracle ? data.oracle.provider : "Oráculo"})`;
    badge.className = "badge badge-amber";
    badge.innerText = `SISTEMA 2 (${data.timing.oracle_ms.toFixed(0)} ms)`;
    clock.style.color = "var(--accent-amber)";
    clock.innerText = `${data.timing.total_ms.toFixed(1)} ms`;
  } else {
    hero.className = "path-hero";
    pathLabel.innerText = "PATRÓN DESCONOCIDO";
    pathTag.innerText = "NOVEDAD NO CONSOLIDADA";
    badge.className = "badge badge-violet";
    badge.innerText = "SISTEMA 1 (Rechazado)";
    clock.innerText = `${data.timing.total_ms.toFixed(2)} ms`;
  }

  // Memory card
  const memDisplay = document.getElementById("result-memory-display");
  if (data.memory) {
    memDisplay.style.display = "grid";
    document.getElementById("result-memory-label").innerText = (data.memory.label || data.label || "").toUpperCase();
    document.getElementById("result-memory-desc").innerText = data.memory.description || "Recuerdo consolidado en la memoria viva.";
    document.getElementById("result-memory-id").innerText = `ID: ${data.memory.id} • Modos: ${data.memory.modality} • Usos: ${data.memory.recall_count}`;

    const thumbWrap = document.getElementById("result-thumb-wrap");
    if (data.memory.thumbnail_url) {
      thumbWrap.innerHTML = `<img src="${data.memory.thumbnail_url}" alt="Thumbnail">`;
    } else if (data.memory.text_preview) {
      thumbWrap.innerHTML = `<div style="padding:0.5rem; font-size:0.7rem; color:var(--text-muted); overflow:hidden;">${data.memory.text_preview.slice(0, 80)}...</div>`;
    } else {
      thumbWrap.innerHTML = `<span style="font-size:0.75rem; color:var(--text-faint);">Sin vista previa</span>`;
    }

    const tagsDiv = document.getElementById("result-memory-tags");
    tagsDiv.innerHTML = "";
    (data.memory.tags || []).forEach((t) => {
      const sp = document.createElement("span");
      sp.className = "badge";
      sp.style.fontSize = "0.7rem";
      sp.innerText = t;
      tagsDiv.appendChild(sp);
    });
  } else {
    memDisplay.style.display = "none";
  }

  // Hypercube
  if (data.query && data.query.code) {
    renderHypercube(data.query.code);
  }

  // Formula & proof
  const formulaCard = document.getElementById("result-formula-card");
  if (data.proof && data.proof.length > 0) {
    let html = "";
    data.proof.forEach((p) => {
      const g = p.guard || {};
      const d = p.discriminant || {};
      html += `<div><strong>Concepto Asociado:</strong> <code>${p.label}</code></div>`;
      html += `<div><strong>Guarda Invariante (Pilar 4):</strong> ${g.matched || 0} / ${g.literals || 0} literales conformes (${g.violated ? g.violated.length : 0} violaciones &le; tolerancia ${g.tolerance || 0})</div>`;
      if (d.formula) {
        html += `<div style="margin-top:0.3rem;"><strong>Fórmula Discriminante Exactor:</strong> <code>${d.formula}</code></div>`;
      }
    });
    formulaCard.innerHTML = html;
  } else if (data.consolidation && data.consolidation.engram) {
    let html = `<div><strong>Nuevo Engrama Consolidado (v${data.consolidation.version}):</strong></div>`;
    data.consolidation.engram.forEach((e) => {
      html += `<div><code>${e.label}</code> &rarr; ${e.guard_formula}</div>`;
      html += `<div>Discriminante: <code>${e.discriminant_formula}</code></div>`;
    });
    formulaCard.innerHTML = html;
  } else {
    formulaCard.innerHTML = `<code>No se encontró coincidencia de engramas activos para este patrón.</code>`;
  }
}

function renderHypercube(code) {
  const matrix = document.getElementById("result-hypercube-matrix");
  const stableSpan = document.getElementById("result-stable-bits");
  matrix.innerHTML = "";

  stableSpan.innerText = `${code.stable_bits || 64} / 64 bits estables`;

  (code.bits || []).forEach((b) => {
    const chip = document.createElement("div");
    chip.className = "bit-chip";
    if (b.state === 1) chip.classList.add("bit-1");
    else if (b.state === 0) chip.classList.add("bit-0");
    else chip.classList.add("bit-dc");

    chip.innerText = b.state === null ? "-" : b.state;
    chip.title = `b${b.i}: ${b.name} (${b.state === null ? "don't-care" : b.state})`;
    matrix.appendChild(chip);
  });
}

// -----------------------------------------------------------------------------
// Telemetry & Benchmark
// -----------------------------------------------------------------------------

async function loadStats() {
  try {
    const res = await fetch("/api/system/status");
    const st = await res.json();

    document.getElementById("stat-memories").innerText = st.memories || 0;
    document.getElementById("stat-concepts").innerText = `${st.concepts || 0} conceptos únicos`;
    document.getElementById("stat-hitrate").innerText = `${((st.hit_rate || 0) * 100).toFixed(1)}%`;
    document.getElementById("stat-hits").innerText = `${st.fast_hits || 0} consultas resueltas localmente`;
    document.getElementById("stat-tokens").innerText = (st.tokens_saved || 0).toLocaleString();
    document.getElementById("stat-cost").innerText = `$${(st.cost_saved_usd || 0).toFixed(4)}`;

    if (st.fastpath_avg_us) {
      document.getElementById("stat-latency").innerText = `${st.fastpath_avg_us.toFixed(2)} μs`;
    }

    if (st.plan) {
      document.getElementById("badge-plan").innerText = `PLAN ${st.plan.name} (k=${st.hypercube_k})`;
    }
  } catch (err) {
    console.error("Error al cargar stats:", err);
  }
}

async function handleRunBenchmark() {
  const btn = document.getElementById("btn-run-benchmark");
  btn.disabled = true;
  btn.innerText = "⏳ Ejecutando 1,000 iteraciones...";

  try {
    const res = await fetch("/api/benchmark?iterations=1000");
    const data = await res.json();

    if (data.error) {
      alert(data.error);
      return;
    }

    document.getElementById("bench-engram-latency").innerText = `${(data.engram_fastpath_us / 1000).toFixed(3)} ms (${data.engram_fastpath_us.toFixed(1)} μs)`;
    document.getElementById("bench-knn-latency").innerText = `${(data.vector_knn_us / 1000).toFixed(3)} ms (${data.vector_knn_us.toFixed(1)} μs)`;

    document.getElementById("bench-summary-note").innerHTML = `
      <strong style="color: var(--accent-emerald);">Aceleración de Hardware:</strong> Exactor Engram fue 
      <strong style="color: var(--accent-cyan);">${data.speedup}x más rápido</strong> que la búsqueda vectorial de similitud coseno 
      con <strong>${(data.engram_self_recall_accuracy * 100).toFixed(1)}% de precisión causal exacta</strong>.
    `;
  } catch (err) {
    alert("Error en benchmark: " + err.message);
  } finally {
    btn.disabled = false;
    btn.innerText = "▶ Ejecutar Benchmark en Vivo";
  }
}

async function handleSeedDemo() {
  const btn = document.getElementById("btn-seed-demo");
  btn.disabled = true;
  btn.innerText = "⚡ Sembrando...";

  try {
    const res = await fetch("/api/demo/seed?concepts=6&exemplars_per_concept=2", { method: "POST" });
    const data = await res.json();
    alert(`¡Demo sembrada con éxito! Se consolidaron ${data.total_created} recuerdos a través del Oráculo.`);
    loadStats();
    loadMemories();
    loadSamples();
  } catch (err) {
    alert("Error al sembrar demo: " + err.message);
  } finally {
    btn.disabled = false;
    btn.innerText = "⚡ Sembrar Demo";
  }
}

async function loadMemories() {
  const gallery = document.getElementById("memories-gallery");
  try {
    const res = await fetch("/api/memories?limit=30");
    const memories = await res.json();
    gallery.innerHTML = "";

    if (!memories || memories.length === 0) {
      gallery.innerHTML = `<span style="font-size: 0.8rem; color: var(--text-faint);">No hay recuerdos en el libro mayor WAL todavía. Haz clic en "⚡ Sembrar Demo" o consulta un objeto.</span>`;
      return;
    }

    memories.forEach((m) => {
      const card = document.createElement("div");
      card.className = "glass gallery-card";

      let visualHtml = "";
      if (m.modality === "image") {
        visualHtml = `<img class="gallery-thumb" src="/api/memories/${m.id}/thumbnail" alt="${m.label}">`;
      } else {
        visualHtml = `<div class="gallery-text-box">${(m.text_preview || "").slice(0, 140)}...</div>`;
      }

      card.innerHTML = `
        ${visualHtml}
        <div>
          <div style="font-size: 0.85rem; font-weight: 700; color: #fff;">${(m.label || "").toUpperCase()}</div>
          <div style="font-size: 0.72rem; color: var(--text-muted);">${m.description || m.modality}</div>
          <div style="font-size: 0.68rem; color: var(--text-faint); margin-top: 0.3rem;">Usos: ${m.recall_count} • ${m.size_bytes} bytes</div>
        </div>
      `;

      card.addEventListener("click", () => inspectMemory(m.id));
      gallery.appendChild(card);
    });
  } catch (err) {
    gallery.innerHTML = `<span style="font-size: 0.8rem; color: var(--text-faint);">Error al cargar recuerdos.</span>`;
  }
}

async function inspectMemory(memId) {
  try {
    const res = await fetch(`/api/memories/${memId}`);
    const m = await res.json();
    alert(`Recuerdo [${m.id}]\nEtiqueta: ${m.label}\nModalidad: ${m.modality}\nTamaño: ${m.size_bytes} bytes\nAlmacenamiento: ${m.storage}\nRecuperado: ${m.recall_count} veces`);
  } catch (err) {
    console.error(err);
  }
}
