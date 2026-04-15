import type { Metadata } from "next";
import { CreateGroupForm } from "@/components/layout/CreateGroupForm";
import { Logo } from "@/components/ui/Logo";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Create a Group",
};

export default function CreateGroupPage() {
  return (
    <div className="h-full">
      <header className="bg-white border-b border-slate-100 sticky top-0 z-40">
        <div className="max-w-lg mx-auto px-4 h-14 flex items-center gap-3">
          <Link
            href="/"
            className="inline-flex items-center justify-center w-9 h-9 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
            aria-label="Go back to home"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
              <path d="M11.25 4.5L6.75 9l4.5 4.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </Link>
          <h1 className="text-base font-semibold text-slate-800">Create a Group</h1>
        </div>
      </header>

      <main className="max-w-lg mx-auto px-4 py-8 animate-fade-in">
        <p className="text-slate-500 text-sm mb-8 leading-relaxed">
          Name your group and enter your display name. Friends join via a
          shareable link — no account needed.
        </p>
        <CreateGroupForm />
      </main>
    </div>
  );
}
