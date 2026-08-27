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

export type MarketRow = {
  market: string;
  orders: number;
  sales: number;
  customers: number;
  repeat_rate: number;
  average_transaction_value: number;
  order_share: number;
  previous_orders: number;
  growth_orders: number | null;
  growth_sales: number | null;
  mapping_confidence: number;
  confidence: 'High' | 'Medium' | 'Low';
  eligible_default: boolean;
  monthly_orders: { month: string; orders: number }[];
};

export type MarketView = {
  period: string;
  empty: boolean;
  current_window?: string;
  comparison_window?: string;
  minimum_orders?: number;
  markets: MarketRow[];
  summary?: {
    active_markets: number;
    eligible_markets: number;
    largest_market: string | null;
    largest_market_orders: number;
    fastest_growth_market: string | null;
    fastest_growth_rate: number | null;
    highest_repeat_market: string | null;
    highest_repeat_rate: number | null;
    top_five_concentration: number;
  };
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
  market_views: Record<string, MarketView>;
  location_mapping: {
    raw_labels: number;
    mapped_rows: number;
    unknown_rows: number;
    high_confidence_rows: number;
    review_pending_labels: number;
  };
  scopes: Record<string, Scope>;
  definitions: Record<string, string>;
};

export const analytics = rawAnalytics as AnalyticsData;
