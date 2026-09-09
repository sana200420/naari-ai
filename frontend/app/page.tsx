"use client";
import { useState } from "react";

const categories = [
  { label: "حيض جي صحت", query: "حيض جي چڪر ڇا آهي؟" },
  { label: "ذهني صحت", query: "روزاني دٻاءُ کي ڪيئن منظم ڪجي؟" },
  { label: "حمل جي صحت", query: "حمل جي پهرين نشاني ڇا هوندي آهي؟" },
  { label: "پي سي او ايس", query: "پي سي او ايس ڇا آهي؟" },
  { label: "غذائيت", query: "عورتن لاء متوازن غذا جو مطلب ڇا آهي؟" },
  { label: "مينوپاز", query: "مينوپاز ڇا آهي؟" },
  { label: "زرخيزي", query: "تصور اصل ۾ ڪيئن ٿيندو آهي؟" },
  { label: "صفائي", query: "هڪ معمولي اندام جي گند عام آهي؟" },
];

export default function Home() {
  const [messages, setMessages] = useState<{ role: string; text: string }[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendMessage(customQuery?: string) {
    const query = customQuery ?? input;
    if (!query.trim()) return;
    const userMsg = { role: "user", text: query };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("https://naari-ai-production.up.railway.app/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, language: "sindhi" }),
      });
      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: data.answer },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "معاف ڪجو، ڪا خرابي آئي آهي." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ padding: "20px", fontSize: "18px", lineHeight: 1.8, maxWidth: "500px", margin: "0 auto" }}>
      {/* Category shortcut cards */}
      {messages.length === 0 && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "10px",
            marginBottom: "20px",
          }}
        >
          {categories.map((cat) => (
            <button
              key={cat.label}
              onClick={() => sendMessage(cat.query)}
              style={{
                padding: "16px 10px",
                fontSize: "16px",
                background: "#e0f0ff",
                color: "#000000",
                border: "1px solid #90c0f0",
                borderRadius: "10px",
                textAlign: "right",
                cursor: "pointer",
              }}
            >
              {cat.label}
            </button>
          ))}
        </div>
      )}

      <div style={{ minHeight: "200px", marginBottom: "20px" }}>
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              textAlign: "right",
              margin: "10px 0",
              padding: "10px",
              background: m.role === "user" ? "#e0f0ff" : "#f0f0f0",
              borderRadius: "8px",
              color: "#000000",
            }}
          >
            {m.text}
          </div>
        ))}
        {loading && <p style={{ color: "#ffffff" }}>...لکجي رهيو آهي</p>}
      </div>

      <div style={{ display: "flex", gap: "8px" }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          style={{
            flex: 1,
            padding: "10px",
            fontSize: "18px",
            textAlign: "right",
            color: "#000000",
            background: "#ffffff",
            border: "1px solid #ccc",
            borderRadius: "6px",
          }}
          placeholder="پنهنجو سوال لکو..."
        />
        <button
          onClick={() => sendMessage()}
          style={{
            padding: "10px 20px",
            fontSize: "16px",
            background: "#2563eb",
            color: "#ffffff",
            border: "none",
            borderRadius: "6px",
          }}
        >
          موڪليو
        </button>
      </div>
    </main>
  );
}
