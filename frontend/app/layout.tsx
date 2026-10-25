import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Company-OS | Foundation",
  description: "Initial Next.js + Python FastAPI foundation for Company-OS.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fa" dir="rtl">
      <body>{children}</body>
    </html>
  );
}
