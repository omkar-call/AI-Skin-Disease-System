// =====================================
// Dermascope AI — Frontend Logic
// =====================================
const API_URL = "https://ai-skin-disease-system.onrender.com/predict";
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

// ---------- Elements ----------

const themeToggle = document.getElementById("themeToggle");
const iconMoon = document.getElementById("iconMoon");
const iconSun = document.getElementById("iconSun");

const uploadBox = document.getElementById("uploadBox");
const imageInput = document.getElementById("imageInput");
const uploadContent = document.getElementById("uploadContent");
const previewWrap = document.getElementById("previewWrap");
const preview = document.getElementById("preview");
const removePreviewBtn = document.getElementById("removePreviewBtn");
const scanSweep = document.getElementById("scanSweep");

const predictBtn = document.getElementById("predictBtn");
const loading = document.getElementById("loading");
const loadingText = document.getElementById("loadingText");

const patientName = document.getElementById("patientName");
const gender = document.getElementById("gender");

const resultCard = document.getElementById("resultCard");
const disease = document.getElementById("disease");
const description = document.getElementById("description");
const recommendation = document.getElementById("recommendation");
const riskBadge = document.getElementById("riskBadge");

const gaugeFill = document.getElementById("gaugeFill");
const gaugeStopA = document.getElementById("gaugeStopA");
const gaugeStopB = document.getElementById("gaugeStopB");
const confidenceValue = document.getElementById("confidenceValue");

const displayName = document.getElementById("displayName");
const displayGender = document.getElementById("displayGender");
const predictionTime = document.getElementById("predictionTime");
const predictionDate = document.getElementById("predictionDate");

const downloadBtn = document.getElementById("downloadBtn");
const newPredictionBtn = document.getElementById("newPredictionBtn");

const toastEl = document.getElementById("toast");

let hasImage = false;
let toastTimer = null;

const GAUGE_RADIUS = 68;
const GAUGE_CIRCUMFERENCE = 2 * Math.PI * GAUGE_RADIUS;

const RISK_COLORS = {
  low:    { a: "#0d9488", b: "#2dd4bf" },
  medium: { a: "#d97706", b: "#fbbf24" },
  high:   { a: "#e11d48", b: "#fb7185" },
  unknown:{ a: "#7c3aed", b: "#ec4899" }
};

if (gaugeFill) {
  gaugeFill.style.strokeDasharray = GAUGE_CIRCUMFERENCE;
  gaugeFill.style.strokeDashoffset = GAUGE_CIRCUMFERENCE;
}

// =====================================
// Theme toggle (persisted)
// =====================================

function applyTheme(theme){
  document.body.classList.toggle("dark", theme === "dark");
  if (iconMoon && iconSun){
    iconMoon.hidden = theme === "dark";
    iconSun.hidden = theme !== "dark";
  }
}

try {
  const savedTheme = localStorage.getItem("dermascopeTheme");
  if (savedTheme) {
    applyTheme(savedTheme);
  } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    applyTheme("dark");
  }
} catch (e) { /* localStorage unavailable — default light theme */ }

themeToggle.addEventListener("click", () => {
  const next = document.body.classList.contains("dark") ? "light" : "dark";
  applyTheme(next);
  try { localStorage.setItem("dermascopeTheme", next); } catch (e) {}
});

// =====================================
// Toast notifications
// =====================================

function showToast(message, type){
  if (!toastEl) { alert(message); return; }
  toastEl.textContent = message;
  toastEl.className = "show" + (type ? " " + type : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove("show"), 3200);
}

function flagInvalid(el){
  if (!el) return;
  el.classList.remove("input-error");
  void el.offsetWidth; // restart animation if already shaking
  el.classList.add("input-error");
  el.addEventListener("animationend", function handler(){
    el.classList.remove("input-error");
    el.removeEventListener("animationend", handler);
  });
}

// =====================================
// Upload / drag & drop
// =====================================

uploadBox.addEventListener("click", (e) => {
  if (e.target.closest("#removePreviewBtn")) return;
  if (!hasImage) imageInput.click();
});

uploadBox.addEventListener("keydown", (e) => {
  if ((e.key === "Enter" || e.key === " ") && !hasImage){
    e.preventDefault();
    imageInput.click();
  }
});

["dragenter", "dragover"].forEach((evt) => {
  uploadBox.addEventListener(evt, (e) => {
    e.preventDefault(); e.stopPropagation();
    if (!hasImage) uploadBox.classList.add("dragging");
  });
});
["dragleave", "drop"].forEach((evt) => {
  uploadBox.addEventListener(evt, (e) => {
    e.preventDefault(); e.stopPropagation();
    uploadBox.classList.remove("dragging");
  });
});
uploadBox.addEventListener("drop", (e) => {
  const file = e.dataTransfer.files[0];
  if (file) {
    const dt = new DataTransfer();
    dt.items.add(file);
    imageInput.files = dt.files;
    handleFile(file);
  }
});
imageInput.addEventListener("change", () => {
  if (imageInput.files.length > 0) handleFile(imageInput.files[0]);
});

function handleFile(file){
  if (!file.type || !file.type.startsWith("image/")){
    showToast("Please upload a valid image file (JPG or PNG).", "error");
    return;
  }
  if (file.size > MAX_FILE_SIZE){
    showToast("That image is too large — please keep it under 10MB.", "error");
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    preview.src = e.target.result;
    uploadContent.style.display = "none";
    previewWrap.hidden = false;
    uploadBox.classList.add("has-image");
    predictBtn.disabled = false;
    hasImage = true;
    resultCard.hidden = true;
  };
  reader.readAsDataURL(file);
}

if (removePreviewBtn){
  removePreviewBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    resetUpload();
  });
}

function resetUpload(){
  preview.src = "";
  imageInput.value = "";
  uploadContent.style.display = "block";
  previewWrap.hidden = true;
  uploadBox.classList.remove("has-image");
  predictBtn.disabled = true;
  hasImage = false;
  scanSweep.classList.remove("active");
}

// =====================================
// Predict
// =====================================

predictBtn.addEventListener("click", async () => {

  if (patientName.value.trim() === ""){
    showToast("Please enter the patient name.", "error");
    flagInvalid(patientName);
    patientName.focus();
    return;
  }

  if (gender.value === ""){
    showToast("Please select a gender.", "error");
    flagInvalid(gender);
    gender.focus();
    return;
  }

  if (!hasImage || imageInput.files.length === 0){
    showToast("Please upload a skin image.", "error");
    return;
  }

  predictBtn.disabled = true;
  loading.hidden = false;
  scanSweep.classList.add("active");
  resultCard.hidden = true;

  const formData = new FormData();
  formData.append("image", imageInput.files[0]);
  formData.append("patientName", patientName.value.trim());
  formData.append("gender", gender.value);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000);

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      body: formData,
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok){
      throw new Error("Server error: " + response.status);
    }

    const data = await response.json();

    if (data.error){
      throw new Error(data.error);
    }

    renderResult(data);

  } catch (error) {
    clearTimeout(timeoutId);
    console.error("Prediction failed:", error);

    if (error.name === "AbortError"){
      showToast("The server took too long to respond. Please try again.", "error");
    } else {
      showToast("Prediction failed: " + error.message, "error");
    }

  } finally {
    loading.hidden = true;
    scanSweep.classList.remove("active");
    predictBtn.disabled = false;
  }
});

function renderResult(data){

  resultCard.hidden = false;

  disease.textContent = data.disease || "Unknown";
  description.textContent = data.description || "No description available.";
  recommendation.textContent = data.recommendation || "Consult a dermatologist.";

  let confNumber = Number(data.confidence);
  if (!Number.isFinite(confNumber)) confNumber = 0;
  confNumber = Math.max(0, Math.min(100, confNumber));

  const riskRaw = (data.risk || "unknown").toLowerCase();
  const riskKey = ["low", "medium", "high"].includes(riskRaw) ? riskRaw : "unknown";
  const riskLabel = riskRaw.toUpperCase();

  riskBadge.textContent = riskLabel;
  riskBadge.className = "badge risk-" + riskKey;

  // Gauge color follows risk level
  const colors = RISK_COLORS[riskKey];
  gaugeStopA.setAttribute("stop-color", colors.a);
  gaugeStopB.setAttribute("stop-color", colors.b);

  // Animate the ring fill + the number counting up together
  const offset = GAUGE_CIRCUMFERENCE - (confNumber / 100) * GAUGE_CIRCUMFERENCE;
  requestAnimationFrame(() => {
    gaugeFill.style.strokeDashoffset = offset;
  });
  animateCount(confidenceValue, Math.round(confNumber));

  displayName.textContent = patientName.value.trim() || "Not specified";
  displayGender.textContent = gender.value || "Not specified";

  const now = new Date();
  predictionTime.textContent = data.prediction_time || now.toLocaleTimeString();
  predictionDate.textContent = data.date || now.toLocaleDateString();

  resultCard.scrollIntoView({ behavior: "smooth", block: "start" });
}

function animateCount(el, target){
  let current = 0;
  const step = Math.max(1, Math.round(target / 30));
  const timer = setInterval(() => {
    current += step;
    if (current >= target){ current = target; clearInterval(timer); }
    el.textContent = current + "%";
  }, 20);
}

// =====================================
// New Analysis
// =====================================

if (newPredictionBtn){
  newPredictionBtn.addEventListener("click", () => {
    resetUpload();
    resultCard.hidden = true;

    patientName.value = "";
    gender.value = "";

    disease.textContent = "—";
    description.textContent = "Waiting for analysis…";
    recommendation.textContent = "Recommendation will appear here.";
    riskBadge.textContent = "—";
    riskBadge.className = "badge";

    confidenceValue.textContent = "0%";
    gaugeFill.style.strokeDashoffset = GAUGE_CIRCUMFERENCE;

    displayName.textContent = "-";
    displayGender.textContent = "-";
    predictionTime.textContent = "--:--";
    predictionDate.textContent = "--";

    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}

// =====================================
// Download PDF report
// (uses html2canvas + jsPDF if they loaded; falls back to the
// browser print dialog — which can also "Save as PDF" — if not)
// =====================================

if (downloadBtn){
  downloadBtn.addEventListener("click", async () => {

    if (resultCard.hidden){
      showToast("Run an analysis first, then download the report.", "error");
      return;
    }

    const hasPdfLibs = window.html2canvas && window.jspdf && window.jspdf.jsPDF;

    if (!hasPdfLibs){
      window.print();
      return;
    }

    const originalText = downloadBtn.innerHTML;
    downloadBtn.innerHTML = "Generating PDF…";
    downloadBtn.disabled = true;

    try {
      const canvas = await window.html2canvas(resultCard, {
        scale: 2,
        backgroundColor: document.body.classList.contains("dark") ? "#1a1024" : "#ffffff",
        useCORS: true
      });

      const imgData = canvas.toDataURL("image/png");
      const { jsPDF } = window.jspdf;

      const pdf = new jsPDF({
        orientation: "portrait",
        unit: "px",
        format: [canvas.width, canvas.height]
      });

      pdf.addImage(imgData, "PNG", 0, 0, canvas.width, canvas.height);

      const safeName = (patientName.value.trim() || "patient").replace(/[^a-z0-9]+/gi, "_");
      pdf.save(`skin-report-${safeName}.pdf`);

      showToast("Report downloaded.", "success");

    } catch (error) {
      console.error("PDF generation failed:", error);
      showToast("Couldn't generate the PDF — opening print dialog instead.", "error");
      window.print();

    } finally {
      downloadBtn.innerHTML = originalText;
      downloadBtn.disabled = false;
    }
  });
}

console.log("Dermascope AI — frontend loaded.");
