import { useEffect, useRef, useState } from "react"
import { Navigate, Route, Routes } from 'react-router-dom'
import { triggerSyncData } from "./api/client"
import { FactsheetPage } from './pages/FactsheetPage'
import { ProductListPage } from './pages/ProductListPage'

function App() {
  const [showToast, setShowToast] = useState(false)
  const hideToastTimerRef = useRef<number | null>(null)

  useEffect(() => {
    return () => {
      if (hideToastTimerRef.current !== null) {
        window.clearTimeout(hideToastTimerRef.current)
      }
    }
  }, [])

  const handleSyncData = () => {
    triggerSyncData()
    setShowToast(true)

    if (hideToastTimerRef.current !== null) {
      window.clearTimeout(hideToastTimerRef.current)
    }

    hideToastTimerRef.current = window.setTimeout(() => {
      setShowToast(false)
      hideToastTimerRef.current = null
    }, 6000)
  }

  return (
    <div className="min-h-screen bg-slate-100 px-8 py-10">
      <div className="mx-auto max-w-6xl">
        <Routes>
          <Route path="/" element={<ProductListPage />} />
          <Route path="/products/:slug" element={<FactsheetPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>

      <button
        type="button"
        onClick={handleSyncData}
        className="fixed bottom-6 right-6 rounded-md bg-slate-900 px-4 py-3 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700"
      >
        Sync Data
      </button>

      {showToast ? (
        <div className="fixed bottom-24 right-6 max-w-sm rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-900 shadow-lg">
          ETL pipeline started. Please wait 10 seconds, then refresh the page to access updated data.
        </div>
      ) : null}
    </div>
  )
}

export default App
