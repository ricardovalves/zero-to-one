import { cn } from "@/lib/utils";
import { getAvatarColor, getInitials } from "@/types";

interface AvatarProps {
  name: string;
  index: number;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeClasses = {
  sm: "w-7 h-7 text-xs",
  md: "w-8 h-8 text-sm",
  lg: "w-10 h-10 text-sm",
};

export function Avatar({ name, index, size = "md", className }: AvatarProps) {
  return (
    <div
      className={cn(
        sizeClasses[size],
        getAvatarColor(index),
        "rounded-full font-semibold flex items-center justify-center flex-shrink-0",
        className
      )}
      aria-hidden="true"
    >
      {getInitials(name)}
    </div>
  );
}
