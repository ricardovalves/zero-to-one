"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { toast } from "sonner";
import Link from "next/link";
import {
  createSettlement,
  getBalances,
  getGroupMembers,
  getSettleUpPlan,
} from "@/lib/api";
import { decodeStoredSession } from "@/lib/session";
import { copyToClipboard } from "@/lib/utils";
import {
  getAvatarColor,
  getBalanceStatus,
  getInitials,
  ApiError,
  type Balance,
  type Transfer,
} from "@/types";
import { Skeleton, MemberRowSkeleton } from "@/components/ui/Skeleton";
import { BottomNav } from "@/components/layout/BottomNav";

interface Props {
  groupId: string;
}

export function SettleUpClient({ groupId }: Props) {
  const router = useRouter();
  const session = decodeStoredSession(groupId);

  const [settledTransferIds, setSettledTransferIds] = useState<Set<number>>(new Set());
  const [settling, setSettling] = useState<Set<number>>(new Set());
  const [showCelebration, setShowCelebration] = useState(false);
  const [copyLabel, setCopyLabel] = useState("Copy Payment Plan");

  // Settle-up plan
  const { data: plan, isLoading: planLoading, mutate: mutatePlan } = useSWR(
    `settle-up-${groupId}`,
    () => getSettleUpPlan(groupId),
    { revalidateOnFocus: true }
  );

  // Balances
  const { data: balances, isLoading: balancesLoading } = useSWR<Balance[]>(
    `balances-${groupId}`,
    () => getBalances(groupId),
    { refreshInterval: 10000 }
  );

  // Members (for index lookup)
  const { data: members } = useSWR(
    `members-${groupId}`,
    () => getGroupMembers(groupId),
    { revalidateOnFocus: false }
  );

  function getMemberIndex(memberId: string): number {
    return members?.findIndex((m) => m.id === memberId) ?? 0;
  }

  async function markSettled(transferIndex: number, transfer: Transfer) {
    if (settling.has(transferIndex) || settledTransferIds.has(transferIndex)) return;

    setSettling((prev) => new Set(prev).add(transferIndex));
    try {
      await createSettlement(
        groupId,
        {
          payer_member_id: transfer.debtor_id,
          payee_member_id: transfer.creditor_id,
          amount_cents: transfer.amount_cents,
          currency: transfer.currency,
        },
        crypto.randomUUID()
      );

      setSettledTransferIds((prev) => {
        const next = new Set(prev).add(transferIndex);
        // Check if all settled
        if (plan && next.size >= plan.transfer_count) {
          setTimeout(() => {
            spawnConfetti();
            setTimeout(() => setShowCelebration(true), 400);
          }, 200);
        }
        return next;
      });

      mutatePlan();
      toast.success("Transfer marked as settled!");
    } catch (err) {
      if (err instanceof ApiError) {
        console.error("[SettleUpClient] API error", err.status, err.message);
        toast.error(err.message);
      } else {
        console.error("[SettleUpClient] Unexpected error", err);
        toast.error("Something went wrong. Please try again.");
      }
    } finally {
      setSettling((prev) => {
        const next = new Set(prev);
        next.delete(transferIndex);
        return next;
      });
    }
  }

  async function handleCopyPlan() {
    if (!plan) return;
    const ok = await copyToClipboard(plan.clipboard_text);
    if (ok) {
      setCopyLabel("Copied!");
      toast.success("Payment plan copied! Paste it in your group chat.");
      setTimeout(() => setCopyLabel("Copy Payment Plan"), 2200);
    }
  }

  function spawnConfetti() {
    const colors = [
      "#10b981", "#34d399", "#6ee7b7", "#a7f3d0",
      "#065f46", "#fbbf24", "#f9a8d4", "#93c5fd",
    ];
    for (let i = 0; i < 60; i++) {
      const el = document.createElement("div");
      const size = Math.random() * 10 + 5;
      el.style.cssText = `
        position: fixed;
        pointer-events: none;
        z-index: 9999;
        width: ${size}px;
        height: ${size}px;
        background: ${colors[Math.floor(Math.random() * colors.length)]};
        border-radius: ${Math.random() > 0.5 ? "50%" : "2px"};
        left: ${Math.random() * 100}vw;
        top: -20px;
        animation: confettiFall ${1.5 + Math.random() * 1.5}s ease-in ${Math.random() * 0.5}s forwards;
      `;
      document.body.appendChild(el);
      setTimeout(() => el.remove(), 3500);
    }
  }

  const isLoading = planLoading || balancesLoading;

  // Celebration screen
  if (showCelebration) {
    return (
      <div
        className="fixed inset-0 bg-white z-50 flex flex-col items-center justify-center px-6 text-center"
        role="status"
        aria-live="polite"
      >
        <div className="animate-bounce-in mb-6">
          <div className="w-24 h-24 bg-brand-100 rounded-full flex items-center justify-center mx-auto">
            <svg width="52" height="52" viewBox="0 0 52 52" fill="none" aria-label="All settled checkmark">
              <circle cx="26" cy="26" r="24" fill="#d1fae5"/>
              <path d="M14 26l8 8 16-16" stroke="#047857" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
        </div>
        <h2 className="text-3xl font-bold text-slate-900 mb-2">Everyone is even!</h2>
        <p className="text-base text-slate-500 mb-8 max-w-xs">
          All debts are settled. {plan?.group_name ?? "The group"} is squared away.
        </p>
        <Link
          href={`/groups/${groupId}`}
          className="w-full max-w-xs h-12 bg-brand-700 text-white font-semibold text-base rounded-xl flex items-center justify-center gap-2 hover:bg-brand-800 active:scale-[0.98] transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
        >
          Back to Group
        </Link>
      </div>
    );
  }

  return (
    <div className="h-full">
      {/* Header */}
      <header className="bg-white border-b border-slate-100 sticky top-0 z-40">
        <div className="max-w-lg mx-auto px-4 h-14 flex items-center gap-3">
          <Link
            href={`/groups/${groupId}`}
            className="inline-flex items-center justify-center w-9 h-9 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
            aria-label="Go back to dashboard"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
              <path d="M11.25 4.5L6.75 9l4.5 4.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </Link>
          <h1 className="text-base font-semibold text-slate-800">Settle Up</h1>
        </div>
      </header>

      <main className="max-w-lg mx-auto px-4 pt-5 pb-36 animate-fade-in" aria-label="Settlement plan">

        {/* Net balances */}
        <section className="mb-6" aria-label="Net balances">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">
            Net Balances
          </h2>
          {isLoading ? (
            <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden divide-y divide-slate-100">
              {Array.from({ length: 4 }).map((_, i) => (
                <MemberRowSkeleton key={i} />
              ))}
            </div>
          ) : balances && balances.length > 0 ? (
            <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
              {balances.map((b) => {
                const idx = getMemberIndex(b.member_id);
                const status = getBalanceStatus(b.net_cents);
                const isMe = b.member_id === session?.memberId;
                return (
                  <div
                    key={b.member_id}
                    className="flex items-center gap-3 px-4 py-3.5 border-b border-slate-100 last:border-b-0"
                  >
                    <div
                      className={`w-8 h-8 rounded-full ${getAvatarColor(idx)} font-semibold text-sm flex items-center justify-center flex-shrink-0`}
                      aria-hidden="true"
                    >
                      {getInitials(b.display_name)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-slate-800 truncate">
                        {b.display_name}
                        {isMe ? (
                          <span className="text-xs font-normal text-slate-400 ml-1">(you)</span>
                        ) : null}
                      </p>
                    </div>
                    <div className="text-right">
                      <span
                        className={`text-sm font-bold tabular-nums ${
                          status === "creditor"
                            ? "text-brand-700"
                            : status === "debtor"
                            ? "text-rose-600"
                            : "text-slate-400"
                        }`}
                        aria-label={`${b.display_name} ${
                          status === "creditor"
                            ? "gets back"
                            : status === "debtor"
                            ? "owes"
                            : "is even"
                        } ${b.net_display}`}
                      >
                        {status === "creditor" ? "+" : status === "debtor" ? "−" : ""}
                        {b.net_display}
                      </span>
                      <div
                        className={`text-xs font-medium ${
                          status === "creditor"
                            ? "text-brand-700/70"
                            : status === "debtor"
                            ? "text-rose-500"
                            : "text-slate-400"
                        }`}
                      >
                        {status === "creditor" ? "gets back" : status === "debtor" ? "owes" : "even"}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6 text-center">
              <p className="text-sm text-slate-500">No balances yet.</p>
            </div>
          )}
        </section>

        {/* Payment plan */}
        <section aria-label="Minimum transfer payment plan">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
              Payment Plan
            </h2>
            {plan ? (
              <span className="text-xs text-slate-400 bg-slate-100 px-2 py-1 rounded-full font-medium">
                {settledTransferIds.size} / {plan.transfer_count} settled
              </span>
            ) : null}
          </div>

          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-32 w-full rounded-2xl" />
              ))}
            </div>
          ) : plan?.all_settled || (plan && plan.transfer_count === 0) ? (
            <div className="bg-brand-50 border border-brand-200 rounded-2xl p-6 text-center">
              <div className="w-12 h-12 bg-brand-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M9 12l2 2 4-4" stroke="#047857" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <circle cx="12" cy="12" r="9" stroke="#047857" strokeWidth="2"/>
                </svg>
              </div>
              <p className="text-base font-semibold text-brand-800 mb-1">All settled!</p>
              <p className="text-sm text-brand-700">No outstanding debts in this group.</p>
            </div>
          ) : plan ? (
            <>
              <p className="text-sm text-slate-500 mb-4 font-medium">
                {plan.transfer_count} transfer{plan.transfer_count !== 1 ? "s" : ""} to clear all debts — the minimum possible.
              </p>
              <div className="space-y-3" role="list" aria-label="Payment plan transfers">
                {plan.transfers.map((transfer, i) => {
                  const settled = settledTransferIds.has(i);
                  const isSettling = settling.has(i);
                  const fromIdx = getMemberIndex(transfer.debtor_id);
                  const toIdx = getMemberIndex(transfer.creditor_id);

                  return (
                    <div
                      key={i}
                      className={`rounded-2xl p-5 shadow-sm border transition-all duration-300 ${
                        settled
                          ? "bg-brand-50 border-brand-200"
                          : "bg-white border-slate-200"
                      }`}
                      role="listitem"
                      aria-label={`Transfer ${i + 1}: ${transfer.debtor_name} pays ${transfer.creditor_name} ${transfer.amount_display}`}
                    >
                      <div className="flex items-start gap-3 mb-4">
                        <div className="w-8 h-8 bg-slate-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-base font-bold text-slate-500">{i + 1}</span>
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <div className="flex items-center gap-1.5">
                              <div
                                className={`w-7 h-7 rounded-full ${getAvatarColor(fromIdx)} font-semibold text-xs flex items-center justify-center`}
                                aria-hidden="true"
                              >
                                {getInitials(transfer.debtor_name)}
                              </div>
                              <span className="text-sm font-semibold text-slate-800">
                                {transfer.debtor_name}
                              </span>
                            </div>
                            <span className="text-slate-400 font-medium text-sm">pays</span>
                            <div className="flex items-center gap-1.5">
                              <div
                                className={`w-7 h-7 rounded-full ${getAvatarColor(toIdx)} font-semibold text-xs flex items-center justify-center`}
                                aria-hidden="true"
                              >
                                {getInitials(transfer.creditor_name)}
                              </div>
                              <span className="text-sm font-semibold text-slate-800">
                                {transfer.creditor_name}
                              </span>
                            </div>
                          </div>
                          <p className="text-2xl font-bold text-slate-900 tabular-nums mt-1.5 tracking-tight amount-display">
                            {transfer.amount_display}
                          </p>
                        </div>
                      </div>

                      <button
                        onClick={() => markSettled(i, transfer)}
                        disabled={settled || isSettling}
                        aria-label={
                          settled
                            ? `Transfer ${i + 1} settled`
                            : `Mark transfer ${i + 1} as settled`
                        }
                        className={`w-full h-10 text-sm font-semibold rounded-xl flex items-center justify-center gap-2 transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 active:scale-[0.98] ${
                          settled
                            ? "bg-brand-100 text-brand-800 cursor-default"
                            : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                        } disabled:pointer-events-none`}
                      >
                        {isSettling ? (
                          <svg className="animate-spin" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                            <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" opacity="0.3"/>
                            <path d="M8 2a6 6 0 016 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                          </svg>
                        ) : settled ? (
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                            <circle cx="8" cy="8" r="6.5" fill="#d1fae5" stroke="#10b981" strokeWidth="1.5"/>
                            <path d="M5 8l2 2 4-4" stroke="#047857" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                        ) : (
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                            <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.5"/>
                            <path d="M5 8l2 2 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                        )}
                        {isSettling ? "Saving..." : settled ? "Settled" : "Mark as Settled"}
                      </button>
                    </div>
                  );
                })}
              </div>
            </>
          ) : null}
        </section>
      </main>

      {/* Sticky copy plan bar */}
      {plan && !plan.all_settled && plan.transfer_count > 0 ? (
        <div
          className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 z-40 safe-bottom"
        >
          <div className="max-w-lg mx-auto px-4 py-3">
            <button
              onClick={handleCopyPlan}
              className="w-full h-12 bg-brand-700 text-white font-semibold text-base rounded-xl flex items-center justify-center gap-2 hover:bg-brand-800 active:scale-[0.98] transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
              aria-label="Copy payment plan to clipboard"
            >
              {copyLabel === "Copied!" ? (
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                  <path d="M3 9l4 4 8-8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                  <rect x="1.5" y="4.5" width="10" height="12" rx="1.5" stroke="currentColor" strokeWidth="1.5"/>
                  <path d="M5.5 4.5V3A1.5 1.5 0 017 1.5h9.5A1.5 1.5 0 0118 3v10.5a1.5 1.5 0 01-1.5 1.5H14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
              )}
              {copyLabel}
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
