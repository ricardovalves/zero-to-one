import type { Metadata } from "next";
import { SettleUpClient } from "@/components/settle/SettleUpClient";

interface Props {
  params: Promise<{ id: string }>;
}

export const metadata: Metadata = {
  title: "Settle Up",
};

export default async function SettleUpPage({ params }: Props) {
  const { id } = await params;
  return <SettleUpClient groupId={id} />;
}
