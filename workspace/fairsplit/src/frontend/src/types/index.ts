// ============================================================
// FairSplit — TypeScript types derived from api-spec.yaml
// DO NOT add .data wrappers on singletons — see api-spec.yaml
// ============================================================

// ---- Enums ----

export type SplitType = "equal" | "custom_amount" | "custom_percentage";
export type Currency = "USD" | "EUR" | "GBP" | "CAD" | "AUD";
export type GroupStatus = "active" | "archived";
export type MemberRole = "admin" | "member";

// ---- Balance colour convention ----
// Green (brand-700) = creditor (balance_cents > 0 = owed money)
// Rose             = debtor   (balance_cents < 0 = owes money)
// Slate            = even     (balance_cents === 0)

// ---- Core entities ----

export interface Group {
  id: string;
  name: string;
  description?: string | null;
  invite_token: string;
  status: GroupStatus;
  default_currency: Currency;
  member_count: number;
  expense_count: number;
  created_at: string;
  updated_at: string;
}

export interface Member {
  id: string;
  group_id: string;
  display_name: string;
  is_admin: boolean;
  joined_at: string;
}

export interface ExpenseSplit {
  member_id: string;
  member_display_name: string;
  amount_cents: number;
  amount_display: string;
  percentage?: number | null;
}

export interface Expense {
  id: string;
  group_id: string;
  payer_id: string;
  payer_name: string;
  amount_cents: number;
  amount_display: string;
  description: string;
  expense_date: string;
  split_type: SplitType;
  split_count: number;
  splits?: ExpenseSplit[];
  created_at: string;
}

export interface Balance {
  member_id: string;
  display_name: string;
  net_cents: number;
  net_display: string;
  paid_total_cents: number;
  owed_total_cents: number;
  settled_out_cents: number;
  settled_in_cents: number;
  status: "creditor" | "debtor" | "settled";
}

export interface BalancesResponse {
  currency: string;
  members: Balance[];
  computed_at: string;
}

export interface Transfer {
  debtor_id: string;
  debtor_name: string;
  creditor_id: string;
  creditor_name: string;
  amount_cents: number;
  amount_display: string;
  currency: string;
}

export interface SettleUpPlan {
  group_name: string;
  currency: Currency;
  all_settled: boolean;
  transfer_count: number;
  transfers: Transfer[];
  clipboard_text: string;
  computed_at: string;
}

export interface Settlement {
  id: string;
  group_id: string;
  payer_id: string;
  payer_name: string;
  payee_id: string;
  payee_name: string;
  amount_cents: number;
  amount_display: string;
  currency: string;
  created_at: string;
}

// ---- API response envelopes ----

/** Collections return {data: T[], total, page, per_page} */
export interface ListResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
}

/** Join/create return {group, member, token} at top level */
export interface CreateGroupResponse {
  group: Group;
  member: Member;
  token: string;
}

export interface JoinGroupResponse {
  group: Group;
  member: Member;
  token: string;
}

// ---- API request bodies ----

export interface CreateGroupRequest {
  name: string;
  description?: string;
  admin_display_name: string;
  default_currency?: Currency;
}

export interface JoinGroupRequest {
  display_name: string;
}

export interface CreateExpenseRequest {
  description: string;
  amount_cents: number;
  payer_member_id: string;
  expense_date: string;
  split_type: SplitType;
  splits: Array<{
    member_id: string;
    amount_cents?: number;
    percentage?: number;
  }>;
}

export interface UpdateExpenseRequest {
  description?: string;
  amount_cents?: number;
  payer_member_id?: string;
  expense_date?: string;
  split_type?: SplitType;
  splits?: Array<{
    member_id: string;
    amount_cents?: number;
    percentage?: number;
  }>;
}

export interface CreateSettlementRequest {
  payer_member_id: string;
  payee_member_id: string;
  amount_cents: number;
  currency: string;
}

// ---- API error ----

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    field?: string;
    request_id?: string;
  };
}

export class ApiError extends Error {
  status: number;
  code: string;
  field?: string;

  constructor(status: number, body: ApiErrorBody) {
    super(body.error.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.error.code;
    this.field = body.error.field;
  }
}

// ---- Session ----

export interface SessionPayload {
  sub: string; // member_id
  group_id: string;
  is_admin: boolean;
  iat: number;
  exp: number;
}

export interface CurrentSession {
  memberId: string;
  groupId: string;
  isAdmin: boolean;
}

// ---- Dev panel ----

export interface DevGroupEntry {
  groupId: string;
  groupName: string;
  inviteToken: string;
  adminName: string;
  memberName: string;
}

// ---- UI helpers ----

export type BalanceStatus = "creditor" | "debtor" | "even";

export function getBalanceStatus(netCents: number): BalanceStatus {
  if (netCents > 0) return "creditor";
  if (netCents < 0) return "debtor";
  return "even";
}

/** Avatar colour palette — consistent across all member rows */
export const AVATAR_COLORS = [
  "bg-emerald-100 text-emerald-800",
  "bg-blue-100 text-blue-800",
  "bg-amber-100 text-amber-800",
  "bg-pink-100 text-pink-800",
  "bg-violet-100 text-violet-800",
  "bg-sky-100 text-sky-800",
  "bg-orange-100 text-orange-800",
  "bg-rose-100 text-rose-800",
  "bg-teal-100 text-teal-800",
  "bg-indigo-100 text-indigo-800",
] as const;

export function getAvatarColor(index: number): string {
  return AVATAR_COLORS[index % AVATAR_COLORS.length] ?? AVATAR_COLORS[0];
}

export function getInitials(name: string | undefined | null): string {
  return (name ?? "?").trim().charAt(0).toUpperCase();
}
