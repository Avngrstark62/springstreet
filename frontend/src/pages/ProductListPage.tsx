import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { getProducts, type Product } from "../api/client"

export function ProductListPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadProducts = async () => {
      try {
        setLoading(true)
        const result = await getProducts()
        setProducts(result)
      } catch (loadError) {
        const message = loadError instanceof Error ? loadError.message : "Failed to load products"
        setError(message)
      } finally {
        setLoading(false)
      }
    }

    void loadProducts()
  }, [])

  return (
    <main className="rounded-xl border border-slate-200 bg-white p-10 shadow-sm">
      <h1 className="mb-8 text-3xl font-semibold text-slate-900">Product List</h1>

      {loading ? <p className="text-slate-600">Loading products...</p> : null}
      {error ? <p className="text-red-600">{error}</p> : null}

      {!loading && !error ? (
        <div className="space-y-4">
          {products.map((product) => (
            <article key={product.id} className="rounded-lg border border-slate-200 p-6">
              <h2 className="mb-2 text-xl font-semibold text-slate-900">{product.name}</h2>
              <p className="mb-4 text-slate-600">{product.description ?? "No description available."}</p>
              <Link
                to={`/products/${product.slug}`}
                className="inline-block rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700"
              >
                View Factsheet
              </Link>
            </article>
          ))}
          {products.length === 0 ? <p className="text-slate-600">No products found.</p> : null}
        </div>
      ) : null}
    </main>
  )
}
