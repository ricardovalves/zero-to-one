"use client";

import { cn } from "@/lib/utils";
import { type InputHTMLAttributes, forwardRef } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, hint, error, className, id, ...props }, ref) => {
    return (
      <div className="w-full">
        {label ? (
          <label
            htmlFor={id}
            className="block text-sm font-medium text-slate-700 mb-1.5"
          >
            {label}
            {props.required ? (
              <span className="text-rose-500 ml-1" aria-hidden="true">
                *
              </span>
            ) : null}
          </label>
        ) : null}
        <input
          ref={ref}
          id={id}
          aria-invalid={!!error}
          aria-describedby={
            [hint ? `${id}-hint` : "", error ? `${id}-error` : ""]
              .filter(Boolean)
              .join(" ") || undefined
          }
          className={cn(
            "w-full h-11 px-4 text-base text-slate-800 bg-white border border-slate-300 rounded-xl",
            "placeholder-slate-400 transition-all duration-150",
            "field-focus",
            error && "field-error",
            className
          )}
          {...props}
        />
        {hint && !error ? (
          <p id={`${id}-hint`} className="mt-1.5 text-xs text-slate-400">
            {hint}
          </p>
        ) : null}
        {error ? (
          <p
            id={`${id}-error`}
            className="mt-1 text-xs text-rose-600 flex items-center gap-1"
            role="alert"
            aria-live="polite"
          >
            <svg
              width="12"
              height="12"
              viewBox="0 0 12 12"
              fill="none"
              aria-hidden="true"
            >
              <circle cx="6" cy="6" r="5" stroke="#f43f5e" strokeWidth="1.5" />
              <path
                d="M6 3.5V6.5M6 8h.01"
                stroke="#f43f5e"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
            {error}
          </p>
        ) : null}
      </div>
    );
  }
);

Input.displayName = "Input";
