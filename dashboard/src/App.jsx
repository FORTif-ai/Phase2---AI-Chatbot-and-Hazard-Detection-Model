import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Memories from './pages/Memories'
import MemoryDetail from './pages/MemoryDetail'
import NewMemory from './pages/NewMemory'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="memories" element={<Memories />} />
        <Route path="memories/new" element={<NewMemory />} />
        <Route path="memories/:uuid" element={<MemoryDetail />} />
      </Route>
    </Routes>
  )
}

export default App
