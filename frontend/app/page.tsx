"use client";

import Link from "next/link";
import { ShieldCheck, Sparkles } from "lucide-react";

export default function Landing() {
  return (
    <main
      dir="rtl"
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        background: "#FFF9F5",
        padding: "32px 20px",
        textAlign: "center",
      }}
    >
      <div
        style={{
          width: "88px",
          height: "88px",
          borderRadius: "26px",
          background: "#4A1942",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: "22px",
          boxShadow: "0 10px 30px rgba(74, 25, 66, 0.25)",
          overflow: "hidden",
        }}
      >
        <img
          src="/Naari_AI_Logo.png"
          alt="Naari AI Logo"
          style={{
            width: "70%",
            height: "70%",
            objectFit: "contain",
          }}
        />
      </div>

      <h1
        style={{
          margin: 0,
          fontSize: "28px",
          fontWeight: 800,
          color: "#4A1942",
        }}
      >
        Naari AI
      </h1>

      <p
        style={{
          marginTop: "10px",
          marginBottom: "6px",
          fontSize: "17px",
          color: "#4A1942",
          maxWidth: "420px",
          lineHeight: "1.8",
        }}
      >
        عورتن جي صحت بابت سوالن جا سولا ۽ محفوظ جواب، سنڌي ٻولي ۾
      </p>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "10px",
          margin: "26px 0",
          width: "100%",
          maxWidth: "360px",
        }}
      >
        <FeatureRow
          icon={<ShieldCheck size={20} color="#F97316" strokeWidth={1.8} />}
          text="ذريعا سان تصديق ٿيل ڄاڻ"
        />
        <FeatureRow
          icon={<Sparkles size={20} color="#F97316" strokeWidth={1.8} />}
          text="بغير نالي، خانگي ۽ آسان"
        />
      </div>

      <Link
        href="/chat"
        style={{
          display: "inline-block",
          padding: "16px 48px",
          background: "#F97316",
          color: "#FFFFFF",
          borderRadius: "16px",
          fontSize: "17px",
          fontWeight: 700,
          textDecoration: "none",
          boxShadow: "0 8px 20px rgba(249, 115, 22, 0.35)",
        }}
      >
        شروع ڪريو
      </Link>

      <p
        style={{
          marginTop: "28px",
          fontSize: "12px",
          color: "#8A6A78",
        }}
      >
        هي معلوماتي مقصدن لاءِ آهي، طبي مشوري جو متبادل ناهي
      </p>
    </main>
  );
}

function FeatureRow({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "10px",
        background: "#FFFFFF",
        border: "1px solid #F0DDD7",
        borderRadius: "14px",
        padding: "12px 16px",
      }}
    >
      {icon}
      <span style={{ fontSize: "14px", fontWeight: 600, color: "#4A1942" }}>{text}</span>
    </div>
  );
}