"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import useSWR from "swr";
import { createExpense, getGroupMembers } from "@/lib/api";
import {
  clearDraft,
  decodeStoredSession,
  loadDraft,
  saveDraft,
} from "@/lib/session";
import { formatCents, parseCents, todayISO } from "@/lib/utils";
import { ApiError, type Member, type SplitType } from "@/types";
import { Avatar } from "@/components/ui/Avatar";
import Link from "next/link";

interface Props {
  groupId: string;
}

type SplitMode = "equal" | "custom_amount" | "custom_percentage";

export function AddExpenseClient({ groupId }: Props) {
  const router = useRouter();
  const session = decodeStoredSession(groupId);

  // Generate idempotency key on mount; regenerate on success
  const [idempotencyKey, setIdempotencyKey] = useState(() => crypto.randomUUID());

  // Form state
  const [amountStr, setAmountStr] = useState("");
  const [description, setDescription] = useState("");
  const [paidByMemberId, setPaidByMemberId] = useState(session?.memberId ?? "");
  const [date, setDate] = useState(todayISO());
  const [splitMode, setSplitMode] = useState<SplitMode>("equal");
  const [customAmounts, setCustomAmounts] = useState<Record<string, string>>({});
  const [customPcts, setCustomPcts] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  // Error state
  const [amountError, setAmountError] = useState("");
  const [descError, setDescError] = useState("");
  const [splitError, setSplitError] = useState("");

  // Members
  const { data: members } = useSWR<Member[]>(
    `members-${groupId}`,
    () => getGroupMembers(groupId),
    { revalidateOnFocus: false }
  );

  const amountCents = parseCents(amountStr);

  // --- Draft persistence ---
  useEffect(() => {
    const draft = loadDraft(groupId);
    if (!draft) return;
    if (draft.amount) setAmountStr(draft.amount);
    if (draft.description) setDescription(draft.description);
    if (draft.paidByMemberId) setPaidByMemberId(draft.paidByMemberId);
    if (draft.splitType) setSplitMode(draft.splitType as SplitMode);
    if (draft.date) setDate(draft.date);
    if (draft.customSplits) {
      if (draft.splitType === "custom_amount") setCustomAmounts(draft.customSplits);
      if (draft.splitType === "custom_percentage") setCustomPcts(draft.customSplits);
    }
  }, [groupId]);

  useEffect(() => {
    function saveDraftOnUnload() {
      if (!amountStr && !description) return;
      saveDraft(groupId, {
        description,
        amount: amountStr,
        paidByMemberId,
        splitType: splitMode,
        date,
        customSplits:
          splitMode === "custom_amount"
            ? customAmounts
            : splitMode === "custom_percentage"
            ? customPcts
            : undefined,
      });
    }
    window.addEventListener("beforeunload", saveDraftOnUnload);
    return () => window.removeEventListener("beforeunload", saveDraftOnUnload);
  }, [groupId, amountStr, description, paidByMemberId, splitMode, date, customAmounts, customPcts]);

  // Set paid-by to current member once members load
  useEffect(() => {
    if (!paidByMemberId && session?.memberId && members) {
      const meInGroup = members.find((m) => m.id === session.memberId);
      if (meInGroup) setPaidByMemberId(meInGroup.id);
    }
  }, [members, session, paidByMemberId]);

  // --- Amount input validation ---
  function handleAmountChange(e: React.ChangeEvent<HTMLInputElement>) {
    let val = e.target.value.replace(/[^0-9.]/g, "");
    // Prevent multiple decimal points
    const parts = val.split(".");
    if (parts.length > 2) val = (parts[0] ?? "") + "." + parts.slice(1).join("");
    setAmountStr(val);
    if (amountError) setAmountError("");
  }

  // --- Split preview (equal mode) ---
  const splitAmountCents =
    members && members.length > 0 && amountCents > 0
      ? Math.floor(amountCents / members.length)
      : 0;

  // --- Custom split validation ---
  function getCustomTotal(): number {
    if (!members) return 0;
    if (splitMode === "custom_amount") {
      return members.reduce((sum, m) => sum + parseCents(customAmounts[m.id] ?? "0"), 0);
    }
    if (splitMode === "custom_percentage") {
      return members.reduce((sum, m) => sum + parseFloat(customPcts[m.id] ?? "0"), 0);
    }
    return 0;
  }

  const customTotal = getCustomTotal();
  const customTarget = splitMode === "custom_percentage" ? 100 : amountCents;
  const customRemaining = customTarget - customTotal;

  // --- Submit ---
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    let valid = true;

    if (amountCents <= 0) {
      setAmountError("Please enter an amount greater than $0");
      valid = false;
    }
    if (!description.trim()) {
      setDescError("Please describe this expense");
      valid = false;
    }
    if (splitMode !== "equal" && Math.abs(customRemaining) > 0.5) {
      setSplitError(
        splitMode === "custom_percentage"
          ? `Percentages must add up to 100% (currently ${customTotal.toFixed(1)}%)`
          : "Amounts must add up to the total"
      );
      valid = false;
    }
    if (!valid) return;

    setSubmitting(true);
    try {
      const splitsPayload =
        splitMode === "equal"
          ? undefined
          : members?.map((m) => ({
              member_id: m.id,
              ...(splitMode === "custom_amount"
                ? { amount_cents: parseCents(customAmounts[m.id] ?? "0") }
                : { percentage: parseFloat(customPcts[m.id] ?? "0") }),
            }));

      await createExpense(
        groupId,
        {
          description: description.trim(),
          amount_cents: amountCents,
          payer_member_id: paidByMemberId,
          expense_date: date,
          split_type: splitMode,
          splits: splitsPayload ?? members?.map((m) => ({ member_id: m.id })) ?? [],
        },
        idempotencyKey
      );

      clearDraft(groupId);
      setIdempotencyKey(crypto.randomUUID());
      toast.success("Expense added!");
      router.push(`/groups/${groupId}`);
    } catch (err) {
      if (err instanceof ApiError) {
        console.error("[AddExpenseClient] API error", err.status, err.message);
        toast.error(err.message);
      } else {
        console.error("[AddExpenseClient] Unexpected error", err);
        toast.error("Something went wrong. Please try again.");
      }
      setSubmitting(false);
    }
  }

  return (
    <div className="h-full">
      {/* Header */}
      <header className="bg-white border-b border-slate-100 sticky top-0 z-40">
        <div className="max-w-lg mx-auto px-4 h-14 flex items-center justify-between">
          <Link
            href={`/groups/${groupId}`}
            className="inline-flex items-center gap-1.5 text-sm text-slate-600 font-medium hover:text-slate-900 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded-lg px-1 py-1"
            aria-label="Cancel and go back to dashboard"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
              <path d="M11.25 4.5L6.75 9l4.5 4.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Cancel
          </Link>
          <h1 className="text-base font-semibold text-slate-800">Add Expense</h1>
          <div className="w-16" />
        </div>
      </header>

      <main className="max-w-lg mx-auto px-4 pt-6 pb-28 animate-fade-in">
        <form id="expense-form" onSubmit={handleSubmit} noValidate>

          {/* Amount — hero field */}
          <div className="mb-6">
            <label
              htmlFor="amount-input"
              className="block text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2"
            >
              Amount
            </label>
            <div
              className={`flex items-center gap-0 bg-white border rounded-2xl px-5 py-4 transition-all duration-150 focus-within:border-brand-700 focus-within:ring-2 focus-within:ring-brand-500/25 ${
                amountError ? "border-rose-400" : "border-slate-200"
              }`}
            >
              <span className="text-3xl font-bold text-slate-400 mr-2 select-none" aria-hidden="true">
                $
              </span>
              <input
                id="amount-input"
                type="text"
                inputMode="decimal"
                placeholder="0.00"
                maxLength={10}
                autoComplete="off"
                value={amountStr}
                onChange={handleAmountChange}
                aria-label="Expense amount in dollars"
                aria-required="true"
                aria-invalid={!!amountError}
                aria-describedby={amountError ? "amount-error" : undefined}
                className="flex-1 bg-transparent text-slate-800 placeholder-slate-300 min-w-0 focus:outline-none text-3xl font-bold amount-display"
                style={{ fontSize: "2rem", fontWeight: 700, letterSpacing: "-0.02em" }}
              />
            </div>
            {amountError ? (
              <p
                id="amount-error"
                className="mt-1.5 text-xs text-rose-600 flex items-center gap-1"
                role="alert"
                aria-live="polite"
              >
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                  <circle cx="6" cy="6" r="5" stroke="#f43f5e" strokeWidth="1.5"/>
                  <path d="M6 3.5V6.5M6 8h.01" stroke="#f43f5e" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
                {amountError}
              </p>
            ) : null}
          </div>

          {/* Description */}
          <div className="mb-5">
            <label htmlFor="description" className="block text-sm font-medium text-slate-700 mb-1.5">
              Description{" "}
              <span className="text-rose-500" aria-hidden="true">*</span>
            </label>
            <input
              id="description"
              type="text"
              placeholder="What was this for?"
              maxLength={80}
              autoComplete="off"
              required
              value={description}
              onChange={(e) => {
                setDescription(e.target.value);
                if (descError) setDescError("");
              }}
              aria-required="true"
              aria-invalid={!!descError}
              aria-describedby={descError ? "description-error" : undefined}
              className={`w-full h-11 px-4 text-base text-slate-800 bg-white border rounded-xl placeholder-slate-400 transition-all duration-150 field-focus ${
                descError ? "field-error" : "border-slate-300"
              }`}
            />
            {descError ? (
              <p
                id="description-error"
                className="mt-1 text-xs text-rose-600 flex items-center gap-1"
                role="alert"
                aria-live="polite"
              >
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                  <circle cx="6" cy="6" r="5" stroke="#f43f5e" strokeWidth="1.5"/>
                  <path d="M6 3.5V6.5M6 8h.01" stroke="#f43f5e" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
                {descError}
              </p>
            ) : null}
          </div>

          {/* Date */}
          <div className="mb-5">
            <label htmlFor="expense-date" className="block text-sm font-medium text-slate-700 mb-1.5">
              Date
            </label>
            <input
              id="expense-date"
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full h-11 px-4 text-base text-slate-800 bg-white border border-slate-300 rounded-xl field-focus transition-all duration-150"
            />
          </div>

          {/* Who paid */}
          <div className="mb-5">
            <label htmlFor="paid-by" className="block text-sm font-medium text-slate-700 mb-1.5">
              Who paid?
            </label>
            <select
              id="paid-by"
              value={paidByMemberId}
              onChange={(e) => setPaidByMemberId(e.target.value)}
              className="w-full h-11 px-4 text-base text-slate-800 bg-white border border-slate-300 rounded-xl field-focus transition-all duration-150 cursor-pointer appearance-none"
              aria-label="Select who paid"
              style={{
                backgroundImage: `url("data:image/svg+xml,%3Csvg width='16' height='16' viewBox='0 0 16 16' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M4 6l4 4 4-4' stroke='%2394a3b8' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E")`,
                backgroundRepeat: "no-repeat",
                backgroundPosition: "right 14px center",
              }}
            >
              {members?.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.display_name}
                  {m.id === session?.memberId ? " (you)" : ""}
                </option>
              ))}
            </select>
          </div>

          {/* Split mode */}
          <div className="mb-5">
            <p className="block text-sm font-medium text-slate-700 mb-2" id="split-label">
              Split between
            </p>
            <div className="space-y-2" role="radiogroup" aria-labelledby="split-label">
              {(
                [
                  {
                    value: "equal",
                    label: "Split equally",
                    desc: "Everyone pays the same share",
                  },
                  {
                    value: "custom_amount",
                    label: "Custom amounts",
                    desc: "Enter a specific dollar amount per person",
                  },
                  {
                    value: "custom_percentage",
                    label: "Custom percentages",
                    desc: "Enter a percentage of the total per person",
                  },
                ] as const
              ).map((opt) => {
                const active = splitMode === opt.value;
                return (
                  <label
                    key={opt.value}
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer transition-all duration-150 border-2 ${
                      active
                        ? "bg-brand-50 border-brand-700 text-brand-900"
                        : "bg-white border-slate-200 hover:bg-slate-50"
                    }`}
                  >
                    <input
                      type="radio"
                      name="split-mode"
                      value={opt.value}
                      checked={active}
                      onChange={() => setSplitMode(opt.value)}
                      className="sr-only"
                    />
                    {/* Custom radio dot */}
                    <span
                      className={`w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                        active
                          ? "bg-brand-700 border-brand-700"
                          : "border-slate-300"
                      }`}
                      aria-hidden="true"
                    >
                      {active ? (
                        <span className="w-1.5 h-1.5 rounded-full bg-white" />
                      ) : null}
                    </span>
                    <div>
                      <p className={`text-sm font-semibold ${active ? "text-brand-900" : "text-slate-700"}`}>
                        {opt.label}
                      </p>
                      <p className={`text-xs ${active ? "text-brand-700/70" : "text-slate-400"}`}>
                        {opt.desc}
                      </p>
                    </div>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Equal split preview */}
          {splitMode === "equal" && amountCents > 0 && members && members.length > 0 ? (
            <div className="mb-5 animate-fade-in">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2">
                Split preview
              </p>
              <div className="bg-white border border-slate-100 rounded-xl overflow-hidden shadow-sm">
                {members.map((m, i) => (
                  <div
                    key={m.id}
                    className="flex items-center gap-3 px-4 py-2.5 border-b border-slate-100 last:border-b-0"
                  >
                    <Avatar name={m.display_name} index={i} size="sm" />
                    <span className="flex-1 text-sm text-slate-700">
                      {m.display_name}
                      {m.id === session?.memberId ? " (you)" : ""}
                    </span>
                    <span className="text-sm font-semibold text-slate-800 tabular-nums">
                      {formatCents(splitAmountCents)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {/* Custom split inputs */}
          {(splitMode === "custom_amount" || splitMode === "custom_percentage") && members ? (
            <div className="mb-5">
              <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
                <div className="divide-y divide-slate-100">
                  {members.map((m, i) => {
                    const val =
                      splitMode === "custom_amount"
                        ? customAmounts[m.id] ?? ""
                        : customPcts[m.id] ?? "";
                    return (
                      <div key={m.id} className="flex items-center gap-3 px-4 py-3">
                        <Avatar name={m.display_name} index={i} size="sm" />
                        <span className="flex-1 text-sm text-slate-700 truncate">
                          {m.display_name}
                          {m.id === session?.memberId ? " (you)" : ""}
                        </span>
                        <div className="flex items-center gap-1 w-28">
                          {splitMode === "custom_amount" ? (
                            <span className="text-sm text-slate-400 font-medium">$</span>
                          ) : null}
                          <input
                            type="text"
                            inputMode="decimal"
                            placeholder={
                              splitMode === "custom_percentage"
                                ? "0"
                                : amountCents > 0 && members.length > 0
                                ? (amountCents / 100 / members.length).toFixed(2)
                                : "0.00"
                            }
                            value={val}
                            onChange={(e) => {
                              setSplitError("");
                              if (splitMode === "custom_amount") {
                                setCustomAmounts((prev) => ({
                                  ...prev,
                                  [m.id]: e.target.value,
                                }));
                              } else {
                                setCustomPcts((prev) => ({
                                  ...prev,
                                  [m.id]: e.target.value,
                                }));
                              }
                            }}
                            aria-label={`${m.display_name} ${splitMode === "custom_percentage" ? "percentage" : "amount"}`}
                            className="w-full h-9 px-2 text-sm text-right font-semibold tabular-nums text-slate-800 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-brand-700 focus:ring-1 focus:ring-brand-500/25 transition-all"
                          />
                          {splitMode === "custom_percentage" ? (
                            <span className="text-sm text-slate-400 font-medium">%</span>
                          ) : null}
                        </div>
                      </div>
                    );
                  })}
                </div>
                {/* Remaining */}
                <div className="px-4 py-3 bg-slate-50 flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Remaining
                  </span>
                  <span
                    className={`text-sm font-semibold tabular-nums ${
                      Math.abs(customRemaining) < 0.5
                        ? "text-brand-700"
                        : customRemaining < 0
                        ? "text-rose-600"
                        : "text-brand-700"
                    }`}
                  >
                    {splitMode === "custom_percentage"
                      ? `${Math.abs(customRemaining).toFixed(1)}%`
                      : formatCents(Math.abs(Math.round(customRemaining)))}
                  </span>
                </div>
                {splitError ? (
                  <p
                    className="px-4 pb-3 text-xs text-rose-600"
                    role="alert"
                    aria-live="polite"
                  >
                    {splitError}
                  </p>
                ) : null}
              </div>
            </div>
          ) : null}
        </form>
      </main>

      {/* Sticky CTA */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 px-4 py-3 z-40 safe-bottom">
        <div className="max-w-lg mx-auto">
          <button
            type="submit"
            form="expense-form"
            disabled={submitting}
            aria-busy={submitting}
            className="w-full h-12 bg-brand-700 text-white font-semibold text-base rounded-xl flex items-center justify-center gap-2 hover:bg-brand-800 active:scale-[0.98] transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 disabled:opacity-40 disabled:pointer-events-none"
            aria-label="Save this expense"
          >
            {submitting ? (
              <svg className="animate-spin" width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                <circle cx="9" cy="9" r="7" stroke="rgba(255,255,255,0.3)" strokeWidth="2"/>
                <path d="M9 2a7 7 0 017 7" stroke="white" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                <path d="M3 9l4 4 8-8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            )}
            {submitting ? "Saving..." : "Add Expense"}
          </button>
        </div>
      </div>
    </div>
  );
}
