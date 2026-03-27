interface PredictResponse {
  clinico: { score: number; nivel: string; max_score: number; porcentaje: number };
  ml: { nivel: string; probabilidades: Record<string, number> };
  coinciden: boolean;
}

const COLORS: Record<string, string> = {
  Leve:     "#22c55e",
  Moderado: "#f59e0b",
  Severo:   "#ef4444",
};

const DESCRIPTIONS: Record<string, string> = {
  Leve:     "Los síntomas de ansiedad son leves. Se recomienda mantener hábitos saludables y técnicas de relajación.",
  Moderado: "Los síntomas son moderados. Considera hablar con un profesional de la salud mental.",
  Severo:   "Los síntomas son severos. Se recomienda buscar atención profesional a la brevedad.",
};

interface Props {
  result: PredictResponse;
  onReset: () => void;
}

export default function ResultCard({ result, onReset }: Props) {
  const { clinico, ml, coinciden } = result;
  const color = COLORS[clinico.nivel] ?? "#6366f1";

  return (
    <div style={{ maxWidth: 600, margin: "0 auto", fontFamily: "system-ui, sans-serif" }}>
      {/* Header */}
      <div style={{
        background: color,
        borderRadius: "16px 16px 0 0",
        padding: "32px 24px",
        textAlign: "center",
        color: "#fff",
      }}>
        <div style={{ fontSize: 48, marginBottom: 8 }}>
          {clinico.nivel === "Leve" ? "😌" : clinico.nivel === "Moderado" ? "😟" : "😰"}
        </div>
        <h2 style={{ margin: 0, fontSize: 28, fontWeight: 800 }}>
          Ansiedad {clinico.nivel}
        </h2>
        <p style={{ margin: "8px 0 0", opacity: .85, fontSize: 15 }}>
          Score clínico DASS: {clinico.score} / {clinico.max_score}
        </p>
      </div>

      {/* Barra de score */}
      <div style={{ background: "#f3f4f6", padding: "20px 24px" }}>
        <div style={{ background: "#e5e7eb", borderRadius: 99, height: 12 }}>
          <div style={{
            width: `${clinico.porcentaje}%`,
            background: color,
            borderRadius: 99,
            height: 12,
            transition: "width 1s ease"
          }} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6, fontSize: 12, color: "#6b7280" }}>
          <span>0 - Leve</span>
          <span>10 - Moderado</span>
          <span>15 - Severo</span>
        </div>
      </div>

      {/* Descripción */}
      <div style={{ background: "#fff", padding: "20px 24px" }}>
        <p style={{ margin: 0, color: "#374151", fontSize: 15, lineHeight: 1.6 }}>
          {DESCRIPTIONS[clinico.nivel]}
        </p>
      </div>

      {/* Predicción ML */}
      <div style={{ background: "#f9fafb", padding: "20px 24px", borderTop: "1px solid #f3f4f6" }}>
        <h3 style={{ margin: "0 0 12px", fontSize: 14, color: "#6b7280", fontWeight: 600, textTransform: "uppercase", letterSpacing: .5 }}>
          Modelo de Machine Learning
        </h3>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 12 }}>
          {Object.entries(ml.probabilidades).map(([nivel, prob]) => (
            <div key={nivel} style={{
              flex: 1,
              minWidth: 100,
              background: "#fff",
              border: `2px solid ${ml.nivel === nivel ? COLORS[nivel] : "#e5e7eb"}`,
              borderRadius: 10,
              padding: "12px 8px",
              textAlign: "center",
            }}>
              <div style={{ fontSize: 20, fontWeight: 800, color: COLORS[nivel] }}>{prob}%</div>
              <div style={{ fontSize: 12, color: "#6b7280", marginTop: 2 }}>{nivel}</div>
            </div>
          ))}
        </div>
        {coinciden ? (
          <p style={{ margin: 0, fontSize: 13, color: "#22c55e", fontWeight: 600 }}>
            ✓ El modelo ML coincide con la clasificación clínica — mayor confianza en el resultado.
          </p>
        ) : (
          <p style={{ margin: 0, fontSize: 13, color: "#f59e0b", fontWeight: 600 }}>
            ⚠ El modelo ML y la escala clínica difieren. El diagnóstico clínico tiene prioridad.
          </p>
        )}
      </div>

      {/* Disclaimer + botón */}
      <div style={{ background: "#fff", padding: "20px 24px", borderTop: "1px solid #f3f4f6", borderRadius: "0 0 16px 16px" }}>
        <p style={{ margin: "0 0 16px", fontSize: 12, color: "#9ca3af", lineHeight: 1.5 }}>
          Este resultado es orientativo y no reemplaza el diagnóstico de un profesional de la salud mental.
          El cuestionario DASS-42 es una herramienta de screening validada internacionalmente.
        </p>
        <button
          onClick={onReset}
          style={{
            width: "100%",
            padding: "14px",
            borderRadius: 10,
            border: "none",
            background: "#6366f1",
            color: "#fff",
            fontWeight: 700,
            fontSize: 15,
            cursor: "pointer",
          }}
        >
          Realizar el test de nuevo
        </button>
      </div>
    </div>
  );
}
