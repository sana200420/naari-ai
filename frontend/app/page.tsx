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

// Override if the Space is renamed or moved.
const SPACE_URL =
  process.env.NEXT_PUBLIC_SPACE_URL ?? "https://sanapalijo-naari-ai.hf.space";

type AskResponse = {
  answer: string;
  path: string;
  confidence_band: string;
  retrieved_ids: number[];
  latency_ms: number;
};

/** Pull the payload out of Gradio's SSE stream.
 *  Frames look like:  "event: complete" then "data: [\"{...json...}\"]"
 *  The inner element is itself a JSON string, hence the double parse. */
function parseGradioSse(raw: string): AskResponse {
  let event: string | null = null;
  for (const rawLine of raw.split("\n")) {
    const line = rawLine.endsWith("\r") ? rawLine.slice(0, -1) : rawLine;
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:") && event === "complete") {
      return JSON.parse(JSON.parse(line.slice(5).trim())[0]) as AskResponse;
    }
  }
  throw new Error("no complete event in Gradio stream");
}

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
      // The backend is a Hugging Face Space. Gradio exposes each endpoint as a
      // two-step REST call: POST queues the job and returns an event_id, then
      // GET streams the result back as SSE. Plain fetch is deliberate --
      // @gradio/client hung on connect here and pulls a large dependency for
      // what is ultimately two HTTP requests.
      const post = await fetch(`${SPACE_URL}/gradio_api/call/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data: [query, "sindhi"] }),
      });
      if (!post.ok) throw new Error(`queue failed: HTTP ${post.status}`);
      const { event_id } = await post.json();

      const stream = await fetch(`${SPACE_URL}/gradio_api/call/ask/${event_id}`);
      if (!stream.ok) throw new Error(`stream failed: HTTP ${stream.status}`);
      const data = parseGradioSse(await stream.text());

      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: data.answer },
      ]);
    } catch (err) {
      // Show the user Sindhi, but leave the real cause in the console --
      // a silent catch-all is how the dead Railway backend went unnoticed.
      console.error("[naari] ask failed:", err);
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
