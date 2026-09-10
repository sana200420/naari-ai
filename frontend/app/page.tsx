"use client";

import { useState } from "react";
import {
  CalendarHeart,
  Brain,
  Baby,
  HeartPulse,
  Apple,
  Flower2,
  HeartHandshake,
  Sparkles,
  Send,
} from "lucide-react";

const categories = [
  {
    label: "حيض جي صحت",
    query: "حيض جي چڪر ڇا آهي؟",
    icon: CalendarHeart,
  },
  {
    label: "ذهني صحت",
    query: "روزاني دٻاءُ کي ڪيئن منظم ڪجي؟",
    icon: Brain,
  },
  {
    label: "حمل جي صحت",
    query: "حمل جي پهرين نشاني ڇا هوندي آهي؟",
    icon: Baby,
  },
  {
    label: "پي سي او ايس",
    query: "پي سي او ايس ڇا آهي؟",
    icon: HeartPulse,
  },
  {
    label: "غذائيت",
    query: "عورتن لاء متوازن غذا جو مطلب ڇا آهي؟",
    icon: Apple,
  },
  {
    label: "مينوپاز",
    query: "مينوپاز ڇا آهي؟",
    icon: Flower2,
  },
  {
    label: "زرخيزي",
    query: "تصور اصل ۾ ڪيئن ٿيندو آهي؟",
    icon: HeartHandshake,
  },
  {
    label: "صفائي",
    query: "هڪ معمولي اندام جي گند عام آهي؟",
    icon: Sparkles,
  },
];

export default function Home() {
  const [messages, setMessages] = useState<
    { role: string; text: string }[]
  >([]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendMessage(customQuery?: string) {
    const query = customQuery ?? input;

    if (!query.trim() || loading) return;

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        text: query,
      },
    ]);

    setInput("");
    setLoading(true);

    try {
      const res = await fetch(
        "https://naari-ai-production.up.railway.app/ask",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            query,
            language: "sindhi",
          }),
        }
      );

      if (!res.ok) {
        throw new Error("Backend request failed");
      }

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text:
            data.answer ||
            "معاف ڪجو، جواب حاصل نه ٿي سگهيو.",
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text:
            "معاف ڪجو، ڪا خرابي آئي آهي. مهرباني ڪري ٻيهر ڪوشش ڪريو.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main
      dir="rtl"
      style={{
        minHeight: "100vh",
        background: "#FFF9F5",
        padding: "24px 16px",
        fontFamily: "Arial, Helvetica, sans-serif",
      }}
    >
      <div
        style={{
          maxWidth: "680px",
          margin: "0 auto",
        }}
      >
        {/* ================= HEADER ================= */}

        <header
          style={{
            background: "#4A1942",
            borderRadius: "26px",
            padding: "28px 20px",
            textAlign: "center",
            color: "#FFFFFF",
            marginBottom: "20px",
            boxShadow:
              "0 12px 30px rgba(74, 25, 66, 0.15)",
          }}
        >
          {/* LOGO */}

          <div
            style={{
              width: "82px",
              height: "82px",
              margin: "0 auto 14px",
              borderRadius: "20px",
              background: "#FFFFFF",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              overflow: "hidden",
              boxShadow:
                "0 6px 18px rgba(249, 115, 22, 0.25)",
            }}
          >
            <img
              src="/Naari_AI_Logo.png"
              alt="Naari AI Logo"
              style={{
                width: "100%",
                height: "100%",
                objectFit: "contain",
                padding: "6px",
              }}
            />
          </div>

          <h1
            style={{
              margin: "0",
              fontSize: "30px",
              fontWeight: "700",
              letterSpacing: "0.3px",
            }}
          >
            Naari AI
          </h1>

          <p
            style={{
              margin: "8px 0 0",
              fontSize: "17px",
              lineHeight: "1.8",
              color: "#FBE9E2",
            }}
          >
            عورتن جي صحت بابت سوالن جا جواب
          </p>
        </header>

        {/* ================= WELCOME ================= */}

        {messages.length === 0 && (
          <>
            <div
              style={{
                background: "#FFFFFF",
                borderRadius: "20px",
                padding: "20px",
                marginBottom: "18px",
                border: "1px solid #F0DDD7",
                boxShadow:
                  "0 5px 18px rgba(74, 25, 66, 0.05)",
                textAlign: "right",
              }}
            >
              <h2
                style={{
                  margin: "0 0 6px",
                  color: "#4A1942",
                  fontSize: "21px",
                  fontWeight: "700",
                }}
              >
                توهان ڪيئن مدد چاهيو ٿا؟
              </h2>

              <p
                style={{
                  margin: 0,
                  color: "#756A70",
                  fontSize: "16px",
                  lineHeight: "1.8",
                }}
              >
                هيٺ ڏنل موضوع چونڊيو يا پنهنجو سوال لکو.
              </p>
            </div>

            {/* ================= CATEGORY CARDS ================= */}

            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "repeat(2, minmax(0, 1fr))",
                gap: "13px",
                marginBottom: "22px",
              }}
            >
              {categories.map((category) => {
                const Icon = category.icon;

                return (
                  <button
                    key={category.label}
                    onClick={() =>
                      sendMessage(category.query)
                    }
                    disabled={loading}
                    style={{
                      minHeight: "100px",
                      padding: "16px",
                      background: "#FFFFFF",
                      color: "#4A1942",
                      border:
                        "1px solid #F0DDD7",
                      borderRadius: "18px",
                      cursor: loading
                        ? "not-allowed"
                        : "pointer",
                      opacity: loading ? 0.65 : 1,
                      boxShadow:
                        "0 4px 14px rgba(74, 25, 66, 0.06)",
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "flex-start",
                      justifyContent: "center",
                      gap: "9px",
                      fontSize: "16px",
                      fontWeight: "600",
                      textAlign: "right",
                    }}
                  >
                    <span
                      style={{
                        width: "44px",
                        height: "44px",
                        borderRadius: "13px",
                        background: "#FFF0E8",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      <Icon
                        size={24}
                        color="#F97316"
                        strokeWidth={1.8}
                      />
                    </span>

                    {category.label}
                  </button>
                );
              })}
            </div>
          </>
        )}

        {/* ================= CHAT MESSAGES ================= */}

        <div
          style={{
            minHeight:
              messages.length > 0 ? "420px" : "0",
            marginBottom: "18px",
          }}
        >
          {messages.map((message, index) => (
            <div
              key={index}
              style={{
                display: "flex",
                justifyContent:
                  message.role === "user"
                    ? "flex-start"
                    : "flex-end",
                margin: "14px 0",
              }}
            >
              <div
                style={{
                  maxWidth: "86%",
                  padding: "14px 17px",
                  background:
                    message.role === "user"
                      ? "#4A1942"
                      : "#FFFFFF",
                  color:
                    message.role === "user"
                      ? "#FFFFFF"
                      : "#30282D",
                  border:
                    message.role === "user"
                      ? "none"
                      : "1px solid #F0DDD7",
                  borderRadius:
                    message.role === "user"
                      ? "18px 18px 4px 18px"
                      : "18px 18px 18px 4px",
                  fontSize: "18px",
                  lineHeight: "1.85",
                  textAlign: "right",
                  boxShadow:
                    "0 5px 14px rgba(74, 25, 66, 0.07)",
                  whiteSpace: "pre-wrap",
                }}
              >
                {message.text}
              </div>
            </div>
          ))}

          {/* LOADING */}

          {loading && (
            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                margin: "14px 0",
              }}
            >
              <div
                style={{
                  background: "#FFF0E8",
                  color: "#C2410C",
                  border:
                    "1px solid #FED7C3",
                  borderRadius:
                    "18px 18px 18px 4px",
                  padding: "13px 17px",
                  fontSize: "17px",
                }}
              >
                جواب تيار ٿي رهيو آهي...
              </div>
            </div>
          )}
        </div>

        {/* ================= INPUT ================= */}

        <div
          style={{
            background: "#FFFFFF",
            padding: "10px",
            borderRadius: "21px",
            border:
              "1px solid #EBDDD8",
            boxShadow:
              "0 8px 25px rgba(74, 25, 66, 0.08)",
            display: "flex",
            gap: "9px",
            alignItems: "center",
            direction: "ltr",
          }}
        >
          <input
            value={input}
            onChange={(e) =>
              setInput(e.target.value)
            }
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                sendMessage();
              }
            }}
            disabled={loading}
            style={{
              flex: 1,
              minWidth: 0,
              padding: "14px",
              fontSize: "17px",
              textAlign: "right",
              color: "#30282D",
              background: "#FFF9F5",
              border:
                "1px solid #EBDDD8",
              borderRadius: "14px",
              outline: "none",
              direction: "rtl",
            }}
            placeholder="پنهنجو سوال لکو..."
          />

          <button
            onClick={() => sendMessage()}
            disabled={loading}
            style={{
              padding: "14px 19px",
              fontSize: "16px",
              fontWeight: "700",
              background: "#F97316",
              color: "#FFFFFF",
              border: "none",
              borderRadius: "14px",
              cursor: loading
                ? "not-allowed"
                : "pointer",
              opacity: loading ? 0.6 : 1,
              whiteSpace: "nowrap",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "7px",
            }}
          >
            <Send
              size={18}
              strokeWidth={2}
            />

            موڪليو
          </button>
        </div>

        {/* ================= FOOTER ================= */}

        <p
          style={{
            textAlign: "center",
            color: "#8A777F",
            fontSize: "13px",
            marginTop: "18px",
            marginBottom: "5px",
          }}
        >
          Naari AI • توهان جي صحت، اسان جي ترجيح
        </p>
      </div>
    </main>
  );
}
