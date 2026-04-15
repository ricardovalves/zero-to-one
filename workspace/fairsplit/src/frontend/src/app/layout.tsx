import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Toaster } from "sonner";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
  preload: true,
});

export const metadata: Metadata = {
  title: {
    default: "FairSplit — Split expenses with friends. No accounts.",
    template: "%s — FairSplit",
  },
  description:
    "Create a group, share a link, log expenses together. One tap to see exactly who pays whom — minimum transfers, zero drama.",
  keywords: ["expense splitting", "split bills", "group expenses", "no signup"],
  openGraph: {
    title: "FairSplit — Split expenses with friends. No accounts.",
    description:
      "Split expenses with friends with zero friction. No account needed to join.",
    type: "website",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: "#047857",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body
        className={`${inter.variable} h-full bg-slate-50 font-sans antialiased`}
      >
        {children}
        <Toaster
          position="top-center"
          toastOptions={{
            style: {
              background: "#0f172a",
              color: "#f8fafc",
              fontSize: "0.875rem",
              fontWeight: "500",
              border: "none",
              borderRadius: "0.75rem",
              padding: "0.75rem 1rem",
            },
          }}
        />
      </body>
    </html>
  );
}
