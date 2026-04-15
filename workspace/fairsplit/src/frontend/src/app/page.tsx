import type { Metadata } from "next";
import Link from "next/link";
import { LandingHero } from "@/components/layout/LandingHero";
import { Logo } from "@/components/ui/Logo";
import { DevSeedLinks } from "@/components/layout/DevSeedLinks";

export const metadata: Metadata = {
  title: "FairSplit — Split expenses with friends. No accounts.",
};

export default function HomePage() {
  return (
    <div className="h-full">
      {/* Header */}
      <header className="bg-white border-b border-slate-100 sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          <Logo />
          <nav className="hidden sm:flex items-center gap-1" aria-label="Site navigation">
            <Link
              href="/create"
              className="text-sm text-slate-600 hover:text-slate-900 px-3 py-1.5 rounded-lg hover:bg-slate-100 transition-colors"
            >
              Create Group
            </Link>
          </nav>
        </div>
      </header>

      <main>
        <LandingHero />

        {/* Value props */}
        <section className="bg-white border-y border-slate-100" aria-label="Product features">
          <div className="max-w-5xl mx-auto px-4 py-14">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-12 h-12 bg-brand-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M13 10V3L4 14h7v7l9-11h-7z" stroke="#047857" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <h3 className="text-base font-semibold text-slate-800 mb-1">Zero friction</h3>
                <p className="text-sm text-slate-500 leading-relaxed">
                  Join with a link and a display name. No email. No password. No app download needed.
                </p>
              </div>

              <div className="text-center">
                <div className="w-12 h-12 bg-brand-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <circle cx="12" cy="12" r="9" stroke="#047857" strokeWidth="2"/>
                    <path d="M12 7v5l3 3" stroke="#047857" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                </div>
                <h3 className="text-base font-semibold text-slate-800 mb-1">No expense cap</h3>
                <p className="text-sm text-slate-500 leading-relaxed">
                  Log as many expenses as your trip needs. No daily limits. No ads. No upsells. Ever.
                </p>
              </div>

              <div className="text-center">
                <div className="w-12 h-12 bg-brand-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M9 12l2 2 4-4" stroke="#047857" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z" stroke="#047857" strokeWidth="2"/>
                  </svg>
                </div>
                <h3 className="text-base font-semibold text-slate-800 mb-1">Minimum transfers</h3>
                <p className="text-sm text-slate-500 leading-relaxed">
                  We compute the fewest bank transfers needed to settle all debts.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* How it works */}
        <section className="max-w-5xl mx-auto px-4 py-16" aria-label="How FairSplit works">
          <h2 className="text-2xl font-bold text-slate-800 text-center mb-12">How it works</h2>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-6 relative">
            {/* Connector line desktop */}
            <div className="hidden sm:block absolute top-6 left-[12.5%] right-[12.5%] h-px bg-slate-200 z-0" aria-hidden="true" />

            {[
              { num: 1, title: "Create a group", desc: "Name your group. You're the organizer." },
              { num: 2, title: "Share the link", desc: "Friends join with just their name. No signup." },
              { num: 3, title: "Log expenses", desc: "Track as you go. Split any way you want." },
              { num: 4, title: "Settle up", desc: "One tap. Minimum transfers. Done." },
            ].map((step) => (
              <div key={step.num} className="text-center relative z-10">
                <div className="w-12 h-12 bg-brand-700 text-white font-bold text-base rounded-full flex items-center justify-center mx-auto mb-4">
                  {step.num}
                </div>
                <h3 className="text-sm font-semibold text-slate-700 mb-1">{step.title}</h3>
                <p className="text-xs text-slate-400">{step.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Dev panel (hidden in production) */}
        {process.env.NEXT_PUBLIC_SHOW_DEV_PANEL === "true" ? (
          <DevPanel />
        ) : null}
      </main>
    </div>
  );
}

function DevPanel() {
  return (
    <section
      className="bg-amber-50 border-t border-amber-200 py-8"
      aria-label="Developer panel"
    >
      <div className="max-w-5xl mx-auto px-4">
        <p className="text-xs font-semibold text-amber-700 uppercase tracking-widest mb-4">
          Dev Panel — Seeded Groups
        </p>
        <p className="text-xs text-amber-600 mb-4">
          These groups are seeded by <code>seed.py</code>. Click a link to join as that member.
        </p>
        <div className="bg-white border border-amber-200 rounded-xl p-4">
          <p className="text-sm text-slate-600">
            Seeded group invite links will appear here after{" "}
            <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">seed.py</code> runs.
            The backend exposes seeded group data at{" "}
            <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">
              GET /api/v1/dev/seed-info
            </code>{" "}
            when <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">ENVIRONMENT=development</code>.
          </p>
          <div className="mt-3 pt-3 border-t border-slate-100">
            <DevSeedLinks />
          </div>
        </div>
      </div>
    </section>
  );
}
