import type { Metadata } from "next";
import { DashboardClient } from "@/components/dashboard/DashboardClient";

interface Props {
  params: Promise<{ id: string }>;
}

export const metadata: Metadata = {
  title: "Group Dashboard",
};

export default async function GroupDashboardPage({ params }: Props) {
  // In Next.js 16, params must be awaited
  const { id } = await params;
  return <DashboardClient groupId={id} />;
}
