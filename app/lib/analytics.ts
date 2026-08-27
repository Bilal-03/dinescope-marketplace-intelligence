import rawAnalytics from '@/app/data/analytics.json';

export const AGGREGATE_VERSION = '1.1.0';

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

export type CuisinePair = {
  market: string;
  cuisine: string;
  allocated_orders: number;
  allocated_sales: number;
  customers: number;
  observed_listings: number;
  demand_share: number;
  listing_share: number;
  demand_to_listing_index: number | null;
  previous_allocated_orders: number;
  growth: number | null;
  rating_coverage: number;
  menu_coverage: number;
  confidence: 'High' | 'Medium' | 'Low';
  eligible_default: boolean;
  opportunity_score: number;
  recommended_action: string;
};

export type CuisineSummary = {
  cuisine: string;
  allocated_orders: number;
  allocated_sales: number;
  customers: number;
  markets: number;
  observed_listings: number;
};

export type CuisineView = {
  period: string;
  empty: boolean;
  current_window?: string;
  comparison_window?: string;
  minimum_allocated_orders?: number;
  allocated_order_total?: number;
  covered_order_count?: number;
  cuisines: CuisineSummary[];
  pairs: CuisinePair[];
  summary?: {
    active_cuisines: number;
    eligible_pairs: number;
    top_cuisine: string | null;
    top_cuisine_orders: number;
    top_opportunity_market: string | null;
    top_opportunity_cuisine: string | null;
    top_opportunity_score: number | null;
  };
};

export type AnalyticsData = {
  aggregate_version: string;
  generated_at: string;
  source: {
    filename: string;
    bytes: number;
    sha256: string;
    rows: number;
    columns: number;
    expected_columns: number;
    schema_matches: boolean;
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
    missing_rating_rows: number;
    missing_menu_attribute_rows: number;
    rating_coverage: number;
    menu_coverage: number;
    restaurant_match_rate: number;
    duplicate_order_ids: number;
    invalid_dates: number;
  };
  filters: { markets: string[]; periods: string[] };
  market_summary: { market: string; orders: number; sales: number; customers: number; repeat_rate: number }[];
  market_views: Record<string, MarketView>;
  cuisine_views: Record<string, CuisineView>;
  cuisine_mapping: {
    raw_tokens: number;
    canonical_cuisines: number;
    excluded_token_rows: number;
    cuisine_coverage: number;
  };
  restaurant_mapping: {
    raw_names: number;
    normalized_names: number;
    repeat_normalized_names: number;
    restaurant_ids: number;
    restaurant_ids_repeated: number;
  };
  restaurant_observations: {
    normalized_name: string;
    observed_rows: number;
    distinct_restaurant_ids: number;
    markets: number;
    rating_coverage: number;
    menu_coverage: number;
  }[];
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

export function analyticsContractErrors(data: AnalyticsData): string[] {
  const errors: string[] = [];
  if (data.aggregate_version !== AGGREGATE_VERSION) {
    errors.push(`aggregate_version must be ${AGGREGATE_VERSION}`);
  }
  if (!data.source.schema_matches || data.source.columns !== data.source.expected_columns) {
    errors.push('source schema does not match the expected column contract');
  }
  if (data.source.rows !== data.quality.raw_rows) {
    errors.push('source rows must equal quality raw rows');
  }
  if (data.quality.valid_transactions + data.quality.excluded_transactions !== data.quality.raw_rows) {
    errors.push('valid plus excluded transactions must equal raw rows');
  }
  if (data.quality.missing_rating_rows !== Math.round(data.quality.raw_rows * (1 - data.quality.rating_coverage))) {
    errors.push('missing rating rows must reconcile to raw rating coverage');
  }
  if (data.quality.missing_menu_attribute_rows !== Math.round(data.quality.raw_rows * (1 - data.quality.menu_coverage))) {
    errors.push('missing menu rows must reconcile to raw menu coverage');
  }
  return errors;
}

const contractErrors = analyticsContractErrors(analytics);
if (contractErrors.length > 0) {
  throw new Error(`Invalid DineScope aggregate contract: ${contractErrors.join('; ')}`);
}
