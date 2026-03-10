import { BrowserRouter, Routes, Route } from "react-router-dom"
import { Layout } from "@/components/layout/Layout"
import { Home } from "@/pages/Home"
import { Login } from "@/pages/Login"
import { Dashboard } from "@/pages/Dashboard"
import { Products } from "@/pages/Products"
import { ProductDetails } from "@/pages/ProductDetails"
import { ProtectedRoute } from "@/components/auth/ProtectedRoute"
import { ProfilePage, OrdersPage, WishlistPage, ReviewsPage, ReturnsPage } from "@/pages/UserPages"

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          {/* We will add more routes later */}
          <Route path="/products" element={<Products />} />
          <Route path="/products/:id" element={<ProductDetails />} />
          <Route path="/deals" element={<Products />} />
          <Route path="/login" element={<Login />} />

          {/* Protected Routes */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/profile" element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          } />
          <Route path="/orders" element={
            <ProtectedRoute>
              <OrdersPage />
            </ProtectedRoute>
          } />
          <Route path="/wishlist" element={
            <ProtectedRoute>
              <WishlistPage />
            </ProtectedRoute>
          } />
          <Route path="/reviews" element={
            <ProtectedRoute>
              <ReviewsPage />
            </ProtectedRoute>
          } />
          <Route path="/returns" element={
            <ProtectedRoute>
              <ReturnsPage />
            </ProtectedRoute>
          } />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
