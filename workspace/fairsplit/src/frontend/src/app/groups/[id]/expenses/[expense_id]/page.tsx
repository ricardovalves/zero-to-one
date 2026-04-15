import type { Metadata } from "next";
import { ExpenseDetailClient } from "@/components/expense/ExpenseDetailClient";

interface Props {
  params: Promise<{ id: string; expense_id: string }>;
}

export const metadata: Metadata = {
  title: "Expense Detail",
};

export default async function ExpenseDetailPage({ params }: Props) {
  const { id, expense_id } = await params;
  return <ExpenseDetailClient groupId={id} expenseId={expense_id} />;
}
