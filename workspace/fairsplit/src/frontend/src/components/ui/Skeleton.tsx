import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn("shimmer rounded-lg", className)}
      aria-hidden="true"
    />
  );
}

export function BalanceSkeleton() {
  return (
    <div className="bg-white rounded-2xl shadow-md p-6 mb-5">
      <Skeleton className="h-3 w-24 mb-3" />
      <div className="flex items-end justify-between gap-4">
        <div>
          <Skeleton className="h-3 w-20 mb-2" />
          <Skeleton className="h-10 w-32" />
        </div>
        <Skeleton className="h-10 w-28 rounded-xl" />
      </div>
    </div>
  );
}

export function MemberRowSkeleton() {
  return (
    <div className="flex items-center gap-3 px-4 py-3.5">
      <Skeleton className="w-8 h-8 rounded-full" />
      <Skeleton className="flex-1 h-4" />
      <Skeleton className="w-16 h-4" />
      <Skeleton className="w-16 h-5 rounded-full" />
    </div>
  );
}

export function ExpenseRowSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-slate-100 shadow-sm px-4 py-3.5 flex items-center gap-3">
      <Skeleton className="w-8 h-8 rounded-full flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <Skeleton className="h-4 w-3/4 mb-1.5" />
        <Skeleton className="h-3 w-1/2" />
      </div>
      <div className="text-right">
        <Skeleton className="h-4 w-16 mb-1" />
        <Skeleton className="h-3 w-12 ml-auto" />
      </div>
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <main className="max-w-2xl mx-auto px-4 pt-5 pb-24">
      <BalanceSkeleton />
      <section className="mb-5">
        <div className="flex items-center justify-between mb-3">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-16" />
        </div>
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden divide-y divide-slate-100">
          {Array.from({ length: 4 }).map((_, i) => (
            <MemberRowSkeleton key={i} />
          ))}
        </div>
      </section>
      <section>
        <div className="flex items-center justify-between mb-3">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-4 w-12" />
        </div>
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <ExpenseRowSkeleton key={i} />
          ))}
        </div>
      </section>
    </main>
  );
}
