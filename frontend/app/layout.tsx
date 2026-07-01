import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "ClaimPilot — state-aware claim automation (demo)",
  description: "Demonstration system. Synthetic data. Not legal advice.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {/* Persistent compliance disclaimer */}
        <div className="bg-amber-100 text-amber-900 text-xs sm:text-sm text-center px-4 py-1.5 border-b border-amber-200">
          Demonstration system · Synthetic data · Not legal advice; does not replace official state
          claim processes.
        </div>

        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto max-w-6xl px-4 h-14 flex items-center gap-6">
            <Link href="/" className="font-semibold text-slate-900">
              Claim<span className="text-sky-600">Pilot</span>
            </Link>
            <nav className="flex items-center gap-4 text-sm text-slate-600">
              <Link href="/search" className="hover:text-slate-900">
                Search
              </Link>
              <Link href="/compare" className="hover:text-slate-900">
                Compare states
              </Link>
            </nav>
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
