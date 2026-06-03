const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export type Product = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

type LargestHolding = {
  ticker: string;
  weight: number;
};

type FactsheetSummary = {
  holdings_count: number;
  largest_holding: LargestHolding | null;
};

type TopHolding = {
  ticker: string;
  company_name: string;
  weight: number;
};

type SectorExposure = {
  sector: string;
  weight: number;
};

type CountryExposure = {
  country: string;
  weight: number;
};

type MarketCapExposure = {
  bucket: string;
  weight: number;
};

export type FactsheetResponse = {
  product: Product;
  summary: FactsheetSummary;
  top_holdings: TopHolding[];
  sector_exposure: SectorExposure[];
  country_exposure: CountryExposure[];
  market_cap_exposure: MarketCapExposure[];
  last_updated: string;
};

type PerformanceReturns = {
  one_month: number;
  three_month: number;
  one_year: number;
};

type PortfolioGrowthPoint = {
  date: string;
  value: number;
};

export type PerformanceResponse = {
  product: Product;
  returns: PerformanceReturns;
  portfolio_growth_chart: PortfolioGrowthPoint[];
  last_updated: string;
};

type ApiErrorResponse = {
  detail?: string;
};

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = (await response.json()) as ApiErrorResponse;
      if (body.detail) {
        detail = body.detail;
      }
    } catch {
      // Ignore JSON parsing errors and use fallback message.
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export async function getProducts(): Promise<Product[]> {
  return request<Product[]>("/products");
}

export async function getProductBySlug(slug: string): Promise<Product> {
  return request<Product>(`/products/slug/${slug}`);
}

export async function getProductFactsheet(productId: string): Promise<FactsheetResponse> {
  return request<FactsheetResponse>(`/products/${productId}/factsheet`);
}

export async function getProductPerformance(productId: string): Promise<PerformanceResponse> {
  return request<PerformanceResponse>(`/products/${productId}/performance`);
}

export function triggerSyncData(): void {
  void fetch(`${API_BASE_URL}/sync-data`, { method: "GET" }).catch(() => {
    // Intentionally ignore failures; sync trigger should not block UI behavior.
  });
}
