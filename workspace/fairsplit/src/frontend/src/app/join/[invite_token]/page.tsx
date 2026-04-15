import type { Metadata } from "next";
import { Logo } from "@/components/ui/Logo";
import { JoinGroupForm } from "@/components/layout/JoinGroupForm";

interface Props {
  params: Promise<{ invite_token: string }>;
}

export const metadata: Metadata = {
  title: "Join Group",
};

export default async function JoinGroupPage({ params }: Props) {
  // In Next.js 16, params must be awaited
  const { invite_token } = await params;

  return (
    <div className="h-full">
      <header className="bg-white border-b border-slate-100">
        <div className="max-w-lg mx-auto px-4 h-14 flex items-center">
          <Logo />
        </div>
      </header>

      <main className="max-w-lg mx-auto px-4 py-10 animate-fade-in">
        <JoinGroupForm inviteToken={invite_token} />
      </main>
    </div>
  );
}
