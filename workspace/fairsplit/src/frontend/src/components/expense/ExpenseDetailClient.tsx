"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import Link from "next/link";
import { toast } from "sonner";
import { getExpense, updateExpense, deleteExpense, getGroupMembers } from "@/lib/api";
import { decodeStoredSession } from "@/lib/session";
import { formatDate, parseCents, todayISO } from "@/lib/utils";
import { Avatar } from "@/components/ui/Avatar";
import { Modal } from "@/components/ui/Modal";
import { Skeleton } from "@/components/ui/Skeleton";
import { ApiError, type Expense, type Member, type SplitType } from "@/types";

interface Props {
  groupId: string;
  expenseId: string;
}

type SplitMode = "equal" | "custom_amount" | "custom_percentage";

export function ExpenseDetailClient({ groupId, expenseId }: Props) {
  const router = useRouter();
  const session = decodeStoredSession(groupId);

  const [editing, setEditing] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [saving, setSaving] = useState(false);

  // Edit form state — populated when editing starts
  const [editDescription, setEditDescription] = useState("");
  const [editAmountStr, setEditAmountStr] = useState("");
  const [editPaidBy, setEditPaidBy] = useState("");
  const [editDate, setEditDate] = useState("");
  const [editSplitMode, setEditSplitMode] = useState<SplitMode>("equal");
  const [editCustomAmounts, setEditCustomAmounts] = useState<Record<string, string>>({});
  const [editCustomPcts, setEditCustomPcts] = useState<Record<string, string>>({});

  // Validation errors
  const [amountError, setAmountError] = useState("");
  const [descError, setDescError] = useState("");
  const [splitError, setSplitError] = useState("");

  const {
    data: expense,
    isLoading,
    mutate,
  } = useSWR<Expense>(
    `expense-${groupId}-${expenseId}`,
    () => getExpense(groupId, expenseId),
    { revalidateOnFocus: false }
  );

  const { data: members } = useSWR<Member[]>(
    `members-${groupId}`,
    () => getGroupMembers(groupId),
    { revalidateOnFocus: false }
  );

  function startEditing() {
    if (!expense) return;
    setEditDescription(expense.description);
    setEditAmountStr((expense.amount_cents / 100).toFixed(2));
    setEditPaidBy(expense.payer_id);
    setEditDate(expense.expense_date);
    setEditSplitMode(expense.split_type as SplitMode);

    // Pre-fill custom splits
    if (expense.split_type === "custom_amount") {
      const amounts: Record<string, string> = {};
      expense.splits?.forEach((s) => {
        amounts[s.member_id] = (s.amount_cents / 100).toFixed(2);
      });
      setEditCustomAmounts(amounts);
      setEditCustomPcts({});
    } else if (expense.split_type === "custom_percentage") {
      const pcts: Record<string, string> = {};
      expense.splits?.forEach((s) => {
        pcts[s.member_id] = (s.percentage ?? 0).toString();
      });
      setEditCustomPcts(pcts);
      setEditCustomAmounts({});
    } else {
      setEditCustomAmounts({});
      setEditCustomPcts({});
    }
    setAmountError("");
    setDescError("");
    setSplitError("");
    setEditing(true);
  }

  function cancelEditing() {
    setEditing(false);
  }

  // --- Edit amount validation ---
  function handleAmountChange(e: React.ChangeEvent<HTMLInputElement>) {
    let val = e.target.value.replace(/[^0-9.]/g, "");
    const parts = val.split(".");
    if (parts.length > 2) val = (parts[0] ?? "") + "." + parts.slice(1).join("");
    setEditAmountStr(val);
    if (amountError) setAmountError("");
  }

  const editAmountCents = parseCents(editAmountStr);

  function getCustomTotal(): number {
    if (!members) return 0;
    if (editSplitMode === "custom_amount") {
      return members.reduce((sum, m) => sum + parseCents(editCustomAmounts[m.id] ?? "0"), 0);
    }
    if (editSplitMode === "custom_percentage") {
      return members.reduce((sum, m) => sum + parseFloat(editCustomPcts[m.id] ?? "0"), 0);
    }
    return 0;
  }

  const customTotal = getCustomTotal();
  const customTarget = editSplitMode === "custom_percentage" ? 100 : editAmountCents;
  const customRemaining = customTarget - customTotal;

  async function handleSaveEdit() {
    let valid = true;
    if (editAmountCents <= 0) {
      setAmountError("Please enter an amount greater than $0");
      valid = false;
    }
    if (!editDescription.trim()) {
      setDescError("Please describe this expense");
      valid = false;
    }
    if (editSplitMode !== "equal" && Math.abs(customRemaining) > 0.5) {
      setSplitError(
        editSplitMode === "custom_percentage"
          ? `Percentages must add up to 100% (currently ${customTotal.toFixed(1)}%)`
          : "Amounts must add up to the total"
      );
      valid = false;
    }
    if (!valid) return;

    setSaving(true);
    try {
      const splitsPayload =
        editSplitMode === "equal"
          ? undefined
          : members?.map((m) => ({
              member_id: m.id,
              ...(editSplitMode === "custom_amount"
                ? { amount_cents: parseCents(editCustomAmounts[m.id] ?? "0") }
                : { percentage: parseFloat(editCustomPcts[m.id] ?? "0") }),
            }));

      await updateExpense(groupId, expenseId, {
        description: editDescription.trim(),
        amount_cents: editAmountCents,
        payer_member_id: editPaidBy,
        expense_date: editDate,
        split_type: editSplitMode,
        splits: splitsPayload,
      });

      await mutate();
      setEditing(false);
      toast.success("Expense updated!");
    } catch (err) {
      if (err instanceof ApiError) {
        console.error("[ExpenseDetailClient] API error (update)", err.status, err.message);
        toast.error(err.message);
      } else {
        console.error("[ExpenseDetailClient] Unexpected error (update)", err);
        toast.error("Something went wrong. Please try again.");
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await deleteExpense(groupId, expenseId, crypto.randomUUID());
      toast.success("Expense deleted.");
      router.push(`/groups/${groupId}`);
    } catch (err) {
      if (err instanceof ApiError) {
        console.error("[ExpenseDetailClient] API error (delete)", err.status, err.message);
        toast.error(err.message);
      } else {
        console.error("[ExpenseDetailClient] Unexpected error (delete)", err);
        toast.error("Could not delete expense. Please try again.");
      }
      setDeleting(false);
      setDeleteOpen(false);
    }
  }

  const isAdmin = session?.isAdmin ?? false;
  const isPaidByMe = expense?.payer_id === session?.memberId;
  const canEdit = isAdmin || isPaidByMe;

  if (isLoading) {
    return (
      <div className="h-full">
        <header className="bg-white border-b border-slate-100 sticky top-0 z-40">
          <div className="max-w-lg mx-auto px-4 h-14 flex items-center gap-3">
            <div className="w-9 h-9 shimmer rounded-xl" />
            <div className="shimmer h-5 w-36 rounded-lg" />
          </div>
        </header>
        <main className="max-w-lg mx-auto px-4 pt-6 pb-24 space-y-4 animate-fade-in">
          <Skeleton className="h-32 w-full rounded-2xl" />
          <Skeleton className="h-48 w-full rounded-2xl" />
          <Skeleton className="h-24 w-full rounded-2xl" />
        </main>
      </div>
    );
  }

  if (!expense) {
    return (
      <div className="h-full flex flex-col">
        <header className="bg-white border-b border-slate-100 sticky top-0 z-40">
          <div className="max-w-lg mx-auto px-4 h-14 flex items-center gap-3">
            <Link
              href={`/groups/${groupId}`}
              className="inline-flex items-center justify-center w-9 h-9 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
              aria-label="Back to dashboard"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                <path d="M11.25 4.5L6.75 9l4.5 4.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </Link>
            <h1 className="text-base font-semibold text-slate-800">Expense Detail</h1>
          </div>
        </header>
        <main className="max-w-lg mx-auto px-4 pt-12 text-center">
          <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
              <path d="M16 10v8M16 22h.01" stroke="#94a3b8" strokeWidth="2.5" strokeLinecap="round"/>
              <circle cx="16" cy="16" r="13" stroke="#94a3b8" strokeWidth="2"/>
            </svg>
          </div>
          <p className="text-base font-semibold text-slate-700 mb-1">Expense not found</p>
          <p className="text-sm text-slate-400 mb-6">This expense may have been deleted.</p>
          <Link
            href={`/groups/${groupId}`}
            className="inline-flex items-center gap-2 h-10 px-5 bg-brand-700 text-white text-sm font-semibold rounded-xl hover:bg-brand-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
          >
            Back to Dashboard
          </Link>
        </main>
      </div>
    );
  }

  const splitAmountCents =
    members && members.length > 0 && editAmountCents > 0
      ? Math.floor(editAmountCents / members.length)
      : 0;

  return (
    <div className="h-full">
      {/* Header */}
      <header className="bg-white border-b border-slate-100 sticky top-0 z-40">
        <div className="max-w-lg mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Link
              href={`/groups/${groupId}`}
              className="inline-flex items-center justify-center w-9 h-9 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
              aria-label="Back to dashboard"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                <path d="M11.25 4.5L6.75 9l4.5 4.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </Link>
            <h1 className="text-base font-semibold text-slate-800">
              {editing ? "Edit Expense" : "Expense Detail"}
            </h1>
          </div>

          {canEdit && !editing ? (
            <div className="flex items-center gap-2">
              <button
                onClick={startEditing}
                className="inline-flex items-center gap-1.5 h-8 px-3 text-brand-700 text-xs font-semibold bg-brand-50 rounded-lg hover:bg-brand-100 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
                aria-label="Edit this expense"
              >
                <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                  <path d="M9.5 1.5L11.5 3.5L4.5 10.5H2.5V8.5L9.5 1.5Z" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                Edit
              </button>
              <button
                onClick={() => setDeleteOpen(true)}
                className="inline-flex items-center gap-1.5 h-8 px-3 text-rose-600 text-xs font-semibold bg-rose-50 rounded-lg hover:bg-rose-100 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-400"
                aria-label="Delete this expense"
              >
                <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                  <path d="M2 3.5h9M5 3.5V2.5a1 1 0 011-1h1a1 1 0 011 1v1M3 3.5l.5 7h6l.5-7" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                Delete
              </button>
            </div>
          ) : editing ? (
            <button
              onClick={cancelEditing}
              className="text-sm text-slate-500 font-medium hover:text-slate-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded-lg px-2 py-1"
            >
              Cancel
            </button>
          ) : null}
        </div>
      </header>

      <main className="max-w-lg mx-auto px-4 pt-5 pb-28 animate-fade-in">

        {editing ? (
          /* ---- EDIT FORM ---- */
          <div className="space-y-5">
            {/* Amount */}
            <div>
              <label
                htmlFor="edit-amount"
                className="block text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2"
              >
                Amount
              </label>
              <div
                className={`flex items-center gap-0 bg-white border rounded-2xl px-5 py-4 transition-all duration-150 focus-within:border-brand-700 focus-within:ring-2 focus-within:ring-brand-500/25 ${
                  amountError ? "border-rose-400" : "border-slate-200"
                }`}
              >
                <span className="text-3xl font-bold text-slate-400 mr-2 select-none" aria-hidden="true">$</span>
                <input
                  id="edit-amount"
                  type="text"
                  inputMode="decimal"
                  placeholder="0.00"
                  maxLength={10}
                  autoComplete="off"
                  value={editAmountStr}
                  onChange={handleAmountChange}
                  aria-label="Expense amount"
                  aria-invalid={!!amountError}
                  aria-describedby={amountError ? "edit-amount-error" : undefined}
                  className="flex-1 bg-transparent text-slate-800 placeholder-slate-300 min-w-0 focus:outline-none text-3xl font-bold amount-display"
                />
              </div>
              {amountError ? (
                <p id="edit-amount-error" className="mt-1.5 text-xs text-rose-600 flex items-center gap-1" role="alert" aria-live="polite">
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                    <circle cx="6" cy="6" r="5" stroke="#f43f5e" strokeWidth="1.5"/>
                    <path d="M6 3.5V6.5M6 8h.01" stroke="#f43f5e" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                  {amountError}
                </p>
              ) : null}
            </div>

            {/* Description */}
            <div>
              <label htmlFor="edit-description" className="block text-sm font-medium text-slate-700 mb-1.5">
                Description <span className="text-rose-500" aria-hidden="true">*</span>
              </label>
              <input
                id="edit-description"
                type="text"
                placeholder="What was this for?"
                maxLength={80}
                autoComplete="off"
                value={editDescription}
                onChange={(e) => { setEditDescription(e.target.value); if (descError) setDescError(""); }}
                aria-invalid={!!descError}
                aria-describedby={descError ? "edit-desc-error" : undefined}
                className={`w-full h-11 px-4 text-base text-slate-800 bg-white border rounded-xl placeholder-slate-400 transition-all duration-150 field-focus ${
                  descError ? "field-error" : "border-slate-300"
                }`}
              />
              {descError ? (
                <p id="edit-desc-error" className="mt-1 text-xs text-rose-600 flex items-center gap-1" role="alert" aria-live="polite">
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                    <circle cx="6" cy="6" r="5" stroke="#f43f5e" strokeWidth="1.5"/>
                    <path d="M6 3.5V6.5M6 8h.01" stroke="#f43f5e" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                  {descError}
                </p>
              ) : null}
            </div>

            {/* Date */}
            <div>
              <label htmlFor="edit-date" className="block text-sm font-medium text-slate-700 mb-1.5">
                Date
              </label>
              <input
                id="edit-date"
                type="date"
                value={editDate}
                onChange={(e) => setEditDate(e.target.value)}
                className="w-full h-11 px-4 text-base text-slate-800 bg-white border border-slate-300 rounded-xl field-focus transition-all duration-150"
              />
            </div>

            {/* Who paid */}
            <div>
              <label htmlFor="edit-paid-by" className="block text-sm font-medium text-slate-700 mb-1.5">
                Who paid?
              </label>
              <select
                id="edit-paid-by"
                value={editPaidBy}
                onChange={(e) => setEditPaidBy(e.target.value)}
                className="w-full h-11 px-4 text-base text-slate-800 bg-white border border-slate-300 rounded-xl field-focus transition-all duration-150 cursor-pointer appearance-none"
                style={{
                  backgroundImage: `url("data:image/svg+xml,%3Csvg width='16' height='16' viewBox='0 0 16 16' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M4 6l4 4 4-4' stroke='%2394a3b8' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E")`,
                  backgroundRepeat: "no-repeat",
                  backgroundPosition: "right 14px center",
                }}
              >
                {members?.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.display_name}{m.id === session?.memberId ? " (you)" : ""}
                  </option>
                ))}
              </select>
            </div>

            {/* Split mode */}
            <div>
              <p className="block text-sm font-medium text-slate-700 mb-2" id="edit-split-label">
                Split between
              </p>
              <div className="space-y-2" role="radiogroup" aria-labelledby="edit-split-label">
                {(
                  [
                    { value: "equal", label: "Split equally", desc: "Everyone pays the same share" },
                    { value: "custom_amount", label: "Custom amounts", desc: "Enter a specific dollar amount per person" },
                    { value: "custom_percentage", label: "Custom percentages", desc: "Enter a percentage of the total per person" },
                  ] as const
                ).map((opt) => {
                  const active = editSplitMode === opt.value;
                  return (
                    <label
                      key={opt.value}
                      className={`flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer transition-all duration-150 border-2 ${
                        active ? "bg-brand-50 border-brand-700 text-brand-900" : "bg-white border-slate-200 hover:bg-slate-50"
                      }`}
                    >
                      <input
                        type="radio"
                        name="edit-split-mode"
                        value={opt.value}
                        checked={active}
                        onChange={() => { setEditSplitMode(opt.value); setSplitError(""); }}
                        className="sr-only"
                      />
                      <span
                        className={`w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                          active ? "bg-brand-700 border-brand-700" : "border-slate-300"
                        }`}
                        aria-hidden="true"
                      >
                        {active ? <span className="w-1.5 h-1.5 rounded-full bg-white" /> : null}
                      </span>
                      <div>
                        <p className={`text-sm font-semibold ${active ? "text-brand-900" : "text-slate-700"}`}>{opt.label}</p>
                        <p className={`text-xs ${active ? "text-brand-700/70" : "text-slate-400"}`}>{opt.desc}</p>
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* Equal split preview */}
            {editSplitMode === "equal" && editAmountCents > 0 && members && members.length > 0 ? (
              <div className="animate-fade-in">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2">Split preview</p>
                <div className="bg-white border border-slate-100 rounded-xl overflow-hidden shadow-sm">
                  {members.map((m, i) => (
                    <div key={m.id} className="flex items-center gap-3 px-4 py-2.5 border-b border-slate-100 last:border-b-0">
                      <Avatar name={m.display_name} index={i} size="sm" />
                      <span className="flex-1 text-sm text-slate-700">{m.display_name}{m.id === session?.memberId ? " (you)" : ""}</span>
                      <span className="text-sm font-semibold text-slate-800 tabular-nums">
                        ${(splitAmountCents / 100).toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            {/* Custom splits */}
            {(editSplitMode === "custom_amount" || editSplitMode === "custom_percentage") && members ? (
              <div>
                <div className="bg-white border border-slate-200 rounded-xl overflow-hidden divide-y divide-slate-100">
                  {members.map((m, i) => {
                    const val =
                      editSplitMode === "custom_amount"
                        ? editCustomAmounts[m.id] ?? ""
                        : editCustomPcts[m.id] ?? "";
                    return (
                      <div key={m.id} className="flex items-center gap-3 px-4 py-3">
                        <Avatar name={m.display_name} index={i} size="sm" />
                        <span className="flex-1 text-sm text-slate-700 truncate">
                          {m.display_name}{m.id === session?.memberId ? " (you)" : ""}
                        </span>
                        <div className="flex items-center gap-1 w-28">
                          {editSplitMode === "custom_amount" ? <span className="text-sm text-slate-400 font-medium">$</span> : null}
                          <input
                            type="text"
                            inputMode="decimal"
                            placeholder={editSplitMode === "custom_percentage" ? "0" : "0.00"}
                            value={val}
                            onChange={(e) => {
                              setSplitError("");
                              if (editSplitMode === "custom_amount") {
                                setEditCustomAmounts((prev) => ({ ...prev, [m.id]: e.target.value }));
                              } else {
                                setEditCustomPcts((prev) => ({ ...prev, [m.id]: e.target.value }));
                              }
                            }}
                            aria-label={`${m.display_name} ${editSplitMode === "custom_percentage" ? "percentage" : "amount"}`}
                            className="w-full h-9 px-2 text-sm text-right font-semibold tabular-nums text-slate-800 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-brand-700 focus:ring-1 focus:ring-brand-500/25 transition-all"
                          />
                          {editSplitMode === "custom_percentage" ? <span className="text-sm text-slate-400 font-medium">%</span> : null}
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="px-4 py-3 bg-slate-50 rounded-b-xl flex items-center justify-between border border-t-0 border-slate-200">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Remaining</span>
                  <span className={`text-sm font-semibold tabular-nums ${Math.abs(customRemaining) < 0.5 ? "text-brand-700" : "text-rose-600"}`}>
                    {editSplitMode === "custom_percentage"
                      ? `${Math.abs(customRemaining).toFixed(1)}%`
                      : `$${(Math.abs(customRemaining) / 100).toFixed(2)}`}
                  </span>
                </div>
                {splitError ? (
                  <p className="mt-2 text-xs text-rose-600" role="alert" aria-live="polite">{splitError}</p>
                ) : null}
              </div>
            ) : null}
          </div>
        ) : (
          /* ---- READ-ONLY VIEW ---- */
          <div className="space-y-4">
            {/* Hero card */}
            <div className="bg-white rounded-2xl shadow-md p-6">
              <div className="flex items-start gap-4">
                <div
                  className="w-12 h-12 rounded-2xl bg-brand-50 flex items-center justify-center flex-shrink-0"
                  aria-hidden="true"
                >
                  <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
                    <rect x="2" y="5" width="18" height="14" rx="2" stroke="#047857" strokeWidth="1.75"/>
                    <path d="M6 5V4a2 2 0 012-2h6a2 2 0 012 2v1" stroke="#047857" strokeWidth="1.75" strokeLinecap="round"/>
                    <path d="M8 11h6M11 8v6" stroke="#047857" strokeWidth="1.75" strokeLinecap="round"/>
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-0.5">
                    {formatDate(expense.expense_date)}
                  </p>
                  <h2 className="text-lg font-bold text-slate-900 mb-1 leading-snug">
                    {expense.description}
                  </h2>
                  <p className="text-xs text-slate-500">
                    Paid by{" "}
                    <span className="font-semibold text-slate-700">
                      {expense.payer_name}
                      {expense.payer_id === session?.memberId ? " (you)" : ""}
                    </span>
                  </p>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="text-2xl font-bold text-slate-900 tabular-nums tracking-tight amount-display">
                    {expense.amount_display}
                  </p>
                  <p className="text-xs text-slate-400 capitalize mt-0.5">
                    {expense.split_type.replace(/_/g, " ")}
                  </p>
                </div>
              </div>
            </div>

            {/* Split breakdown */}
            {expense.splits && expense.splits.length > 0 ? (
              <section aria-label="How this expense is split">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">
                  Split breakdown
                </h3>
                <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
                  {expense.splits.map((split, idx) => {
                    const memberIdx = members?.findIndex((m) => m.id === split.member_id) ?? idx;
                    const isMe = split.member_id === session?.memberId;
                    return (
                      <div
                        key={split.member_id}
                        className={`flex items-center gap-3 px-4 py-3.5 border-b border-slate-100 last:border-b-0 ${
                          isMe ? "bg-brand-50/40" : ""
                        }`}
                      >
                        <Avatar name={split.member_display_name} index={memberIdx} size="sm" />
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm truncate ${isMe ? "font-semibold text-slate-800" : "font-medium text-slate-700"}`}>
                            {split.member_display_name}
                            {isMe ? (
                              <span className="text-xs font-normal text-slate-400 ml-1">(you)</span>
                            ) : null}
                          </p>
                          {split.percentage != null ? (
                            <p className="text-xs text-slate-400 mt-0.5">
                              {split.percentage.toFixed(1)}% of total
                            </p>
                          ) : null}
                        </div>
                        <span className="text-sm font-semibold text-slate-800 tabular-nums">
                          {split.amount_display}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </section>
            ) : null}

            {/* Metadata */}
            <section aria-label="Expense metadata" className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
              <div className="px-4 py-3.5 flex items-center justify-between border-b border-slate-100">
                <span className="text-sm text-slate-500">Expense ID</span>
                <code className="text-xs text-slate-400 font-mono truncate max-w-[180px]">{expense.id}</code>
              </div>
              <div className="px-4 py-3.5 flex items-center justify-between border-b border-slate-100">
                <span className="text-sm text-slate-500">Created</span>
                <span className="text-sm text-slate-700 font-medium">
                  {new Date(expense.created_at).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </span>
              </div>
              <div className="px-4 py-3.5 flex items-center justify-between">
                <span className="text-sm text-slate-500">Split type</span>
                <span className="text-sm text-slate-700 font-medium capitalize">
                  {expense.split_type.replace(/_/g, " ")}
                </span>
              </div>
            </section>

            {/* Non-admin notice */}
            {!canEdit ? (
              <p className="text-xs text-slate-400 text-center">
                Only the group admin or the person who paid can edit or delete this expense.
              </p>
            ) : null}
          </div>
        )}
      </main>

      {/* Sticky save button when editing */}
      {editing ? (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 px-4 py-3 z-40 safe-bottom">
          <div className="max-w-lg mx-auto">
            <button
              onClick={handleSaveEdit}
              disabled={saving}
              aria-busy={saving}
              className="w-full h-12 bg-brand-700 text-white font-semibold text-base rounded-xl flex items-center justify-center gap-2 hover:bg-brand-800 active:scale-[0.98] transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 disabled:opacity-40 disabled:pointer-events-none"
              aria-label="Save expense changes"
            >
              {saving ? (
                <svg className="animate-spin" width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                  <circle cx="9" cy="9" r="7" stroke="rgba(255,255,255,0.3)" strokeWidth="2"/>
                  <path d="M9 2a7 7 0 017 7" stroke="white" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                  <path d="M3 9l4 4 8-8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              )}
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </div>
      ) : null}

      {/* Delete confirmation modal */}
      <Modal
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        title="Delete Expense"
      >
        <p className="text-sm text-slate-600 mb-5">
          Are you sure you want to delete{" "}
          <strong className="text-slate-800">{expense.description}</strong>?{" "}
          This will update all balances. This action cannot be undone.
        </p>
        <div className="flex gap-3">
          <button
            onClick={() => setDeleteOpen(false)}
            disabled={deleting}
            className="flex-1 h-11 bg-white border border-slate-200 text-slate-700 text-sm font-semibold rounded-xl hover:bg-slate-50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 disabled:opacity-40 disabled:pointer-events-none"
          >
            Cancel
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting}
            aria-busy={deleting}
            className="flex-1 h-11 bg-rose-600 text-white text-sm font-semibold rounded-xl hover:bg-rose-700 active:scale-[0.98] transition-all duration-150 flex items-center justify-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-400 focus-visible:ring-offset-2 disabled:opacity-40 disabled:pointer-events-none"
          >
            {deleting ? (
              <svg className="animate-spin" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <circle cx="8" cy="8" r="6" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5"/>
                <path d="M8 2a6 6 0 016 6" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            ) : null}
            {deleting ? "Deleting..." : "Delete Expense"}
          </button>
        </div>
      </Modal>
    </div>
  );
}
