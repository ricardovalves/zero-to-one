"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import Link from "next/link";
import { toast } from "sonner";
import {
  getCurrentMember,
  getGroup,
  getGroupMembers,
  getExpenses,
  getBalances,
} from "@/lib/api";
import { decodeStoredSession, storeToken } from "@/lib/session";
import { buildInviteUrl, copyToClipboard, formatDate } from "@/lib/utils";
import { getAvatarColor, getBalanceStatus, getInitials, ApiError } from "@/types";
import type { Balance, Expense, Group, Member } from "@/types";
import { DashboardSkeleton } from "@/components/ui/Skeleton";
import { Modal } from "@/components/ui/Modal";
import { Avatar } from "@/components/ui/Avatar";
import { BottomNav } from "@/components/layout/BottomNav";

interface Props {
  groupId: string;
}

export function DashboardClient({ groupId }: Props) {
  const router = useRouter();
  const [session, setSession] = useState(decodeStoredSession(groupId));
  const [sessionLoading, setSessionLoading] = useState(!session);
  const [inviteOpen, setInviteOpen] = useState(false);
  const [copyLabel, setCopyLabel] = useState("Copy");

  // Recover session from cookie if localStorage is empty
  useEffect(() => {
    if (session) return;
    getCurrentMember(groupId)
      .then((member) => {
        // Cookie worked — we have membership
        setSession({
          memberId: member.id,
          groupId: member.group_id,
          isAdmin: member.is_admin,
        });
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) {
          // Genuinely not a member — redirect
          router.replace("/");
        } else {
          console.error("[DashboardClient] Session recovery error", err);
        }
      })
      .finally(() => setSessionLoading(false));
  }, [groupId, session, router]);

  // Show welcome toast on join
  useEffect(() => {
    if (typeof window === "undefined") return;
    const justJoined = sessionStorage.getItem("justJoined");
    const name = sessionStorage.getItem("joinedName");
    if (justJoined && name) {
      setTimeout(() => toast.success(`Welcome, ${name}!`), 300);
      sessionStorage.removeItem("justJoined");
      sessionStorage.removeItem("joinedName");
    }
  }, []);

  // Static data (no polling needed)
  const { data: group, isLoading: groupLoading } = useSWR<Group>(
    session ? `group-${groupId}` : null,
    () => getGroup(groupId),
    { revalidateOnFocus: false }
  );

  const { data: members, isLoading: membersLoading } = useSWR<Member[]>(
    session ? `members-${groupId}` : null,
    () => getGroupMembers(groupId),
    { revalidateOnFocus: false }
  );

  const { data: expenses, isLoading: expensesLoading } = useSWR(
    session ? `expenses-${groupId}` : null,
    () => getExpenses(groupId),
    { revalidateOnFocus: false }
  );

  // Balances — polled every 10 seconds, no loading indicator for background refreshes
  const {
    data: balances,
    isLoading: balancesInitialLoading,
  } = useSWR<Balance[]>(
    session ? `balances-${groupId}` : null,
    () => getBalances(groupId),
    {
      refreshInterval: 10000,
      revalidateOnFocus: true,
      // dedupingInterval keeps background refresh from showing loading state
      dedupingInterval: 2000,
    }
  );

  // Declare expensesInitialLoading BEFORE it is used in isInitialLoading
  const expensesInitialLoading = expensesLoading && !expenses;

  const isInitialLoading =
    sessionLoading ||
    groupLoading ||
    membersLoading ||
    expensesInitialLoading ||
    balancesInitialLoading;

  if (isInitialLoading) {
    return (
      <div className="h-full">
        <header className="bg-white border-b border-slate-100 sticky top-0 z-40">
          <div className="max-w-2xl mx-auto px-4 h-14 flex items-center">
            <div className="shimmer h-5 w-32 rounded-lg" />
          </div>
        </header>
        <DashboardSkeleton />
      </div>
    );
  }

  // Find current member's balance
  const myBalance = balances?.find((b) => b.member_id === session?.memberId);
  const myStatus = myBalance ? getBalanceStatus(myBalance.net_cents) : "even";

  async function handleCopyInvite() {
    if (!group) return;
    const url = buildInviteUrl(group.invite_token);
    const ok = await copyToClipboard(url);
    if (ok) {
      setCopyLabel("Copied!");
      setTimeout(() => setCopyLabel("Copy"), 2000);
    }
  }

  async function handleShareInvite() {
    if (!group) return;
    const url = buildInviteUrl(group.invite_token);
    if (typeof navigator !== "undefined" && navigator.share) {
      try {
        await navigator.share({
          title: `Join ${group.name} on FairSplit`,
          url,
        });
        return;
      } catch {
        // Fall through
      }
    }
    await copyToClipboard(url);
    toast.success("Link copied! Paste it in your group chat.");
    setInviteOpen(false);
  }

  const recentExpenses = expenses?.data?.slice(0, 6) ?? [];

  return (
    <div className="h-full">
      {/* Header */}
      <header className="bg-white border-b border-slate-100 sticky top-0 z-40">
        <div className="max-w-2xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Link
              href="/"
              className="flex items-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded-lg"
            >
              <div className="w-6 h-6 bg-brand-700 rounded-md flex items-center justify-center flex-shrink-0">
                <svg width="12" height="12" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                  <path d="M7 1L9.5 5.5H13L10 8.5L11.5 13L7 10.5L2.5 13L4 8.5L1 5.5H4.5L7 1Z" fill="white"/>
                </svg>
              </div>
            </Link>
            <h1 className="text-base font-semibold text-slate-800 truncate max-w-[200px]">
              {group?.name ?? "Dashboard"}
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setInviteOpen(true)}
              className="inline-flex items-center gap-1.5 h-8 px-3 text-brand-700 text-xs font-semibold bg-brand-50 rounded-lg hover:bg-brand-100 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
              aria-label="Invite members"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <path d="M7 2.5v9M2.5 7h9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
              Invite
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-2xl mx-auto px-4 pt-5 pb-24 animate-fade-in" aria-label="Group dashboard">

        {/* Balance hero card */}
        <section className="bg-white rounded-2xl shadow-md p-6 mb-5" aria-label="Your balance">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">
            Your Balance
          </p>
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-sm text-slate-500 mb-0.5 font-medium">
                {myStatus === "creditor"
                  ? "You are owed"
                  : myStatus === "debtor"
                  ? "You owe"
                  : "You're all even"}
              </p>
              <p
                className={`text-4xl font-bold tabular-nums tracking-tight amount-display ${
                  myStatus === "creditor"
                    ? "text-brand-700"
                    : myStatus === "debtor"
                    ? "text-rose-600"
                    : "text-slate-400"
                }`}
              >
                {myBalance?.net_display ?? "$0.00"}
              </p>
            </div>
            <Link
              href={`/groups/${groupId}/settle-up`}
              className="inline-flex items-center gap-2 h-10 px-5 bg-brand-700 text-white text-sm font-semibold rounded-xl hover:bg-brand-800 active:scale-[0.98] transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 whitespace-nowrap"
              aria-label="View and settle up all debts"
            >
              <svg width="15" height="15" viewBox="0 0 15 15" fill="none" aria-hidden="true">
                <path d="M3 7.5h9M9 4l3 3.5-3 3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Settle Up
            </Link>
          </div>
        </section>

        {/* Member balances */}
        <section className="mb-5" aria-label="Member balances">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-slate-700">Members</h2>
            <button
              onClick={() => setInviteOpen(true)}
              className="text-xs text-brand-700 font-semibold hover:text-brand-800 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-brand-500 rounded"
            >
              + Invite
            </button>
          </div>

          {members && balances ? (
            <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
              {members.map((member, idx) => {
                const balance = balances.find((b) => b.member_id === member.id);
                const bCents = balance?.net_cents ?? 0;
                const status = getBalanceStatus(bCents);
                const isMe = member.id === session?.memberId;

                return (
                  <div
                    key={member.id}
                    className="flex items-center gap-3 px-4 py-3.5 border-b border-slate-100 last:border-b-0"
                    role="row"
                    aria-label={`${member.display_name}${isMe ? " (you)" : ""} — ${balance?.net_display ?? "$0.00"}`}
                  >
                    <Avatar name={member.display_name} index={idx} />
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm truncate ${isMe ? "font-semibold text-slate-800" : "font-medium text-slate-700"}`}>
                        {member.display_name}
                        {isMe ? (
                          <span className="text-xs font-normal text-slate-400 ml-1">
                            (you)
                          </span>
                        ) : null}
                      </p>
                    </div>
                    <span
                      className={`text-sm font-semibold tabular-nums ${
                        status === "creditor"
                          ? "text-brand-700"
                          : status === "debtor"
                          ? "text-rose-600"
                          : "text-slate-400"
                      }`}
                    >
                      {status === "creditor" ? "+" : status === "debtor" ? "−" : ""}
                      {balance?.net_display ?? "$0.00"}
                    </span>
                    <span
                      className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                        status === "creditor"
                          ? "bg-brand-100 text-brand-700"
                          : status === "debtor"
                          ? "bg-rose-100 text-rose-600"
                          : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {status === "creditor"
                        ? "gets back"
                        : status === "debtor"
                        ? "owes"
                        : "even"}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6 text-center">
              <p className="text-sm text-slate-500">No members yet.</p>
            </div>
          )}
        </section>

        {/* Recent expenses */}
        <section aria-label="Recent expenses">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-slate-700">Recent Expenses</h2>
          </div>

          {recentExpenses.length === 0 ? (
            <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-8 text-center">
              <div className="w-12 h-12 bg-brand-50 rounded-2xl flex items-center justify-center mx-auto mb-3">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <rect x="3" y="6" width="18" height="13" rx="2" stroke="#047857" strokeWidth="1.75"/>
                  <path d="M7 6V5a2 2 0 012-2h6a2 2 0 012 2v1" stroke="#047857" strokeWidth="1.75" strokeLinecap="round"/>
                  <path d="M12 11v4M10 13h4" stroke="#047857" strokeWidth="1.75" strokeLinecap="round"/>
                </svg>
              </div>
              <p className="text-sm font-semibold text-slate-700 mb-1">No expenses yet</p>
              <p className="text-xs text-slate-400 mb-4">
                Add your first expense and start tracking!
              </p>
              <Link
                href={`/groups/${groupId}/add-expense`}
                className="inline-flex items-center gap-2 h-9 px-4 bg-brand-700 text-white text-xs font-semibold rounded-xl hover:bg-brand-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
              >
                Add First Expense
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {recentExpenses.map((expense, idx) => (
                <ExpenseRow
                  key={expense.id}
                  expense={expense}
                  groupId={groupId}
                  currentMemberId={session?.memberId}
                  memberIndex={
                    members?.findIndex(
                      (m) => m.id === expense.payer_id
                    ) ?? idx
                  }
                />
              ))}
            </div>
          )}
        </section>
      </main>

      {/* Bottom navigation */}
      <BottomNav groupId={groupId} active="home" />

      {/* Invite modal */}
      <Modal
        open={inviteOpen}
        onClose={() => setInviteOpen(false)}
        title="Invite Members"
      >
        {group ? (
          <>
            <p className="text-sm text-slate-500 mb-4">
              Share this link with anyone you want to add to the group.
            </p>
            <div className="flex items-center gap-2 mb-4">
              <code className="flex-1 text-xs text-slate-600 font-mono bg-slate-50 px-3 py-2.5 rounded-lg border border-slate-200 truncate">
                {buildInviteUrl(group.invite_token)}
              </code>
              <button
                onClick={handleCopyInvite}
                className="h-9 px-3 bg-brand-50 text-brand-700 text-xs font-semibold rounded-lg hover:bg-brand-100 transition-colors whitespace-nowrap focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
                aria-label="Copy invite link"
              >
                {copyLabel}
              </button>
            </div>
            <button
              onClick={handleShareInvite}
              className="w-full h-10 bg-brand-700 text-white text-sm font-semibold rounded-xl flex items-center justify-center gap-2 hover:bg-brand-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M10 2L14 6M14 6L10 10M14 6H6C4.34 6 3 7.34 3 9v3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Share Link
            </button>
          </>
        ) : null}
      </Modal>
    </div>
  );
}

// Sub-component: expense row
function ExpenseRow({
  expense,
  groupId,
  currentMemberId,
  memberIndex,
}: {
  expense: Expense;
  groupId: string;
  currentMemberId?: string;
  memberIndex: number;
}) {
  const myShare = expense.splits?.find(
    (s) => s.member_id === currentMemberId
  );

  return (
    <Link
      href={`/groups/${groupId}/expenses/${expense.id}`}
      className="bg-white rounded-xl border border-slate-100 shadow-sm px-4 py-3.5 flex items-center gap-3 transition-colors hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
      aria-label={`${expense.description}, ${expense.amount_display}`}
    >
      <Avatar
        name={expense.payer_name}
        index={memberIndex}
        size="md"
      />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-slate-800 truncate">
          {expense.description}
        </p>
        <p className="text-xs text-slate-400 mt-0.5">
          {formatDate(expense.expense_date)}
          {expense.payer_id !== currentMemberId
            ? ` · Paid by ${expense.payer_name}`
            : ""}
        </p>
      </div>
      <div className="text-right">
        <p className="text-sm font-semibold text-slate-800 tabular-nums">
          {expense.amount_display}
        </p>
        {myShare ? (
          <p className="text-xs text-slate-400 tabular-nums">
            your share {myShare.amount_display}
          </p>
        ) : null}
      </div>
    </Link>
  );
}
