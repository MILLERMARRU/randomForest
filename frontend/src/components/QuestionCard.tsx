import { SCALE_LABELS } from "../data/questions";

interface Props {
  index: number;
  text: string;
  value: number | undefined;
  onChange: (val: number) => void;
}

export default function QuestionCard({ index, text, value, onChange }: Props) {
  return (
    <div style={{
      background: "#fff",
      borderRadius: 12,
      padding: "20px 24px",
      marginBottom: 16,
      boxShadow: "0 1px 4px rgba(0,0,0,.08)",
      borderLeft: `4px solid ${value ? "#6366f1" : "#e5e7eb"}`,
      transition: "border-color .2s"
    }}>
      <p style={{ margin: "0 0 16px", fontSize: 15, color: "#1f2937", lineHeight: 1.5 }}>
        <span style={{ fontWeight: 700, color: "#6366f1", marginRight: 8 }}>{index}.</span>
        {text}
      </p>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        {SCALE_LABELS.map(({ value: v, label }) => (
          <button
            key={v}
            onClick={() => onChange(v)}
            style={{
              flex: 1,
              minWidth: 110,
              padding: "10px 6px",
              borderRadius: 8,
              border: `2px solid ${value === v ? "#6366f1" : "#e5e7eb"}`,
              background: value === v ? "#6366f1" : "#f9fafb",
              color: value === v ? "#fff" : "#374151",
              fontWeight: value === v ? 700 : 400,
              cursor: "pointer",
              fontSize: 13,
              transition: "all .15s",
            }}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
