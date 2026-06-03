import { useEffect, useMemo, useState } from "react"
import { Link, useParams } from "react-router-dom"
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import {
  getProductBySlug,
  getProductFactsheet,
  getProductPerformance,
  type FactsheetResponse,
  type PerformanceResponse,
} from "../api/client"

type FactsheetData = {
  factsheet: FactsheetResponse
  performance: PerformanceResponse
}

function toNumber(value: number | string): number {
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : 0
  }
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

function formatWeight(weight: number | string): string {
  return `${toNumber(weight).toFixed(2)}%`
}

function formatReturn(value: number | string): string {
  return `${(toNumber(value) * 100).toFixed(2)}%`
}

function formatDate(value: string): string {
  return value.slice(0, 10)
}

function DataTable({
  columns,
  rows,
}: {
  columns: [string, string]
  rows: Array<[string, number | string]>
}) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200">
      <table className="w-full border-collapse text-left text-sm">
        <thead className="bg-slate-50 text-slate-600">
          <tr>
            <th className="px-4 py-3 font-medium">{columns[0]}</th>
            <th className="px-4 py-3 text-right font-medium">{columns[1]}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([name, value]) => (
            <tr key={name} className="border-t border-slate-200">
              <td className="px-4 py-3 text-slate-800">{name}</td>
              <td className="px-4 py-3 text-right text-slate-800">{formatWeight(value)}</td>
            </tr>
          ))}
          {rows.length === 0 ? (
            <tr>
              <td className="px-4 py-3 text-slate-600" colSpan={2}>
                No data available.
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  )
}

export function FactsheetPage() {
  const { slug } = useParams()
  const [data, setData] = useState<FactsheetData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadFactsheet = async () => {
      if (!slug) {
        setError("Product slug is missing")
        setLoading(false)
        return
      }

      try {
        setLoading(true)
        const product = await getProductBySlug(slug)
        const [factsheet, performance] = await Promise.all([
          getProductFactsheet(product.id),
          getProductPerformance(product.id),
        ])

        setData({ factsheet, performance })
      } catch (loadError) {
        const message = loadError instanceof Error ? loadError.message : "Failed to load factsheet"
        setError(message)
      } finally {
        setLoading(false)
      }
    }

    void loadFactsheet()
  }, [slug])

  const chartData = useMemo(
    () =>
      (data?.performance.portfolio_growth_chart ?? []).map((point) => ({
        date: point.date,
        value: Number(toNumber(point.value).toFixed(2)),
      })),
    [data],
  )

  return (
    <main className="space-y-6 rounded-xl border border-slate-200 bg-white p-10 shadow-sm">
      <div className="flex items-center justify-between">
        <Link
          to="/"
          className="inline-block rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
        >
          Back to Products
        </Link>
      </div>

      {loading ? <p className="text-slate-600">Loading factsheet...</p> : null}
      {error ? <p className="text-red-600">{error}</p> : null}

      {data ? (
        <>
          <section className="space-y-2">
            <h1 className="text-3xl font-semibold text-slate-900">{data.factsheet.product.name}</h1>
            <p className="max-w-3xl text-slate-600">
              {data.factsheet.product.description ?? "No description available."}
            </p>
            <p className="text-sm text-slate-500">Last Updated: {formatDate(data.factsheet.last_updated)}</p>
          </section>

          <section className="grid grid-cols-4 gap-4">
            <div className="rounded-lg border border-slate-200 p-4">
              <p className="text-sm text-slate-500">Holdings</p>
              <p className="mt-2 text-2xl font-semibold text-slate-900">{data.factsheet.summary.holdings_count}</p>
            </div>
            <div className="rounded-lg border border-slate-200 p-4">
              <p className="text-sm text-slate-500">Largest Holding</p>
              <p className="mt-2 text-lg font-semibold text-slate-900">
                {data.factsheet.summary.largest_holding?.ticker ?? "N/A"}
              </p>
              <p className="text-sm text-slate-600">
                {data.factsheet.summary.largest_holding
                  ? formatWeight(data.factsheet.summary.largest_holding.weight)
                  : "-"}
              </p>
            </div>
            <div className="rounded-lg border border-slate-200 p-4">
              <p className="text-sm text-slate-500">Countries</p>
              <p className="mt-2 text-2xl font-semibold text-slate-900">{data.factsheet.country_exposure.length}</p>
            </div>
            <div className="rounded-lg border border-slate-200 p-4">
              <p className="text-sm text-slate-500">Sectors</p>
              <p className="mt-2 text-2xl font-semibold text-slate-900">{data.factsheet.sector_exposure.length}</p>
            </div>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-slate-900">Top Holdings</h2>
            <div className="overflow-hidden rounded-lg border border-slate-200">
              <table className="w-full border-collapse text-left text-sm">
                <thead className="bg-slate-50 text-slate-600">
                  <tr>
                    <th className="px-4 py-3 font-medium">Ticker</th>
                    <th className="px-4 py-3 font-medium">Company</th>
                    <th className="px-4 py-3 text-right font-medium">Weight</th>
                  </tr>
                </thead>
                <tbody>
                  {data.factsheet.top_holdings.map((holding) => (
                    <tr key={holding.ticker} className="border-t border-slate-200">
                      <td className="px-4 py-3 text-slate-800">{holding.ticker}</td>
                      <td className="px-4 py-3 text-slate-800">{holding.company_name}</td>
                      <td className="px-4 py-3 text-right text-slate-800">{formatWeight(holding.weight)}</td>
                    </tr>
                  ))}
                  {data.factsheet.top_holdings.length === 0 ? (
                    <tr>
                      <td className="px-4 py-3 text-slate-600" colSpan={3}>
                        No holdings available.
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-slate-900">Sector Exposure</h2>
            <DataTable
              columns={["Sector", "Weight"]}
              rows={data.factsheet.sector_exposure.map((entry) => [entry.sector, entry.weight])}
            />
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-slate-900">Country Exposure</h2>
            <DataTable
              columns={["Country", "Weight"]}
              rows={data.factsheet.country_exposure.map((entry) => [entry.country, entry.weight])}
            />
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-slate-900">Market Cap Exposure</h2>
            <DataTable
              columns={["Bucket", "Weight"]}
              rows={data.factsheet.market_cap_exposure.map((entry) => [entry.bucket, entry.weight])}
            />
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-slate-900">Returns</h2>
            <div className="grid grid-cols-3 gap-4">
              <div className="rounded-lg border border-slate-200 p-4">
                <p className="text-sm text-slate-500">1M Return</p>
                <p className="mt-2 text-2xl font-semibold text-slate-900">
                  {formatReturn(data.performance.returns.one_month)}
                </p>
              </div>
              <div className="rounded-lg border border-slate-200 p-4">
                <p className="text-sm text-slate-500">3M Return</p>
                <p className="mt-2 text-2xl font-semibold text-slate-900">
                  {formatReturn(data.performance.returns.three_month)}
                </p>
              </div>
              <div className="rounded-lg border border-slate-200 p-4">
                <p className="text-sm text-slate-500">1Y Return</p>
                <p className="mt-2 text-2xl font-semibold text-slate-900">
                  {formatReturn(data.performance.returns.one_year)}
                </p>
              </div>
            </div>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-slate-900">Performance Chart</h2>
            <div className="h-80 rounded-lg border border-slate-200 p-4">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 12 }} minTickGap={28} />
                  <YAxis tick={{ fill: "#64748b", fontSize: 12 }} width={44} />
                  <Tooltip
                    formatter={(value) => [`${Number(value).toFixed(2)}`, "Portfolio Value"]}
                    labelFormatter={(label) => `Date: ${label}`}
                  />
                  <Line type="monotone" dataKey="value" stroke="#0f172a" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>
        </>
      ) : null}
    </main>
  )
}
