import { Navigate, Route, Routes } from 'react-router-dom'
import { FactsheetPage } from './pages/FactsheetPage'
import { ProductListPage } from './pages/ProductListPage'

function App() {
  return (
    <div className="min-h-screen bg-slate-100 px-8 py-10">
      <div className="mx-auto max-w-6xl">
        <Routes>
          <Route path="/" element={<ProductListPage />} />
          <Route path="/products/:slug" element={<FactsheetPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </div>
  )
}

export default App
