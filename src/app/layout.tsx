import type { Metadata } from "next";
import { Geist, Geist_Mono, Fraunces } from "next/font/google";
import "./globals.css";

// Placeholder for Satoshi (self-hosted variable font per design spec).
// Swap for the real Satoshi-Variable.woff2 by replacing this with a
// @font-face + `--font-satoshi` custom property once the asset is available.
const satoshiFallback = Geist({
  variable: "--font-satoshi",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800", "900"],
});

// Old-world serif for headings — carries the "aged library / chess room" feel.
const fraunces = Fraunces({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  style: ["normal", "italic"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "IABTM — I Am Better Than Me",
  description:
    "IABTM's AI Curator turns digital media consumption into a purposeful, identity-aligned journey of self-actualization.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${satoshiFallback.variable} ${fraunces.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-(--color-bg-primary) text-(--color-ink)">
        {children}
      </body>
    </html>
  );
}
