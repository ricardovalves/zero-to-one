"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { createGroup } from "@/lib/api";
import { storeToken } from "@/lib/session";
import { buildInviteUrl, copyToClipboard } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ApiError } from "@/types";

const schema = z.object({
  groupName: z
    .string()
    .min(1, "Please enter a group name")
    .max(50, "Group name must be 50 characters or less"),
  displayName: z
    .string()
    .min(2, "Name must be at least 2 characters")
    .max(30, "Name must be 30 characters or less"),
});

type FormData = z.infer<typeof schema>;

export function CreateGroupForm() {
  const router = useRouter();
  const [success, setSuccess] = useState<{
    groupId: string;
    groupName: string;
    inviteToken: string;
  } | null>(null);
  const [copyLabel, setCopyLabel] = useState("Copy");
  const [idempotencyKey] = useState(() => crypto.randomUUID());

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const groupNameVal = watch("groupName") ?? "";

  async function onSubmit(data: FormData) {
    try {
      const res = await createGroup(
        {
          name: data.groupName.trim(),
          admin_display_name: data.displayName.trim(),
          default_currency: "USD",
        },
        idempotencyKey
      );

      // Store token in localStorage
      storeToken(res.group.id, res.token);

      setSuccess({
        groupId: res.group.id,
        groupName: res.group.name,
        inviteToken: res.group.invite_token,
      });
    } catch (err) {
      if (err instanceof ApiError) {
        console.error("[CreateGroupForm] API error", err.status, err.message);
        toast.error(err.message);
      } else {
        console.error("[CreateGroupForm] Unexpected error", err);
        toast.error("Something went wrong. Please try again.");
      }
    }
  }

  async function handleCopyLink(inviteToken: string) {
    const url = buildInviteUrl(inviteToken);
    const ok = await copyToClipboard(url);
    if (ok) {
      setCopyLabel("Copied!");
      setTimeout(() => setCopyLabel("Copy"), 2000);
    }
  }

  async function handleShare(groupName: string, inviteToken: string) {
    const url = buildInviteUrl(inviteToken);
    if (typeof navigator !== "undefined" && navigator.share) {
      try {
        await navigator.share({
          title: `Join ${groupName} on FairSplit`,
          text: "Join our expense group on FairSplit — no account needed!",
          url,
        });
        return;
      } catch {
        // Fall through to copy
      }
    }
    await handleCopyLink(inviteToken);
    toast.success("Link copied! Paste it in your group chat.");
  }

  // ---- SUCCESS STATE ----
  if (success) {
    const inviteUrl = buildInviteUrl(success.inviteToken);
    return (
      <div className="animate-fade-in">
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-brand-100 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse-check">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
              <path d="M7 16l6 6 12-12" stroke="#047857" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h2 className="text-xl font-bold text-slate-800 mb-1">
            {success.groupName} is ready!
          </h2>
          <p className="text-sm text-slate-500">
            Share the link below. Friends can join without an account.
          </p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 mb-4">
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2">
            Your group link
          </label>
          <div className="flex items-center gap-2">
            <code
              className="flex-1 text-sm text-slate-700 font-mono bg-slate-50 px-3 py-2 rounded-lg border border-slate-200 truncate"
              aria-label="Shareable group link"
            >
              {inviteUrl}
            </code>
            <button
              onClick={() => handleCopyLink(success.inviteToken)}
              className="inline-flex items-center justify-center gap-1.5 h-9 px-3 bg-brand-50 text-brand-700 text-xs font-semibold rounded-lg hover:bg-brand-100 active:scale-[0.97] transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 whitespace-nowrap"
              aria-label="Copy group link to clipboard"
            >
              {copyLabel}
            </button>
          </div>
        </div>

        <button
          onClick={() => handleShare(success.groupName, success.inviteToken)}
          className="w-full h-11 bg-white border border-slate-200 text-slate-700 font-semibold text-sm rounded-xl flex items-center justify-center gap-2 hover:bg-slate-50 hover:border-slate-300 active:scale-[0.98] transition-all duration-150 mb-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M10 2L14 6M14 6L10 10M14 6H6C4.34 6 3 7.34 3 9v3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Share Link
        </button>

        <button
          onClick={() => router.push(`/groups/${success.groupId}`)}
          className="w-full h-12 bg-brand-700 text-white font-semibold text-base rounded-xl flex items-center justify-center gap-2 hover:bg-brand-800 active:scale-[0.98] transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
        >
          Go to Dashboard
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M3 8H13M9 4L13 8L9 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </div>
    );
  }

  // ---- FORM STATE ----
  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <div className="mb-5">
        <Input
          id="group-name"
          label="Group Name"
          placeholder="Nashville Trip"
          maxLength={50}
          autoComplete="off"
          required
          error={errors.groupName?.message}
          {...register("groupName")}
        />
        <p className="mt-1 text-xs text-slate-400 text-right">
          <span className={groupNameVal.length > 45 ? "text-amber-600" : ""}>
            {groupNameVal.length}
          </span>{" "}
          / 50
        </p>
      </div>

      <div className="mb-8">
        <Input
          id="display-name"
          label="Your Name"
          placeholder="Maya"
          maxLength={30}
          autoComplete="nickname"
          required
          hint="This is how you'll appear to others. No password needed."
          error={errors.displayName?.message}
          {...register("displayName")}
        />
      </div>

      <Button
        type="submit"
        size="lg"
        loading={isSubmitting}
        className="w-full"
        aria-label="Create group and get shareable link"
      >
        {!isSubmitting ? (
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
            <path d="M9 3.75V14.25M3.75 9H14.25" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        ) : null}
        {isSubmitting ? "Creating..." : "Create Group & Get Link"}
      </Button>
    </form>
  );
}
