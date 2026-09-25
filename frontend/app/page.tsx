"use client";

import Link from "next/link";
import { ShieldCheck, Lock } from "lucide-react";

const facts = [
  {
    icon: ShieldCheck,
    text: "ذريعا سان تصديق ٿيل ڄاڻ",
  },
  {
    icon: Lock,
    text: "بغير نالي، خانگي ۽ آسان",
  },
];

export default function Landing() {
  return (
    <main
      dir="rtl"
      style={{
        minHeight: "100dvh",
        display: "flex",
        flexDirection: "column",
        background: "#FFF9F5",
        fontFamily: "var(--font-sindhi), Arial, Helvetica, sans-serif",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "440px",
          margin: "0 auto",
          padding: "28px 22px 22px",
          flex: 1,
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* ================= LETTERHEAD ================= */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            paddingBottom: "18px",
            borderBottom: "1px solid #F0DDD7",
          }}
        >
          <div
            style={{
              width: "42px",
              height: "42px",
              borderRadius: "11px",
              background: "#4A1942",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              overflow: "hidden",
              flexShrink: 0,
            }}
          >
            <img
              src="/Naari_AI_Logo.png"
              alt="Naari AI Logo"
              style={{ width: "100%", height: "100%", objectFit: "contain", padding: "5px" }}
            />
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "1px" }}>
            <span style={{ fontSize: "16px", fontWeight: 700, color: "#4A1942" }}>
              Naari AI
            </span>
            <span style={{ fontSize: "13px", color: "#8A777F" }}>نارِي اي آءِ</span>
          </div>
        </div>

        {/* ================= HERO ================= */}
        <div style={{ marginTop: "40px" }}>
          <h1
            style={{
              margin: 0,
              fontSize: "27px",
              fontWeight: 800,
              color: "#4A1942",
              lineHeight: 1.7,
            }}
          >
            عورتن جي صحت بابت سوالن جا سولا ۽ محفوظ جواب، سنڌي ٻولي ۾
          </h1>

          <div
            style={{
              width: "44px",
              height: "3px",
              background: "#F97316",
              borderRadius: "2px",
              margin: "18px 0 22px",
              marginInlineStart: "auto",
              marginInlineEnd: "0",
            }}
          />
        </div>

        {/* ================= TRUST FACTS ================= */}
        <div
          style={{
            background: "#FFFFFF",
            border: "1px solid #F0DDD7",
            borderRadius: "14px",
            overflow: "hidden",
          }}
        >
          {facts.map((fact, i) => {
            const Icon = fact.icon;
            return (
              <div
                key={fact.text}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  padding: "14px 16px",
                  borderTop: i === 0 ? "none" : "1px solid #F5EBE6",
                  borderRight: "3px solid #F97316",
                }}
              >
                <Icon size={18} color="#F97316" strokeWidth={1.8} />
                <span style={{ fontSize: "14.5px", fontWeight: 600, color: "#4A1942" }}>
                  {fact.text}
                </span>
              </div>
            );
          })}
        </div>

        {/* ================= SPACER + CTA ================= */}
        <div style={{ flex: 1, minHeight: "28px" }} />

        <Link
          href="/chat"
          style={{
            display: "block",
            textAlign: "center",
            padding: "16px",
            background: "#F97316",
            color: "#FFFFFF",
            borderRadius: "14px",
            fontSize: "16.5px",
            fontWeight: 700,
            textDecoration: "none",
            boxShadow: "0 8px 20px rgba(249, 115, 22, 0.28)",
          }}
        >
          شروع ڪريو
        </Link>

        {/* ================= FOOTER ================= */}
        <div style={{ marginTop: "22px", paddingTop: "14px", borderTop: "1px solid #F0DDD7" }}>
          <p style={{ margin: 0, fontSize: "12px", color: "#8A777F", lineHeight: 1.7 }}>
            هي معلوماتي مقصدن لاءِ آهي، طبي مشوري جو متبادل ناهي
          </p>
          <p style={{ margin: "4px 0 0", fontSize: "11.5px", color: "#B3A6AC" }}>
            توهان جي صحت، اسان جي ترجيح
          </p>
        </div>
      </div>
    </main>
  );
}