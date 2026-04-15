import Link from "next/link";
import { cn } from "@/lib/utils";

interface Props {
  groupId: string;
  active: "home" | "add" | "settle" | "group";
}

export function BottomNav({ groupId, active }: Props) {
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 z-40 safe-bottom"
      aria-label="Main navigation"
    >
      <div className="max-w-2xl mx-auto h-16 flex items-center">
        {/* Home */}
        <Link
          href={`/groups/${groupId}`}
          className={cn(
            "flex-1 flex flex-col items-center justify-center gap-0.5 h-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-inset",
            active === "home" ? "text-brand-700" : "text-slate-400 hover:text-slate-600"
          )}
          aria-current={active === "home" ? "page" : undefined}
          aria-label="Dashboard"
        >
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
            <path
              d="M3 9.5L11 3l8 6.5V19a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z"
              stroke="currentColor"
              strokeWidth="1.75"
              fill={active === "home" ? "#ecfdf5" : "none"}
              strokeLinejoin="round"
            />
          </svg>
          <span className={cn("text-[10px]", active === "home" ? "font-semibold" : "font-medium")}>
            Home
          </span>
        </Link>

        {/* Add Expense */}
        <Link
          href={`/groups/${groupId}/add-expense`}
          className="flex-1 flex flex-col items-center justify-center gap-0.5 h-full text-slate-400 hover:text-slate-600 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-inset"
          aria-label="Add a new expense"
        >
          <div className="w-10 h-10 bg-brand-700 rounded-xl flex items-center justify-center shadow-md">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <path d="M10 4v12M4 10h12" stroke="white" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
        </Link>

        {/* Settle Up */}
        <Link
          href={`/groups/${groupId}/settle-up`}
          className={cn(
            "flex-1 flex flex-col items-center justify-center gap-0.5 h-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-inset",
            active === "settle" ? "text-brand-700" : "text-slate-400 hover:text-slate-600"
          )}
          aria-current={active === "settle" ? "page" : undefined}
          aria-label="Settle up"
        >
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
            <path
              d="M3 11h16M14 7l5 4-5 4"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span className={cn("text-[10px]", active === "settle" ? "font-semibold" : "font-medium")}>
            Settle
          </span>
        </Link>

        {/* Group */}
        <div
          className="flex-1 flex flex-col items-center justify-center gap-0.5 h-full text-slate-400"
          aria-label="Group settings (coming soon)"
        >
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
            <circle cx="8.5" cy="7" r="3" stroke="currentColor" strokeWidth="1.75"/>
            <path d="M2 19c0-3.59 2.91-6.5 6.5-6.5" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"/>
            <circle cx="16" cy="8.5" r="2.5" stroke="currentColor" strokeWidth="1.75"/>
            <path d="M13 19c0-2.76 1.79-5 4-5h.5" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"/>
          </svg>
          <span className="text-[10px] font-medium">Group</span>
        </div>
      </div>
    </nav>
  );
}
