import { useState, useEffect } from "react";

// ─────────────────────────────────────────────
// Styles — inline so there's zero config needed
// ─────────────────────────────────────────────
const S = {
  app: {
    fontFamily: "'Segoe UI', system-ui, sans-serif",
    background: "#f0f4f8",
    minHeight: "100vh",
    padding: "0 0 60px 0",
  },
  header: {
    background: "#cc0000",
    color: "white",
    padding: "18px 32px",
    display: "flex",
    alignItems: "center",
    gap: 16,
    boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
  },
  headerTitle: { margin: 0, fontSize: 22, fontWeight: 700, letterSpacing: 0.5 },
  headerSub: { margin: 0, fontSize: 13, opacity: 0.85 },
  layout: {
    maxWidth: 1100,
    margin: "32px auto",
    padding: "0 24px",
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 28,
  },
  card: {
    background: "white",
    borderRadius: 10,
    padding: 28,
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
  },
  cardTitle: {
    margin: "0 0 20px 0",
    fontSize: 17,
    fontWeight: 700,
    color: "#1a1a1a",
    borderBottom: "2px solid #cc0000",
    paddingBottom: 10,
  },
  section: { marginBottom: 20 },
  sectionLabel: {
    fontSize: 12,
    fontWeight: 700,
    color: "#666",
    textTransform: "uppercase",
    letterSpacing: 0.8,
    marginBottom: 8,
    display: "block",
  },
  row: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 },
  input: {
    width: "100%",
    padding: "9px 12px",
    border: "1px solid #d1d5db",
    borderRadius: 6,
    fontSize: 14,
    boxSizing: "border-box",
    outline: "none",
    transition: "border-color 0.15s",
  },
  textarea: {
    width: "100%",
    padding: "9px 12px",
    border: "1px solid #d1d5db",
    borderRadius: 6,
    fontSize: 13,
    boxSizing: "border-box",
    resize: "vertical",
    fontFamily: "inherit",
    outline: "none",
  },
  tagInput: {
    display: "flex",
    gap: 8,
    marginBottom: 8,
  },
  tagList: { display: "flex", flexWrap: "wrap", gap: 6 },
  tag: {
    background: "#e8f0fe",
    color: "#1a56db",
    borderRadius: 4,
    padding: "3px 10px",
    fontSize: 12,
    display: "flex",
    alignItems: "center",
    gap: 6,
  },
  tagRemove: {
    cursor: "pointer",
    color: "#666",
    fontWeight: 700,
    fontSize: 14,
    lineHeight: 1,
    background: "none",
    border: "none",
    padding: 0,
  },
  addBtn: {
    padding: "8px 14px",
    background: "#f3f4f6",
    border: "1px solid #d1d5db",
    borderRadius: 6,
    fontSize: 13,
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
  submitBtn: {
    width: "100%",
    padding: "12px",
    background: "#cc0000",
    color: "white",
    border: "none",
    borderRadius: 7,
    fontSize: 16,
    fontWeight: 700,
    cursor: "pointer",
    marginTop: 8,
    transition: "background 0.15s",
  },
  disabledBtn: {
    width: "100%",
    padding: "12px",
    background: "#999",
    color: "white",
    border: "none",
    borderRadius: 7,
    fontSize: 16,
    fontWeight: 700,
    cursor: "not-allowed",
    marginTop: 8,
  },
  loading: {
    textAlign: "center",
    padding: "40px 0",
    color: "#666",
  },
  spinner: {
    display: "inline-block",
    width: 28,
    height: 28,
    border: "3px solid #e5e7eb",
    borderTop: "3px solid #cc0000",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
    marginBottom: 12,
  },
  error: {
    background: "#fef2f2",
    border: "1px solid #fca5a5",
    borderRadius: 7,
    padding: "14px 16px",
    color: "#dc2626",
    marginBottom: 16,
    fontSize: 14,
  },
  planSection: { marginBottom: 22 },
  planSectionTitle: {
    fontWeight: 700,
    fontSize: 14,
    color: "#cc0000",
    marginBottom: 8,
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  planItem: {
    padding: "7px 0 7px 14px",
    borderLeft: "3px solid #e5e7eb",
    fontSize: 14,
    color: "#374151",
    marginBottom: 5,
    lineHeight: 1.5,
  },
  downloadBtn: {
    display: "inline-block",
    marginTop: 16,
    padding: "9px 20px",
    background: "#059669",
    color: "white",
    border: "none",
    borderRadius: 6,
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
  },
  emptyState: {
    textAlign: "center",
    padding: "50px 20px",
    color: "#9ca3af",
    fontSize: 15,
  },
  orderList: { marginBottom: 24 },
  orderItem: {
    display: "block",
    width: "100%",
    padding: "12px 14px",
    marginBottom: 8,
    textAlign: "left",
    background: "#f8fafc",
    border: "1px solid #e2e8f0",
    borderRadius: 8,
    cursor: "pointer",
    fontSize: 14,
    color: "#1e293b",
    transition: "background 0.15s, border-color 0.15s",
  },
  orderItemHover: { background: "#f1f5f9", borderColor: "#cbd5e1" },
  orderItemMeta: { fontSize: 12, color: "#64748b", marginTop: 4 },
};

// ─────────────────────────────────────────────
// TagInput — reusable component for list fields
// ─────────────────────────────────────────────
function TagInput({ values, onChange, placeholder }) {
  const [draft, setDraft] = useState("");

  function add() {
    const v = draft.trim();
    if (v && !values.includes(v)) onChange([...values, v]);
    setDraft("");
  }

  return (
    <div>
      <div style={S.tagInput}>
        <input
          style={S.input}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), add())}
          placeholder={placeholder}
        />
        <button style={S.addBtn} onClick={add} type="button">+ Add</button>
      </div>
      <div style={S.tagList}>
        {values.map((v, i) => (
          <span key={i} style={S.tag}>
            {v}
            <button
              style={S.tagRemove}
              onClick={() => onChange(values.filter((_, j) => j !== i))}
            >×</button>
          </span>
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// CarePlan display + download
// ─────────────────────────────────────────────
function CarePlanView({ carePlan, orderInfo }) {
  const sections = [
    { key: "problem_list", label: "Problem List", icon: "📋" },
    { key: "goals", label: "Goals", icon: "🎯" },
    { key: "pharmacist_interventions", label: "Pharmacist Interventions", icon: "💊" },
    { key: "monitoring_plan", label: "Monitoring Plan", icon: "📊" },
  ];

  function downloadTxt() {
    const lines = [
      "SPECIALTY PHARMACY CARE PLAN",
      "=".repeat(50),
      `Patient: ${orderInfo.patient_first_name} ${orderInfo.patient_last_name}`,
      `MRN: ${orderInfo.patient_mrn}`,
      `Medication: ${orderInfo.medication_name}`,
      `Provider: ${orderInfo.referring_provider} (NPI: ${orderInfo.referring_provider_npi})`,
      `Generated: ${new Date().toLocaleString()}`,
      "",
    ];

    sections.forEach(({ key, label }) => {
      lines.push(label.toUpperCase());
      lines.push("-".repeat(30));
      (carePlan[key] || []).forEach((item) => lines.push(`• ${item}`));
      lines.push("");
    });

    const blob = new Blob([lines.join("\n")], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `care_plan_${orderInfo.patient_mrn}_${orderInfo.medication_name}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div>
      {sections.map(({ key, label }) => (
        <div key={key} style={S.planSection}>
          <div style={S.planSectionTitle}>{label}</div>
          {(carePlan[key] || []).map((item, i) => (
            <div key={i} style={S.planItem}>{item}</div>
          ))}
        </div>
      ))}
      <button style={S.downloadBtn} onClick={downloadTxt}>
        ⬇ Download as .txt
      </button>
    </div>
  );
}

// ─────────────────────────────────────────────
// Main App
// ─────────────────────────────────────────────
const EMPTY_FORM = {
  patient_first_name: "",
  patient_last_name: "",
  patient_mrn: "",
  patient_dob: "",
  referring_provider: "",
  referring_provider_npi: "",
  primary_diagnosis: "",
  additional_diagnoses: [],
  medication_name: "",
  medication_history: [],
  patient_records: "",
};

// Sample data so you can try it immediately
const SAMPLE_FORM = {
  patient_first_name: "Jane",
  patient_last_name: "Smith",
  patient_mrn: "001234",
  patient_dob: "1990-01-15",
  referring_provider: "Dr. Michael Chen",
  referring_provider_npi: "1234567890",
  primary_diagnosis: "G70.01",
  additional_diagnoses: ["I10", "K21.0"],
  medication_name: "IVIG",
  medication_history: ["Pyridostigmine 60mg q6h PRN", "Prednisone 10mg daily"],
  patient_records:
    "Patient presents with progressive proximal muscle weakness and ptosis over 2 weeks. AChR antibody positive. MGFA class IIb. Neurology recommends IVIG for rapid symptomatic control. Current meds: Lisinopril 10mg, Omeprazole 20mg. No known drug allergies. Weight 72kg.",
};

export default function App() {
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null); // { care_plan, order_id, orderInfo }
  const [orderList, setOrderList] = useState([]); // [{ order_id, created_at, patient_name, medication_name }]
  const [ordersLoading, setOrdersLoading] = useState(true);
  const [ordersError, setOrdersError] = useState(null);

  function fetchOrders() {
    setOrdersError(null);
    setOrdersLoading(true);
    fetch("/api/orders/")
      .then((r) => r.json())
      .then((data) => {
        setOrderList(data.orders || []);
        setOrdersError(null);
      })
      .catch((err) => {
        setOrderList([]);
        setOrdersError("Could not load orders. Is the backend running?");
      })
      .finally(() => setOrdersLoading(false));
  }

  useEffect(() => {
    fetchOrders();
  }, []);

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function loadOrder(orderId) {
    setError(null);
    try {
      const res = await fetch(`/api/orders/${orderId}/`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to load order");
      setResult({
        order_id: data.order_id,
        care_plan: data.care_plan,
        orderInfo: data,
      });
    } catch (e) {
      setError(e.message);
      setResult(null);
    }
  }

  async function handleSubmit() {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch("/api/generate-care-plan/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Unknown error");
      setResult({
        order_id: data.order_id,
        care_plan: data.care_plan ?? null,
        orderInfo: form,
        message: data.message,
      });
      setOrderList((prev) => [
        { order_id: data.order_id, created_at: new Date().toISOString(), patient_name: `${form.patient_first_name} ${form.patient_last_name}`, medication_name: form.medication_name },
        ...prev,
      ]);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const isReady =
    form.patient_first_name &&
    form.patient_last_name &&
    form.medication_name &&
    form.primary_diagnosis &&
    form.patient_records;

  return (
    <div style={S.app}>
      {/* inject spinner keyframe */}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      {/* Header */}
      <div style={S.header}>
        <div>
          <p style={S.headerTitle}>CVS Care Plan Generator</p>
          <p style={S.headerSub}>Specialty Pharmacy · Powered by Claude AI</p>
        </div>
      </div>

      <div style={S.layout}>
        {/* ── LEFT: Existing Orders + Input Form ── */}
        <div style={S.card}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <p style={{ ...S.cardTitle, margin: 0 }}>Existing Orders</p>
            <button
              type="button"
              style={{ ...S.addBtn, padding: "6px 12px" }}
              onClick={fetchOrders}
              disabled={ordersLoading}
            >
              {ordersLoading ? "Loading…" : "↻ Refresh"}
            </button>
          </div>
          <div style={S.orderList}>
            {ordersError && (
              <p style={{ margin: "0 0 8px", fontSize: 13, color: "#dc2626" }}>{ordersError}</p>
            )}
            {!ordersLoading && orderList.length === 0 && !ordersError && (
              <p style={{ margin: 0, fontSize: 14, color: "#94a3b8" }}>No orders yet. Create one below.</p>
            )}
            {!ordersLoading && orderList.map((o) => (
              <button
                key={o.order_id}
                type="button"
                style={{
                  ...S.orderItem,
                  ...(result?.order_id === o.order_id ? S.orderItemHover : {}),
                }}
                onClick={() => loadOrder(o.order_id)}
              >
                <strong>{o.patient_name}</strong> · {o.medication_name || "—"}
                <div style={S.orderItemMeta}>
                  {o.created_at ? new Date(o.created_at).toLocaleString() : ""} · ID: {o.order_id.slice(0, 8)}…
                </div>
              </button>
            ))}
          </div>

          <p style={S.cardTitle}>New Care Plan Order</p>

          {/* Patient */}
          <div style={S.section}>
            <span style={S.sectionLabel}>Patient</span>
            <div style={{ ...S.row, marginBottom: 10 }}>
              <input
                style={S.input}
                placeholder="First Name"
                value={form.patient_first_name}
                onChange={(e) => set("patient_first_name", e.target.value)}
              />
              <input
                style={S.input}
                placeholder="Last Name"
                value={form.patient_last_name}
                onChange={(e) => set("patient_last_name", e.target.value)}
              />
            </div>
            <input
              style={S.input}
              placeholder="MRN (6-digit ID)"
              value={form.patient_mrn}
              onChange={(e) => set("patient_mrn", e.target.value)}
            />
            <input
              style={{ ...S.input, marginBottom: 0 }}
              type="date"
              placeholder="Date of Birth"
              value={form.patient_dob}
              onChange={(e) => set("patient_dob", e.target.value)}
            />
          </div>

          {/* Provider */}
          <div style={S.section}>
            <span style={S.sectionLabel}>Referring Provider</span>
            <div style={{ ...S.row, marginBottom: 0 }}>
              <input
                style={S.input}
                placeholder="Provider Name"
                value={form.referring_provider}
                onChange={(e) => set("referring_provider", e.target.value)}
              />
              <input
                style={S.input}
                placeholder="NPI (10 digits)"
                value={form.referring_provider_npi}
                onChange={(e) => set("referring_provider_npi", e.target.value)}
              />
            </div>
          </div>

          {/* Diagnoses */}
          <div style={S.section}>
            <span style={S.sectionLabel}>Diagnosis</span>
            <input
              style={{ ...S.input, marginBottom: 10 }}
              placeholder="Primary Diagnosis (ICD-10, e.g. G70.01)"
              value={form.primary_diagnosis}
              onChange={(e) => set("primary_diagnosis", e.target.value)}
            />
            <span style={{ ...S.sectionLabel, marginTop: 4 }}>Additional Diagnoses</span>
            <TagInput
              values={form.additional_diagnoses}
              onChange={(v) => set("additional_diagnoses", v)}
              placeholder="ICD-10 code, press Enter"
            />
          </div>

          {/* Medication */}
          <div style={S.section}>
            <span style={S.sectionLabel}>Medication</span>
            <input
              style={{ ...S.input, marginBottom: 10 }}
              placeholder="Medication Name"
              value={form.medication_name}
              onChange={(e) => set("medication_name", e.target.value)}
            />
            <span style={{ ...S.sectionLabel, marginTop: 4 }}>Medication History</span>
            <TagInput
              values={form.medication_history}
              onChange={(v) => set("medication_history", v)}
              placeholder="e.g. Lisinopril 10mg daily"
            />
          </div>

          {/* Patient Records */}
          <div style={S.section}>
            <span style={S.sectionLabel}>Patient Records / Clinical Notes</span>
            <textarea
              style={{ ...S.textarea, minHeight: 120 }}
              placeholder="Paste clinical notes, history, or relevant patient information here..."
              value={form.patient_records}
              onChange={(e) => set("patient_records", e.target.value)}
            />
          </div>

          {/* Actions */}
          <div style={{ display: "flex", gap: 10, marginBottom: 12 }}>
            <button
              style={{ ...S.addBtn, flex: 1 }}
              onClick={() => setForm(SAMPLE_FORM)}
            >
              Fill Sample Data
            </button>
            <button
              style={{ ...S.addBtn, flex: 1 }}
              onClick={() => { setForm(EMPTY_FORM); setResult(null); setError(null); }}
            >
              Clear Form
            </button>
          </div>

          {error && <div style={S.error}>⚠ {error}</div>}

          <button
            style={isReady && !loading ? S.submitBtn : S.disabledBtn}
            onClick={handleSubmit}
            disabled={!isReady || loading}
          >
            {loading ? "Submitting..." : "Generate Care Plan →"}
          </button>
        </div>

        {/* ── RIGHT: Result Panel ── */}
        <div style={S.card}>
          <p style={S.cardTitle}>Generated Care Plan</p>

          {loading && (
            <div style={S.loading}>
              <div style={S.spinner} />
              <p style={{ margin: 0 }}>Submitting...</p>
            </div>
          )}

          {!loading && !result && !error && (
            <div style={S.emptyState}>
              Fill in the patient form and click<br />
              <strong>Generate Care Plan</strong> to get started.
            </div>
          )}

          {!loading && result && (
            <>
              {result.message && (
                <p style={{ fontSize: 14, color: "#059669", marginBottom: 8, fontWeight: 600 }}>
                  {result.message}
                </p>
              )}
              {result.order_id && (
                <p style={{ fontSize: 13, color: "#666", marginBottom: 10 }}>
                  Order ID: <code style={{ background: "#f0f0f0", padding: "2px 6px", borderRadius: 4 }}>{result.order_id}</code>
                </p>
              )}
              {result.care_plan ? (
                <CarePlanView
                  carePlan={result.care_plan}
                  orderInfo={result.orderInfo}
                />
              ) : (
                <div style={S.emptyState}>
                  Care plan not available (pending, processing, or failed for this order).
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
