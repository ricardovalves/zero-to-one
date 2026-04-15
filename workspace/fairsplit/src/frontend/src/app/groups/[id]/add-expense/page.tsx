import type { Metadata } from "next";
import { AddExpenseClient } from "@/components/expense/AddExpenseClient";

interface Props {
  params: Promise<{ id: string }>;
}

export const metadata: Metadata = {
  title: "Add Expense",
};

export default async function AddExpensePage({ params }: Props) {
  const { id } = await params;
  return <AddExpenseClient groupId={id} />;
}
