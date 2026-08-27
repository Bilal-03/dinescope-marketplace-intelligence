import rawAnalytics from '@/app/data/analytics.json';

export type MonthlyPoint = {
  month: string;
  orders: number;
  sales: number;
  customers: number;
  new_customers: number;
  returning_customers: number;
};

export type Segment = {
  segment: string;
  customers: number;
  customer_share: number;
  orders: number;
  orders_per_customer: number;
  sales: number;
  sales_per_customer: number;
  repeat_rate: number;
  median_recency: number;
  action: string;
};

export type Scope = {
  label: string;
  period: string;
  empty: boolean;
  range?: [string, string];
  metrics?: {
    valid_transactions: number;
    gross_sales: number;
    active_customers: number;
    new_customers: number;
    repeat_customers: number;
    repeat_rate: number;
    orders_per_customer: number;
    average_transaction_value: number;
  };
  monthly?: MonthlyPoint[];
  frequency?: { frequency: string; customers: number }[];
  segments?: Segment[];
  cohorts?: { cohort: string; size: number; retention: number[] }[];
  insight?: { headline: string; evidence: string; action: string; confidence: string };
};

export type AnalyticsData = {
  generated_at: string;
  source: {
    filename: string;
    sha256: string;
    rows: number;
    columns: number;
    date_format: string;
    date_min: string;
    date_max: string;
  };
  quality: {
    raw_rows: number;
    valid_transactions: number;
    excluded_transactions: number;
    valid_rate: number;
    zero_sales: number;
    missing_sales: number;
    unsupported_currency: number;
    rating_coverage: number;
    menu_coverage: number;
    restaurant_match_rate: number;
    duplicate_order_ids: number;
    invalid_dates: number;
  };
  filters: { markets: string[]; periods: string[] };
  market_summary: { market: string; orders: number; sales: number; customers: number; repeat_rate: number }[];
  scopes: Record<string, Scope>;
  definitions: Record<string, string>;
};

export const analytics = rawAnalytics as AnalyticsData;
