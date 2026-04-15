import { cn } from "@/lib/utils";

interface LogoProps {
  className?: string;
  size?: "sm" | "md";
}

export function Logo({ className, size = "md" }: LogoProps) {
  const iconSize = size === "sm" ? "w-6 h-6" : "w-7 h-7";
  const iconInner = size === "sm" ? 12 : 14;

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div
        className={cn(
          iconSize,
          "bg-brand-700 rounded-lg flex items-center justify-center flex-shrink-0"
        )}
      >
        <svg
          width={iconInner}
          height={iconInner}
          viewBox="0 0 14 14"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M7 1L9.5 5.5H13L10 8.5L11.5 13L7 10.5L2.5 13L4 8.5L1 5.5H4.5L7 1Z"
            fill="white"
          />
        </svg>
      </div>
      <span className="text-slate-900 font-semibold text-base">FairSplit</span>
    </div>
  );
}
