"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export function LandingHero() {
  const router = useRouter();
  const [linkInput, setLinkInput] = useState("");
  const [linkError, setLinkError] = useState(false);

  function extractInviteToken(input: string): string | null {
    const trimmed = input.trim();
    // Match /join/{token} pattern
    const match =
      trimmed.match(/\/join\/([a-zA-Z0-9_-]+)/) ??
      trimmed.match(/^([a-zA-Z0-9_-]{8,})$/);
    return match?.[1] ?? null;
  }

  function handleLinkInput(e: React.ChangeEvent<HTMLInputElement>) {
    const val = e.target.value;
    setLinkInput(val);
    if (val.length === 0) {
      setLinkError(false);
    } else if (extractInviteToken(val)) {
      setLinkError(false);
    } else if (val.length > 5) {
      setLinkError(true);
    }
  }

  function handleJoinFromLink() {
    const token = extractInviteToken(linkInput);
    if (token) {
      router.push(`/join/${token}`);
    }
  }

  const canJoin = !!extractInviteToken(linkInput);

  return (
    <section className="max-w-5xl mx-auto px-4 pt-16 pb-12 sm:pt-24 sm:pb-20">
      <div className="max-w-2xl mx-auto text-center">
        {/* Badge */}
        <div className="inline-flex items-center gap-1.5 bg-brand-50 text-brand-700 text-xs font-semibold px-3 py-1.5 rounded-full mb-6 border border-brand-100">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
            <circle cx="6" cy="6" r="5" fill="#047857" opacity="0.2"/>
            <circle cx="6" cy="6" r="2.5" fill="#047857"/>
          </svg>
          Free forever · No account to join
        </div>

        {/* Headline */}
        <h1 className="text-4xl sm:text-5xl font-bold text-slate-900 tracking-tight leading-tight mb-4">
          Split expenses with<br />
          <span className="text-brand-700">friends.</span> No accounts.
        </h1>
        <p className="text-lg text-slate-500 mb-10 max-w-md mx-auto leading-relaxed">
          Create a group, share a link, log expenses together. One tap to see
          exactly who pays whom — and how many transfers it takes.
        </p>

        {/* Primary CTA */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center mb-6">
          <Link
            href="/create"
            className="inline-flex items-center justify-center gap-2 bg-brand-700 text-white font-semibold text-base px-7 py-3.5 rounded-xl hover:bg-brand-800 active:scale-[0.98] transition-all duration-150 shadow-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
              <path d="M9 3.75V14.25M3.75 9H14.25" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            Create a New Group
          </Link>
        </div>

        {/* Paste link */}
        <div className="text-center">
          <p className="text-sm text-slate-400 mb-3">Already have an invite link?</p>
          <div className="flex items-center gap-2 max-w-sm mx-auto">
            <label htmlFor="paste-link" className="sr-only">
              Paste group invite link
            </label>
            <input
              id="paste-link"
              type="url"
              inputMode="url"
              placeholder="Paste your group link here"
              value={linkInput}
              onChange={handleLinkInput}
              onKeyDown={(e) => e.key === "Enter" && canJoin && handleJoinFromLink()}
              className="flex-1 h-11 px-4 text-sm text-slate-700 bg-white border border-slate-200 rounded-xl placeholder-slate-400 transition-all duration-150 focus:outline-none focus:border-brand-700 focus:ring-1 focus:ring-brand-500/25"
              aria-label="Paste group invite link"
              aria-describedby={linkError ? "link-error" : undefined}
            />
            <button
              onClick={handleJoinFromLink}
              disabled={!canJoin}
              className="inline-flex items-center justify-center h-11 px-4 bg-brand-700 text-white text-sm font-semibold rounded-xl disabled:opacity-50 disabled:pointer-events-none transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
              aria-label="Join group from link"
            >
              Join
            </button>
          </div>
          {linkError ? (
            <p
              id="link-error"
              className="mt-2 text-xs text-rose-600"
              role="alert"
            >
              That doesn&apos;t look like a valid FairSplit link.
            </p>
          ) : null}
        </div>
      </div>
    </section>
  );
}
