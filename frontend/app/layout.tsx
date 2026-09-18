import type { Metadata } from "next";
import { Geist, Geist_Mono, Noto_Naskh_Arabic } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// Sindhi needs real Arabic glyph shaping (letter joining) -- Geist/Arial
// don't have Arabic glyphs at all, which is why م was rendering disconnected.
// Naskh (not Nastaliq) chosen for small-screen legibility, and it covers
// Sindhi's extended letters (ڏ ڄ ٺ ڦ ڻ ڱ ڳ) correctly.
const notoNaskhArabic = Noto_Naskh_Arabic({
  variable: "--font-sindhi",
  subsets: ["arabic"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Naari AI",
  description: "عورتن جي صحت بابت سوالن جا جواب — Sindhi women's health information assistant",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="sd"
      dir="rtl"
      className={`${geistSans.variable} ${geistMono.variable} ${notoNaskhArabic.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}