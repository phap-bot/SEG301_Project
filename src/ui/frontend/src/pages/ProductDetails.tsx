import { useState, useEffect } from "react"
import { useParams } from "react-router-dom"
import { ExternalLink, Heart, Tag, AlertCircle, ImageOff } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { PLATFORM_MAP, DEFAULT_PLATFORM } from "@/lib/platforms"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from "recharts"

const ProductImage = ({ src, alt, className }: { src?: string; alt: string; className?: string }) => {
    const [error, setError] = useState(false)
    if (!src || error) {
        return (
            <div className="flex flex-col items-center justify-center w-full h-full text-zinc-400 bg-zinc-50 rounded-xl">
                <ImageOff className="w-12 h-12 mb-2 opacity-30" />
                <span className="text-sm uppercase tracking-wider font-semibold opacity-50">No image available</span>
            </div>
        )
    }
    return <img src={src} alt={alt} className={className} onError={() => setError(true)} loading="lazy" />
}

interface Product {
    id: number
    platform: string
    product_id: string
    product_name: string
    price: number
    original_price?: number
    discount_percent?: number
    product_url: string
    image_url?: string
}

const generateMockPriceHistory = (basePrice: number) => {
    const data = []
    let currentPrice = basePrice + (basePrice * 0.15) // Start higher
    const today = new Date()

    for (let i = 30; i >= 0; i--) {
        const d = new Date()
        d.setDate(today.getDate() - i)

        if (i % 7 === 0) {
            currentPrice = currentPrice - (currentPrice * 0.05)
        }
        if (i === 2) currentPrice = basePrice // Drop to reality recently

        data.push({
            date: d.toLocaleDateString("vi-VN", { month: "short", day: "numeric" }),
            price: Math.max(Math.round(currentPrice), basePrice - 100000)
        })
    }
    return data
}

export function ProductDetails() {
    const { id } = useParams()
    const [product, setProduct] = useState<Product | null>(null)
    const [loading, setLoading] = useState(true)
    const [priceHistory, setPriceHistory] = useState<any[]>([])
    const [isTracked, setIsTracked] = useState(false)
    const [platformVouchers, setPlatformVouchers] = useState<any[]>([])

    useEffect(() => {
        const fetchTrackingStatus = async () => {
            if (!product) return
            const userId = localStorage.getItem("user_id")
            if (userId) {
                try {
                    const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/user/${userId}/tracking`)
                    if (res.ok) {
                        const data = await res.json()
                        const tr = data.tracked_products || []
                        const vo = data.saved_vouchers || []
                        setIsTracked(tr.some((p: Product) => p.id === product.id))
                        setPlatformVouchers(vo.filter((v: any) => v.platform === product.platform))
                        return
                    }
                } catch (err) {}
            }
            
            // Fallback
            const savedTracked = JSON.parse(localStorage.getItem("tracked_products") || "[]")
            setIsTracked(savedTracked.some((p: Product) => p.id === product.id))
            
            const savedVo = JSON.parse(localStorage.getItem("saved_vouchers") || "[]")
            const matching = savedVo.filter((v: any) => v.platform === product.platform)
            setPlatformVouchers(matching)
        }
        fetchTrackingStatus()
    }, [product])

    const toggleTrack = async () => {
        if (!product) return
        
        let saved = JSON.parse(localStorage.getItem("tracked_products") || "[]")
        const userId = localStorage.getItem("user_id")
        
        if (isTracked) {
            saved = saved.filter((p: Product) => p.id !== product.id)
            setIsTracked(false)
            if (userId) {
                fetch(`${import.meta.env.VITE_API_URL}/api/v1/user/${userId}/tracked_products/${product.id}`, { method: "DELETE" }).catch(() => {})
            }
        } else {
            saved.push(product)
            setIsTracked(true)
            if (userId) {
                fetch(`${import.meta.env.VITE_API_URL}/api/v1/user/${userId}/tracked_products`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(product)
                }).catch(() => {})
            }
        }
        localStorage.setItem("tracked_products", JSON.stringify(saved))
    }

    useEffect(() => {
        const fetchDetails = async () => {
            try {
                const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/products/${id}`)
                if (!response.ok) throw new Error("Product fetch failed")
                const data = await response.json()

                setProduct(data)
                setPriceHistory(generateMockPriceHistory(data.price))
            } catch (error) {
                console.error("Error fetching product details:", error)
            } finally {
                setLoading(false)
            }
        }

        if (id) fetchDetails()
    }, [id])

    if (loading) {
        return (
            <div className="max-w-6xl mx-auto space-y-8 animate-pulse">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12">
                    <div className="bg-white rounded-xl p-8 flex items-center justify-center border h-[400px] md:h-[500px]">
                        <Skeleton className="w-full h-full rounded-xl" />
                    </div>
                    <div className="space-y-6 pt-4">
                        <Skeleton className="h-6 w-32" />
                        <Skeleton className="h-10 w-full" />
                        <Skeleton className="h-10 w-3/4" />
                        <div className="pt-4 space-y-4">
                            <Skeleton className="h-12 w-48" />
                            <Skeleton className="h-6 w-32" />
                        </div>
                        <div className="flex gap-4 pt-6 border-t mt-8">
                            <Skeleton className="h-14 flex-1 rounded-xl" />
                            <Skeleton className="h-14 w-16 rounded-xl" />
                        </div>
                        <div className="mt-8">
                            <Skeleton className="h-24 w-full rounded-lg" />
                        </div>
                    </div>
                </div>
                <Card>
                    <CardHeader>
                        <Skeleton className="h-6 w-48" />
                    </CardHeader>
                    <CardContent>
                        <Skeleton className="h-[300px] w-full rounded-lg" />
                    </CardContent>
                </Card>
            </div>
        )
    }

    if (!product) {
        return (
            <div className="py-20 text-center space-y-4">
                <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground" />
                <h2 className="text-2xl font-bold">Product not found</h2>
                <p className="text-muted-foreground">The product you are looking for does not exist or was removed.</p>
            </div>
        )
    }

    return (
        <div className="max-w-6xl mx-auto space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12">
                {/* Product Image Section */}
                <div className="bg-white rounded-xl p-8 flex items-center justify-center border h-[400px] md:h-[500px]">
                    <ProductImage
                        src={product.image_url}
                        alt={product.product_name}
                        className="w-full h-full object-contain mix-blend-multiply"
                    />
                </div>

                {/* Product Info Section */}
                <div className="space-y-6">
                    <div className="space-y-2">
                        <div className="flex items-center gap-3">
                            {(() => {
                                const style = PLATFORM_MAP[product.platform] || DEFAULT_PLATFORM
                                return (
                                    <Badge className={`px-3 py-1 text-sm shadow-sm border flex items-center gap-1.5 font-bold tracking-wider ${style.bg} ${style.color} ${style.border} hover:${style.bg}`}>
                                        <style.icon className="h-4 w-4" />
                                        {product.platform}
                                    </Badge>
                                )
                            })()}
                            {product.discount_percent && product.discount_percent > 0 && (
                                <Badge className="bg-red-500 hover:bg-red-600">Save {product.discount_percent}%</Badge>
                            )}
                        </div>
                        <h1 className="text-3xl font-bold leading-tight">{product.product_name}</h1>
                    </div>

                    <div className="space-y-1">
                        <div className="text-4xl font-extrabold text-red-600">
                            {product.price.toLocaleString("vi-VN")}đ
                        </div>
                        {product.original_price && product.original_price > product.price && (
                            <div className="text-lg text-muted-foreground line-through">
                                {product.original_price.toLocaleString("vi-VN")}đ
                            </div>
                        )}
                    </div>

                    <div className="flex gap-4 pt-4 border-t">
                        <a href={product.product_url} target="_blank" rel="noreferrer" className="flex-1">
                            {(() => {
                                const style = PLATFORM_MAP[product.platform] || DEFAULT_PLATFORM
                                return (
                                    <Button size="lg" className={`w-full flex gap-2 text-white hover:opacity-90 transition-opacity`} style={{ backgroundColor: style.color.replace('text-[', '').replace(']', '') }} >
                                        <style.icon className="h-5 w-5" />
                                        <span className="font-semibold text-lg">Buy on {product.platform}</span>
                                        <ExternalLink className="h-4 w-4 ml-auto opacity-70" />
                                    </Button>
                                )
                            })()}
                        </a>
                        <Button 
                            size="lg" 
                            variant={isTracked ? "default" : "outline"} 
                            className={`flex-none px-4 transition-all ${isTracked ? "bg-red-50 text-red-500 hover:bg-red-100 hover:text-red-600 border-red-200" : ""}`}
                            onClick={toggleTrack}
                        >
                            <Heart className={`h-5 w-5 ${isTracked ? "fill-current" : ""}`} />
                        </Button>
                    </div>

                    <div className="bg-primary/5 rounded-2xl p-6 mt-6 border border-primary/20 shadow-sm relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-8 flex opacity-5 mix-blend-multiply pointer-events-none">
                            <Tag className="w-32 h-32" />
                        </div>
                        <h3 className="font-extrabold text-xl flex items-center gap-2 mb-4">
                            <Tag className="h-5 w-5 text-primary" />
                            {platformVouchers.length > 0 ? `Saved Vouchers (${product.platform})` : "Available Vouchers"}
                        </h3>
                        {platformVouchers.length > 0 ? (
                            <div className="space-y-3 relative z-10">
                                {platformVouchers.map((v, i) => (
                                    <div key={i} className="flex items-center justify-between bg-white rounded-xl p-4 border shadow-sm">
                                        <div className="flex-1 space-y-1">
                                            <div className="font-extrabold text-blue-600 text-lg">{v.code}</div>
                                            <div className="text-sm text-zinc-600 font-medium">{v.description || "Discount voucher"}</div>
                                        </div>
                                        <Button 
                                            variant="outline"
                                            className="px-6 hover:bg-blue-50 border-blue-200 text-blue-600 hover:text-blue-700" 
                                            onClick={() => navigator.clipboard.writeText(v.code)}
                                        >
                                            Copy Code
                                        </Button>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-sm text-muted-foreground leading-relaxed relative z-10 font-medium">
                                Sign in to automatically apply our hidden vouchers and bring this price down further at checkout. 
                                Or use the Compare dashboard to hunt for more vouchers automatically!
                            </p>
                        )}
                    </div>
                </div>
            </div>

            {/* Price History Chart */}
            <Card>
                <CardHeader>
                    <CardTitle>Price History (30 Days)</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="h-[300px] w-full mt-4">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={priceHistory} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                <XAxis
                                    dataKey="date"
                                    tick={{ fontSize: 12 }}
                                    tickMargin={10}
                                    stroke="#888888"
                                />
                                <YAxis
                                    tickFormatter={(val) => `${(val / 1000000).toFixed(1)}M`}
                                    tick={{ fontSize: 12 }}
                                    tickMargin={10}
                                    stroke="#888888"
                                />
                                <Tooltip
                                    formatter={(value?: number | string) => [`${Number(value ?? 0).toLocaleString("vi-VN")}đ`, "Price"]}
                                    contentStyle={{ borderRadius: "8px", border: "none", boxShadow: "0 4px 12px rgba(0,0,0,0.1)" }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="price"
                                    stroke="#2563eb"
                                    strokeWidth={3}
                                    dot={false}
                                    activeDot={{ r: 6, fill: "#2563eb" }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
