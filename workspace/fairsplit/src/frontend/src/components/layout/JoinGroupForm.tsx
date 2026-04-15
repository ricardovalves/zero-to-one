"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { joinGroup } from "@/lib/api";
import { storeToken } from "@/lib/session";
import { getAvatarColor, getInitials, ApiError } from "@/types";
import { Button } from "@/components/ui/Button";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface GroupPreview {
  id: string;
  name: string;
  member_count: number;
  expense_count: number;
  members: Array<{ id: string; display_name: string; is_admin: boolean }>;
}

const schema = z.object({
  displayName: z
    .string()
    .min(2, "Name must be at least 2 characters")
    .max(30, "Name must be 30 characters or less"),
});

type FormData = z.infer<typeof schema>;

interface Props {
  inviteToken: string;
}

export function JoinGroupForm({ inviteToken }: Props) {
  const router = useRouter();
  const [group, setGroup] = useState<GroupPreview | null>(null);
  const [loadingGroup, setLoadingGroup] = useState(true);
  const [nameVal, setNameVal] = useState("");

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const watchedName = watch("displayName") ?? "";

  useEffect(() => {
    setNameVal(watchedName);
  }, [watchedName]);

  // Load group preview from invite token
  useEffect(() => {
    fetch(`${API_URL}/api/v1/groups/preview/${inviteToken}`, {
      credentials: "include",
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) setGroup(data as GroupPreview);
      })
      .catch(() => {
        // Preview not critical — form still works
      })
      .finally(() => setLoadingGroup(false));
  }, [inviteToken]);

  async function onSubmit(data: FormData) {
    try {
      const res = await joinGroup(inviteToken, {
        display_name: data.displayName.trim(),
      });

      // Store token in localStorage cache
      storeToken(res.group.id, res.token);

      // Store welcome state
      sessionStorage.setItem("justJoined", "true");
      sessionStorage.setItem("joinedName", data.displayName.trim());

      router.push(`/groups/${res.group.id}`);
    } catch (err) {
      if (err instanceof ApiError) {
        console.error("[JoinGroupForm] API error", err.status, err.message);
        if (err.status === 404) {
          toast.error("This invite link is invalid or has expired.");
        } else if (err.status === 409) {
          toast.error(
            "Someone in this group already has that name. Try a variation."
          );
        } else {
          toast.error(err.message);
        }
      } else {
        console.error("[JoinGroupForm] Unexpected error", err);
        toast.error("Something went wrong. Please try again.");
      }
    }
  }

  const displayedMembers = group?.members?.slice(0, 4) ?? [];
  const extraCount = Math.max(0, (group?.member_count ?? 0) - displayedMembers.length);

  return (
    <>
      {/* Group identity */}
      <div className="text-center mb-8">
        <p className="text-sm text-slate-400 mb-1 font-medium">You&apos;re invited to</p>
        <h1 className="text-3xl font-bold text-slate-900 mb-5">
          {loadingGroup ? (
            <span className="inline-block w-40 h-8 shimmer rounded-lg" aria-hidden="true" />
          ) : (
            group?.name ?? "This group"
          )}
        </h1>

        {/* Member avatars */}
        {displayedMembers.length > 0 ? (
          <div
            className="flex items-center justify-center mb-3"
            aria-label="Current members"
          >
            {displayedMembers.map((m, i) => (
              <div
                key={m.id}
                className={`w-10 h-10 rounded-full ${getAvatarColor(i)} font-semibold text-sm flex items-center justify-center border-2 border-white shadow-sm`}
                style={{ marginLeft: i === 0 ? 0 : "-8px", zIndex: displayedMembers.length - i }}
                title={m.display_name}
                aria-label={m.display_name}
              >
                {getInitials(m.display_name)}
              </div>
            ))}
            {extraCount > 0 ? (
              <div
                className="w-10 h-10 rounded-full bg-slate-100 text-slate-500 font-semibold text-xs flex items-center justify-center border-2 border-white shadow-sm"
                style={{ marginLeft: "-8px" }}
                aria-label={`${extraCount} more member${extraCount > 1 ? "s" : ""}`}
              >
                +{extraCount}
              </div>
            ) : null}
          </div>
        ) : null}

        {group && group.members.length > 0 ? (
          <p className="text-sm text-slate-500">
            <span className="font-medium text-slate-700">
              {displayedMembers.map((m) => m.display_name).join(", ")}
            </span>
            {extraCount > 0 ? ` and ${extraCount} other${extraCount > 1 ? "s are" : " is"} in this group` : " are in this group"}
          </p>
        ) : null}
      </div>

      {/* Group info card */}
      {group ? (
        <div className="bg-white border border-slate-100 rounded-2xl p-5 mb-6 shadow-sm">
          <div className="flex items-center gap-3 mb-3 pb-3 border-b border-slate-100">
            <div className="w-8 h-8 bg-brand-50 rounded-lg flex items-center justify-center flex-shrink-0">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M2 11.5V5.5C2 4.4 2.9 3.5 4 3.5H12C13.1 3.5 14 4.4 14 5.5V9.5C14 10.6 13.1 11.5 12 11.5H5L2 14V11.5Z" stroke="#047857" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div>
              <p className="text-xs text-slate-400 font-medium">Group</p>
              <p className="text-sm font-semibold text-slate-800">{group.name}</p>
            </div>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-500">Members</span>
            <span className="font-semibold text-slate-700">{group.member_count} people</span>
          </div>
          <div className="flex items-center justify-between text-sm mt-1.5">
            <span className="text-slate-500">Expenses logged</span>
            <span className="font-semibold text-slate-700">{group.expense_count} expenses</span>
          </div>
        </div>
      ) : null}

      {/* Name form */}
      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <div className="mb-6">
          <label
            htmlFor="display-name"
            className="block text-sm font-medium text-slate-700 mb-1.5"
          >
            What&apos;s your name?
          </label>
          <input
            id="display-name"
            type="text"
            placeholder="Enter your first name"
            maxLength={30}
            autoComplete="nickname"
            autoFocus
            aria-required="true"
            aria-invalid={!!errors.displayName}
            aria-describedby={
              errors.displayName ? "name-error" : "name-hint"
            }
            className={`w-full h-12 px-4 text-base text-slate-800 bg-white border rounded-xl placeholder-slate-400 transition-all duration-150 field-focus ${
              errors.displayName ? "field-error" : "border-slate-300"
            }`}
            {...register("displayName")}
          />
          {errors.displayName ? (
            <p
              id="name-error"
              className="mt-1 text-xs text-rose-600 flex items-center gap-1"
              role="alert"
              aria-live="polite"
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                <circle cx="6" cy="6" r="5" stroke="#f43f5e" strokeWidth="1.5"/>
                <path d="M6 3.5V6.5M6 8h.01" stroke="#f43f5e" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
              {errors.displayName.message}
            </p>
          ) : (
            <p id="name-hint" className="mt-1.5 text-xs text-brand-700 font-medium flex items-center gap-1">
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                <path d="M9 5.5C9 7.43 7.43 9 5.5 9S2 7.43 2 5.5 3.57 2 5.5 2 9 3.57 9 5.5z" stroke="#047857" strokeWidth="1.2"/>
                <path d="M5.5 5.5v2M5.5 3.5h.01" stroke="#047857" strokeWidth="1.2" strokeLinecap="round"/>
              </svg>
              No account needed. Just your first name.
            </p>
          )}
        </div>

        <Button
          type="submit"
          size="lg"
          loading={isSubmitting}
          disabled={nameVal.trim().length < 2}
          className="w-full"
        >
          {!isSubmitting ? (
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
              <path d="M12 9H6M9 6l3 3-3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              <circle cx="9" cy="9" r="7" stroke="currentColor" strokeWidth="1.5"/>
            </svg>
          ) : null}
          {isSubmitting ? "Joining..." : "Join Group"}
        </Button>
      </form>

      <p className="text-center text-xs text-slate-400 mt-5 leading-relaxed">
        Your display name is only visible to members of this group.
        <br />
        No email or password required.
      </p>
    </>
  );
}
