import { useState } from "react";
import axios from "axios";
import {
  QUESTIONS,
  QUESTIONS_PER_PAGE,
  TOTAL_PAGES,
} from "./data/questions";
import QuestionCard from "./components/QuestionCard";
import ResultCard from "./components/ResultCard";

type Answers = Record<string, number>;

interface PredictResponse {
  clinico: { score: number; nivel: string; max_score: number; porcentaje: number };
  ml: { nivel: string; probabilidades: Record<string, number> };
  coinciden: boolean;
}

export default function App() {
  const [page, setPage]       = useState(0);
  const [answers, setAnswers] = useState<Answers>({});
  const [result, setResult]   = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  const pageQuestions = QUESTIONS.slice(
    (page - 1) * QUESTIONS_PER_PAGE,
    page * QUESTIONS_PER_PAGE
  );

  const answered      = pageQuestions.filter(q => answers[q.key] !== undefined).length;
  const allAnswered   = answered === pageQuestions.length;
  const totalAnswered = QUESTIONS.filter(q => answers[q.key] !== undefined).length;
  const progress      = Math.round((totalAnswered / QUESTIONS.length) * 100);

  const handleAnswer = (key: string, val: number) =>
    setAnswers(prev => ({ ...prev, [key]: val }));

  const handleNext = () => {
    if (page < TOTAL_PAGES) {
      setPage(p => p + 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    try {
      const payload = {
        ...Object.fromEntries(QUESTIONS.map(q => [q.key, answers[q.key] ?? 2])),
        age: 20, gender: 2, education: 3,
      };
      const { data } = await axios.post<PredictResponse>(
        "https://t81rg91w-8000.brs.devtunnels.ms/predict",
        payload
      );
      setResult(data);
    } catch {
      setError("No se pudo conectar con el servidor. Asegúrate de que el backend esté corriendo.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setAnswers({});
    setResult(null);
    setPage(0);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const wrap: React.CSSProperties = {
    minHeight: "100vh",
    background: "#f5f3ff",
    fontFamily: "system-ui, -apple-system, sans-serif",
    padding: "24px 16px",
  };
  const container: React.CSSProperties = { maxWidth: 620, margin: "0 auto" };

  if (result) {
    return (
      <div style={wrap}>
        <div style={container}>
          <ResultCard result={result} onReset={handleReset} />
        </div>
      </div>
    );
  }

  if (page === 0) {
    return (
      <div style={wrap}>
        <div style={container}>
          <div style={{ background: "#fff", borderRadius: 16, overflow: "hidden", boxShadow: "0 4px 24px rgba(0,0,0,.08)" }}>
            <div style={{ background: "#6366f1", padding: "40px 32px", textAlign: "center", color: "#fff" }}>
              <div style={{ fontSize: 56, marginBottom: 12 }}>🧠</div>
              <h1 style={{ margin: 0, fontSize: 26, fontWeight: 800 }}>Test de Ansiedad DASS-42</h1>
              <p style={{ margin: "12px 0 0", opacity: .85, fontSize: 15 }}>
                Depression Anxiety Stress Scales · Validado internacionalmente
              </p>
            </div>
            <div style={{ padding: "32px" }}>
              <p style={{ color: "#374151", lineHeight: 1.7, marginTop: 0 }}>
                Este cuestionario consta de <strong>42 afirmaciones</strong>. Lee cada una y selecciona
                con qué frecuencia te ha ocurrido <strong>durante la última semana</strong>.
              </p>
              <div style={{ background: "#f0f4ff", borderRadius: 10, padding: "16px 20px", marginBottom: 24 }}>
                {["Nunca", "A veces", "Frecuentemente", "Casi siempre"].map((l, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: i < 3 ? 8 : 0 }}>
                    <span style={{
                      width: 28, height: 28, borderRadius: 6, background: "#6366f1",
                      color: "#fff", fontWeight: 700, display: "flex",
                      alignItems: "center", justifyContent: "center", fontSize: 13, flexShrink: 0
                    }}>{i + 1}</span>
                    <span style={{ color: "#374151", fontSize: 14 }}>{l}</span>
                  </div>
                ))}
              </div>
              <p style={{ fontSize: 12, color: "#9ca3af", marginBottom: 24, lineHeight: 1.5 }}>
                Tus respuestas son anónimas. Este test es orientativo y no reemplaza
                el diagnóstico de un profesional de la salud.
              </p>
              <button
                onClick={() => setPage(1)}
                style={{
                  width: "100%", padding: "16px", borderRadius: 12,
                  border: "none", background: "#6366f1", color: "#fff",
                  fontWeight: 700, fontSize: 16, cursor: "pointer",
                }}
              >
                Comenzar el test
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const isLastPage = page === TOTAL_PAGES;

  return (
    <div style={wrap}>
      <div style={container}>
        {/* Progreso */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <span style={{ fontWeight: 700, color: "#1f2937", fontSize: 15 }}>
              Página {page} de {TOTAL_PAGES}
            </span>
            <span style={{ fontSize: 13, color: "#6b7280" }}>{progress}% completado</span>
          </div>
          <div style={{ background: "#e5e7eb", borderRadius: 99, height: 8 }}>
            <div style={{
              width: `${progress}%`, background: "#6366f1",
              borderRadius: 99, height: 8, transition: "width .4s ease"
            }} />
          </div>
        </div>

        {/* Preguntas */}
        {pageQuestions.map((q, i) => (
          <QuestionCard
            key={q.key}
            index={(page - 1) * QUESTIONS_PER_PAGE + i + 1}
            text={q.text}
            value={answers[q.key]}
            onChange={(val) => handleAnswer(q.key, val)}
          />
        ))}

        {error && (
          <div style={{
            background: "#fef2f2", border: "1px solid #fecaca",
            borderRadius: 10, padding: "12px 16px",
            color: "#dc2626", marginBottom: 16, fontSize: 14
          }}>
            {error}
          </div>
        )}

        {/* Navegación */}
        <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
          <button
            onClick={() => { setPage(p => p - 1); window.scrollTo({ top: 0, behavior: "smooth" }); }}
            style={{
              flex: 1, padding: "14px", borderRadius: 10,
              border: "2px solid #e5e7eb", background: "#fff",
              color: "#374151", fontWeight: 600, fontSize: 15, cursor: "pointer",
            }}
          >
            Anterior
          </button>

          {isLastPage ? (
            <button
              onClick={handleSubmit}
              disabled={!allAnswered || loading}
              style={{
                flex: 2, padding: "14px", borderRadius: 10, border: "none",
                background: allAnswered && !loading ? "#6366f1" : "#c7d2fe",
                color: "#fff", fontWeight: 700, fontSize: 15,
                cursor: allAnswered && !loading ? "pointer" : "not-allowed",
              }}
            >
              {loading ? "Analizando..." : "Ver resultado"}
            </button>
          ) : (
            <button
              onClick={handleNext}
              disabled={!allAnswered}
              style={{
                flex: 2, padding: "14px", borderRadius: 10, border: "none",
                background: allAnswered ? "#6366f1" : "#c7d2fe",
                color: "#fff", fontWeight: 700, fontSize: 15,
                cursor: allAnswered ? "pointer" : "not-allowed",
              }}
            >
              Siguiente ({answered}/{pageQuestions.length})
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
