import { useEffect, useMemo, useState } from "react"
import { useNavigate, Link } from "react-router-dom"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"

import { Activity, Search, ShoppingCart, Heart, LogOut, Star, Flame, Tag, X, ImageOff } from "lucide-react"

import { PLATFORM_MAP, DEFAULT_PLATFORM } from "@/lib/platforms"

type Voucher = {
    platform: string
    code: string
    discount_amount?: number | null
    discount_percentage?: number | null
    min_spend?: number | null
    description?: string | null
    valid_until?: string | null
}

type Product = {
    id: number
    platform: string
    product_id: string
    product_name: string
    price: number
    original_price?: number | null
    discount_percent?: number | null
    product_url: string
    image_url?: string | null
    rating?: number | null
    review_count?: number | null
}

type Offer = {
    platform: string
    product: Product
    base_price?: number | null
    discount_percent?: number | null
    voucher?: Voucher | null
    effective_price?: number | null
    score: number
}

type RecommendationGroup = {
    group_key: string
    display_name: string
    best_overall?: Offer | null
    best_by_platform: Offer[]
}

type CompareResponse = {
    query: string
    groups: RecommendationGroup[]
}

export function Dashboard() {
    const navigate = useNavigate()

    const [compareQuery, setCompareQuery] = useState("")
    const [compareLoading, setCompareLoading] = useState(false)
    const [compareData, setCompareData] = useState<CompareResponse | null>(null)
    const [compareError, setCompareError] = useState<string | null>(null)
    const [trackedProducts, setTrackedProducts] = useState<Product[]>([])
    const [savedVouchers, setSavedVouchers] = useState<Voucher[]>([])
    const [totalSaved, setTotalSaved] = useState(0)

    useEffect(() => {
        const loadFromBackend = async () => {
            const userId = localStorage.getItem("user_id")
            if (userId) {
                try {
                    const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/user/${userId}/tracking`)
                    if (res.ok) {
                        const data = await res.json()
                        const tr = data.tracked_products || []
                        const vo = data.saved_vouchers || []
                        setTrackedProducts(tr)
                        setSavedVouchers(vo)
                        localStorage.setItem("tracked_products", JSON.stringify(tr))
                        localStorage.setItem("saved_vouchers", JSON.stringify(vo))
                        
                        const sum = tr.reduce((acc: number, p: Product) => {
                            if (p.original_price && p.original_price > p.price) {
                                return acc + (p.original_price - p.price)
                            }
                            return acc
                        }, 0)
                        setTotalSaved(sum)
                        return
                    }
                } catch (err) {
                    console.error("Failed to load tracking from DB", err)
                }
            }
            
            // Fallback
            const tr = JSON.parse(localStorage.getItem("tracked_products") || "[]")
            setTrackedProducts(tr)
            const vo = JSON.parse(localStorage.getItem("saved_vouchers") || "[]")
            setSavedVouchers(vo)
            const sum = tr.reduce((acc: number, p: Product) => {
                if (p.original_price && p.original_price > p.price) {
                    return acc + (p.original_price - p.price)
                }
                return acc
            }, 0)
            setTotalSaved(sum)
        }
        loadFromBackend()
    }, [])
    
    const removeTrackedProduct = async (id: number) => {
        const userId = localStorage.getItem("user_id")
        if (userId) {
            try {
                await fetch(`${import.meta.env.VITE_API_URL}/api/v1/user/${userId}/tracked_products/${id}`, { method: "DELETE" })
            } catch (err) {}
        }
        
        let saved = JSON.parse(localStorage.getItem("tracked_products") || "[]")
        saved = saved.filter((p: Product) => p.id !== id)
        localStorage.setItem("tracked_products", JSON.stringify(saved))
        setTrackedProducts(saved)
        
        const sum = saved.reduce((acc: number, p: Product) => {
            if (p.original_price && p.original_price > p.price) {
                return acc + (p.original_price - p.price)
            }
            return acc
        }, 0)
        setTotalSaved(sum)
    }

    const saveVoucher = async (v: Voucher) => {
        let saved = JSON.parse(localStorage.getItem("saved_vouchers") || "[]")
        if (!saved.find((sv: Voucher) => sv.code === v.code)) {
            saved.push(v)
            localStorage.setItem("saved_vouchers", JSON.stringify(saved))
            setSavedVouchers(saved)
            
            const userId = localStorage.getItem("user_id")
            if (userId) {
                try {
                    await fetch(`${import.meta.env.VITE_API_URL}/api/v1/user/${userId}/saved_vouchers`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(v)
                    })
                } catch (err) {}
            }
        }
    }

    const removeVoucher = async (code: string) => {
        const userId = localStorage.getItem("user_id")
        if (userId) {
            try {
                await fetch(`${import.meta.env.VITE_API_URL}/api/v1/user/${userId}/saved_vouchers/${code}`, { method: "DELETE" })
            } catch(e) {}
        }
        let saved = JSON.parse(localStorage.getItem("saved_vouchers") || "[]")
        saved = saved.filter((sv: Voucher) => sv.code !== code)
        localStorage.setItem("saved_vouchers", JSON.stringify(saved))
        setSavedVouchers(saved)
    }

    const totalGroups = useMemo(() => compareData?.groups?.length || 0, [compareData])

    const runCompare = async () => {
        const q = compareQuery.trim()
        if (!q) return

        setCompareLoading(true)
        setCompareError(null)
        try {
            const url = new URL(`${import.meta.env.VITE_API_URL}/api/v1/compare`)
            url.searchParams.set("query", q)
            url.searchParams.set("search_type", "hybrid")
            url.searchParams.set("max_candidates", "100")
            url.searchParams.set("max_groups", "5")
            const userId = localStorage.getItem("user_id")
            if (userId) {
                url.searchParams.set("user_id", userId)
            }

            const res = await fetch(url.toString())
            if (!res.ok) throw new Error("Compare request failed")
            const data: CompareResponse = await res.json()
            setCompareData(data)
        } catch (e: any) {
            setCompareError(e?.message || "Compare failed")
            setCompareData(null)
        } finally {
            setCompareLoading(false)
        }
    }

    // This button is kept to preserve layout, but without auth it's just a navigation.
    const handleLogout = async () => {
        navigate("/")
    }

    useEffect(() => {
        // keep compareData stable; no auth listener anymore
    }, [])

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between border-b pb-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
                    <p className="text-muted-foreground">Price Compare & Recommendations</p>
                </div>
                <Button variant="outline" onClick={handleLogout} className="flex gap-2">
                    <LogOut className="h-4 w-4" />
                    Back
                </Button>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Saved</CardTitle>
                        <Activity className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-green-600">{totalSaved.toLocaleString("vi-VN")}đ</div>
                        <p className="text-xs text-muted-foreground">From tracked price drops</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Tracked Products</CardTitle>
                        <Heart className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{trackedProducts.length}</div>
                        <p className="text-xs text-muted-foreground">
                            {trackedProducts.length === 0 ? "Your watchlist is empty" : "Actively tracking price changes"}
                        </p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Vouchers Used</CardTitle>
                        <ShoppingCart className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{savedVouchers.length}</div>
                        <p className="text-xs text-muted-foreground">Saved in your wallet</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Quick Tips</CardTitle>
                        <Star className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <p className="text-sm text-muted-foreground">Try searching “airpods”, “iphone”, etc.</p>
                    </CardContent>
                </Card>
            </div>

            <Card className="border-border/60">
                <CardHeader className="space-y-2">
                    <CardTitle className="text-xl">Price Compare & Recommendation</CardTitle>
                    <p className="text-sm text-muted-foreground">
                        Enter a product name. We group similar listings across platforms and recommend the best deal (price + discounts + vouchers when available).
                    </p>
                </CardHeader>
                <CardContent className="space-y-5">
                    <div className="flex flex-col md:flex-row gap-3">
                        <div className="flex-1 relative">
                            <Search className="absolute left-4 top-3.5 h-5 w-5 text-muted-foreground" />
                            <Input
                                value={compareQuery}
                                onChange={(e) => setCompareQuery(e.target.value)}
                                placeholder="e.g. AirPods Pro 2, iPhone 15 Pro Max 256..."
                                className="h-12 pl-12 rounded-xl"
                                onKeyDown={(e) => {
                                    if (e.key === "Enter") runCompare()
                                }}
                            />
                        </div>
                        <Button className="h-12 rounded-xl font-bold" disabled={compareLoading} onClick={runCompare}>
                            {compareLoading ? "Comparing..." : "Compare"}
                        </Button>
                    </div>

                    {compareError && <div className="text-sm text-red-600">{compareError}</div>}

                    {compareData && totalGroups === 0 && (
                        <div className="text-sm text-muted-foreground">No grouped recommendations found.</div>
                    )}

                    {compareData && totalGroups > 0 && (
                        <div className="space-y-6">
                            {compareData.groups.map((g) => (
                                <div key={g.group_key} className="rounded-2xl border p-4 md:p-5 space-y-4">
                                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                                        <div>
                                            <div className="text-lg font-bold">{g.display_name}</div>
                                            <div className="text-xs text-muted-foreground">Group: {g.group_key}</div>
                                        </div>
                                        {g.best_overall && (
                                            <div className="flex items-center gap-2">
                                                <Badge className="bg-green-600 hover:bg-green-700">Best overall</Badge>
                                                <span className="text-lg font-extrabold text-red-600">
                                                    {(g.best_overall.effective_price ?? g.best_overall.product.price).toLocaleString("vi-VN")}đ
                                                </span>
                                            </div>
                                        )}
                                    </div>

                                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                        {g.best_by_platform.map((o) => {
                                            const style = PLATFORM_MAP[o.platform] || PLATFORM_MAP[o.product.platform] || DEFAULT_PLATFORM
                                            const eff = o.effective_price ?? o.product.price
                                            return (
                                                <a
                                                    key={`${g.group_key}-${o.platform}-${o.product.id}`}
                                                    href={o.product.product_url}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                    className="block rounded-xl border p-4 hover:bg-zinc-50 transition-colors"
                                                >
                                                    <div className="flex items-start gap-3">
                                                        {o.product.image_url ? (
                                                            <img
                                                                src={o.product.image_url}
                                                                alt={o.product.product_name}
                                                                className="h-16 w-16 object-contain bg-white rounded-lg border p-1 mix-blend-multiply"
                                                            />
                                                        ) : (
                                                            <div className="h-16 w-16 rounded-lg border bg-white flex items-center justify-center text-xs text-muted-foreground">
                                                                No img
                                                            </div>
                                                        )}

                                                        <div className="min-w-0 flex-1">
                                                            <div className="flex items-center gap-2">
                                                                <Badge className={`border ${style.bg} ${style.color} ${style.border}`}>
                                                                    <style.icon className="h-3.5 w-3.5 mr-1" />
                                                                    {o.platform}
                                                                </Badge>
                                                                {o.discount_percent && o.discount_percent >= 30 ? (
                                                                    <div className="flex items-center gap-1 px-2.5 py-0.5 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-full shadow-md shadow-red-500/20 animate-pulse">
                                                                        <Flame className="h-3 w-3 fill-current" />
                                                                        <span className="text-[10px] font-black uppercase tracking-wide">-{o.discount_percent}% HOT</span>
                                                                    </div>
                                                                ) : o.discount_percent ? (
                                                                    <Badge className="bg-red-500 hover:bg-red-600 border-0">-{o.discount_percent}%</Badge>
                                                                ) : null}
                                                                {o.voucher ? (
                                                                    <div 
                                                                        className="flex items-center gap-1 px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-md shadow-md shadow-blue-500/20 cursor-pointer active:scale-95 transition-transform border border-blue-500"
                                                                        onClick={(e) => {
                                                                            e.preventDefault()
                                                                            e.stopPropagation()
                                                                            saveVoucher(o.voucher!)
                                                                        }}
                                                                    >
                                                                        <Tag className="h-3.5 w-3.5" />
                                                                        <span className="text-[10px] font-bold uppercase tracking-wider">Save {o.voucher.code}</span>
                                                                    </div>
                                                                ) : null}
                                                            </div>
                                                            <div className="mt-2 font-medium text-sm line-clamp-2 text-zinc-800">
                                                                {o.product.product_name}
                                                            </div>
                                                            <div className="mt-2 flex items-baseline gap-2">
                                                                <span className="text-xl font-extrabold text-red-600">{eff.toLocaleString("vi-VN")}đ</span>
                                                                {o.base_price && o.base_price > eff ? (
                                                                    <span className="text-sm text-muted-foreground line-through">
                                                                        {o.base_price.toLocaleString("vi-VN")}đ
                                                                    </span>
                                                                ) : null}
                                                            </div>
                                                            {o.voucher?.code ? (
                                                                <div className="mt-1 text-xs text-muted-foreground">
                                                                    Voucher: <span className="font-semibold">{o.voucher.code}</span>
                                                                </div>
                                                            ) : null}
                                                        </div>
                                                    </div>
                                                </a>
                                            )
                                        })}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* New Sections for Tracking */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-4">
                <Card className="border-border/60 shadow-sm overflow-hidden group hover:shadow-md transition-shadow">
                    <CardHeader className="flex flex-row items-center justify-between pb-4 border-b px-6 pt-6 mb-4 bg-zinc-50/50">
                        <div className="space-y-1">
                            <CardTitle className="text-lg flex items-center gap-2">
                                <Heart className="h-5 w-5 text-red-500 fill-red-100" />
                                Tracked Pre-Order / Price Drops
                            </CardTitle>
                        </div>
                    </CardHeader>
                    {trackedProducts.length > 0 ? (
                        <CardContent className="px-6 pb-6">
                            <div className="space-y-4 max-h-[300px] overflow-y-auto pr-2">
                                {trackedProducts.map(p => {
                                    const style = PLATFORM_MAP[p.platform] || DEFAULT_PLATFORM
                                    return (
                                        <div key={p.id} className="flex items-center gap-4 p-3 border rounded-xl hover:bg-zinc-50 transition-colors">
                                            {p.image_url ? (
                                                <img src={p.image_url} alt={p.product_name} className="w-16 h-16 object-contain rounded-lg border bg-white p-1" />
                                            ) : (
                                                <div className="w-16 h-16 bg-zinc-100 rounded-lg flex items-center justify-center">
                                                    <ImageOff className="w-6 h-6 text-zinc-300" />
                                                </div>
                                            )}
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <Badge className={`border px-1.5 py-0 text-[10px] ${style.bg} ${style.color}`}>
                                                        <style.icon className="w-3 h-3 mr-1"/>{p.platform}
                                                    </Badge>
                                                </div>
                                                <Link to={`/products/${p.id}`} className="font-semibold text-sm line-clamp-1 hover:text-primary transition-colors">
                                                    {p.product_name}
                                                </Link>
                                                <div className="text-red-600 font-extrabold text-sm mt-1">
                                                    {p.price.toLocaleString("vi-VN")}đ
                                                </div>
                                            </div>
                                            <Button variant="ghost" size="icon" className="text-zinc-400 hover:text-red-500 hover:bg-red-50" onClick={() => removeTrackedProduct(p.id)}>
                                                <X className="w-4 h-4" />
                                            </Button>
                                        </div>
                                    )
                                })}
                            </div>
                        </CardContent>
                    ) : (
                        <CardContent className="px-6 pb-6">
                            <div className="flex flex-col items-center justify-center py-12 text-center space-y-3 border-2 border-dashed rounded-2xl bg-zinc-50/50 group-hover:bg-zinc-50 transition-colors">
                                <div className="p-3 bg-white rounded-full shadow-sm">
                                    <Heart className="h-6 w-6 text-zinc-300" />
                                </div>
                                <div className="text-sm font-bold text-zinc-600">No tracked products yet</div>
                                <p className="text-xs text-zinc-400 max-w-[250px] font-medium">Search for products and click the heart icon to track price drops here.</p>
                            </div>
                        </CardContent>
                    )}
                </Card>

                <Card className="border-border/60 shadow-sm overflow-hidden group hover:shadow-md transition-shadow">
                    <CardHeader className="flex flex-row items-center justify-between pb-4 border-b px-6 pt-6 mb-4 bg-zinc-50/50">
                        <div className="space-y-1">
                            <CardTitle className="text-lg flex items-center gap-2">
                                <Tag className="h-5 w-5 text-blue-500 fill-blue-100" />
                                Saved Vouchers Wallet
                            </CardTitle>
                        </div>
                    </CardHeader>
                    {savedVouchers.length > 0 ? (
                        <CardContent className="px-6 pb-6">
                            <div className="space-y-4 max-h-[300px] overflow-y-auto pr-2">
                                {savedVouchers.map((v, i) => (
                                    <div key={i} className="flex items-center gap-4 p-3 border rounded-xl hover:bg-zinc-50 transition-colors bg-gradient-to-r from-blue-50/20 to-transparent">
                                        <div className="w-16 h-16 bg-blue-50 text-blue-600 rounded-lg flex flex-col items-center justify-center border border-blue-100 shadow-sm">
                                            <Tag className="w-6 h-6 mb-1" />
                                            <span className="text-[10px] font-bold uppercase">{v.platform}</span>
                                        </div>
                                        <div className="flex-1 min-w-0 space-y-1">
                                            <div className="font-extrabold text-lg text-blue-700">{v.code}</div>
                                            <div className="text-sm font-medium text-zinc-600 line-clamp-1">{v.description || `Discount ${v.discount_percentage ? v.discount_percentage + '%' : v.discount_amount?.toLocaleString("vi-VN") + 'đ'}`}</div>
                                            {v.min_spend && <div className="text-[11px] text-zinc-500 font-medium">Min spend: {v.min_spend.toLocaleString("vi-VN")}đ</div>}
                                        </div>
                                        <Button variant="ghost" size="icon" className="text-zinc-400 hover:text-red-500 hover:bg-red-50" onClick={() => removeVoucher(v.code)}>
                                            <X className="w-4 h-4" />
                                        </Button>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    ) : (
                        <CardContent className="px-6 pb-6">
                            <div className="flex flex-col items-center justify-center py-12 text-center space-y-3 border-2 border-dashed rounded-2xl bg-zinc-50/50 group-hover:bg-zinc-50 transition-colors">
                                <div className="p-3 bg-white rounded-full shadow-sm">
                                    <Tag className="h-6 w-6 text-zinc-300" />
                                </div>
                                <div className="text-sm font-bold text-zinc-600">Your voucher wallet is empty</div>
                                <p className="text-xs text-zinc-400 max-w-[250px] font-medium">Vouchers from best deals will automatically be saved here for quick tracking & usage.</p>
                            </div>
                        </CardContent>
                    )}
                </Card>
            </div>
        </div>
    )
}

