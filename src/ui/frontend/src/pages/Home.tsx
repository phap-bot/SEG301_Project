import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tag, TrendingUp, Search } from "lucide-react"
import { useState, useEffect, useRef } from "react"
import { useNavigate, Link } from "react-router-dom"
import { PLATFORM_MAP, DEFAULT_PLATFORM } from "@/lib/platforms"

// Mock Data for "Best Deals" section
const BEST_DEALS = [
    {
        id: 1,
        title: "iPhone 15 Pro Max 256GB Chính Hãng VN/A",
        platform: "FPT Shop",
        price: 26990000,
        original_price: 34990000,
        discount: 22,
        image_url: "https://minhtuanmobile.com/uploads/blog/tat-tan-tat-thong-tin-ve-iphone-15-khi-nao-ra-mat-co-gi-moi-230913125208.jpg"
    },
    {
        id: 2,
        title: "MacBook Air M2 13.6\" 8B/256GB",
        platform: "Lazada",
        price: 21500000,
        original_price: 28990000,
        discount: 25,
        image_url: "https://cdn.hoanghamobile.com/i/preview/Uploads/2022/06/07/macbook-air-m2-2022-7.png"
    },
    {
        id: 3,
        title: "Tai nghe Bluetooth Apple AirPods Pro 2",
        platform: "CellphoneS",
        price: 4990000,
        original_price: 6490000,
        discount: 23,
        image_url: "https://cdn2.cellphones.com.vn/insecure/rs:fill:358:358/q:90/plain/https://cellphones.com.vn/media/catalog/product/a/p/airpods-pro-2-1_3_2.png"
    }
]

export function Home() {
    const [query, setQuery] = useState("")
    const [suggestions, setSuggestions] = useState<any[]>([])
    const [showSuggestions, setShowSuggestions] = useState(false)
    const [isSearching, setIsSearching] = useState(false)
    const searchRef = useRef<HTMLDivElement>(null)
    const navigate = useNavigate()

    useEffect(() => {
        const fetchSuggestions = async () => {
            if (!query.trim()) {
                setSuggestions([])
                return
            }
            setIsSearching(true)
            try {
                const url = new URL(`${import.meta.env.VITE_API_URL}/api/v1/search`)
                url.searchParams.append("query", query)
                url.searchParams.append("limit", "5")
                const res = await fetch(url.toString())
                if (res.ok) {
                    const data = await res.json()
                    setSuggestions(data.results || [])
                }
            } catch (error) {
                console.error("Error fetching suggestions:", error)
            } finally {
                setIsSearching(false)
            }
        }

        const debounceTimer = setTimeout(fetchSuggestions, 300)
        return () => clearTimeout(debounceTimer)
    }, [query])

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
                setShowSuggestions(false)
            }
        }
        document.addEventListener("mousedown", handleClickOutside)
        return () => document.removeEventListener("mousedown", handleClickOutside)
    }, [])

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault()
        if (query.trim()) {
            setShowSuggestions(false)
            navigate(`/products?query=${encodeURIComponent(query)}`)
        }
    }

    return (
        <div className="space-y-16">
            {/* Hero Section */}
            <section className="text-center py-20 px-4 max-w-5xl mx-auto space-y-8">
                <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight">
                    Never Overpay for Tech <br />
                    <span className="text-primary text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-primary">
                        Find the Best Deals.
                    </span>
                </h1>
                <p className="text-xl md:text-2xl text-muted-foreground">
                    Compare prices instantly across Lazada, CellphoneS, DienMayXanh and more. Save money effortlessly with our advanced matching engine.
                </p>
                <div className="pt-6 flex justify-center">
                    <div ref={searchRef} className="w-full max-w-3xl relative">
                        <form onSubmit={handleSearch} className="flex w-full items-center relative">
                            <Search className="absolute left-6 h-6 w-6 text-muted-foreground" />
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => {
                                    setQuery(e.target.value)
                                    setShowSuggestions(true)
                                }}
                                onFocus={() => setShowSuggestions(true)}
                                placeholder="Search for MacBook, iPhone, Airpods..."
                                className="w-full h-16 pl-16 pr-6 rounded-full border-2 border-primary/20 bg-background text-xl shadow-md focus:border-primary focus:outline-none focus:ring-4 focus:ring-primary/20 transition-all"
                            />
                            <button type="submit" className="absolute right-3 h-12 px-8 rounded-full bg-primary text-primary-foreground text-lg font-bold hover:bg-primary/90 transition-colors">
                                Search
                            </button>
                        </form>

                        {/* Autocomplete Dropdown */}
                        {showSuggestions && query.trim() && (
                            <div className="absolute top-full mt-3 w-full bg-white dark:bg-zinc-950 border rounded-2xl shadow-xl overflow-hidden z-50 text-left">
                                {isSearching ? (
                                    <div className="p-6 text-center text-muted-foreground animate-pulse text-lg">Searching...</div>
                                ) : suggestions.length > 0 ? (
                                    <ul>
                                        {suggestions.map((item) => (
                                            <li key={item.id} className="border-b last:border-0">
                                                <Link
                                                    to={`/products/${item.id}`}
                                                    className="flex items-center gap-4 p-4 hover:bg-zinc-100 dark:hover:bg-zinc-900 transition-colors"
                                                >
                                                    {item.image_url ? (
                                                        <img src={item.image_url} alt={item.product_name} className="w-16 h-16 object-contain mix-blend-multiply" />
                                                    ) : (
                                                        <div className="w-16 h-16 bg-zinc-100 rounded-lg flex items-center justify-center text-sm text-muted-foreground border">No img</div>
                                                    )}
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-lg font-medium leading-tight text-zinc-900 line-clamp-1">{item.product_name}</p>
                                                        <p className="text-xl font-bold text-red-600 mt-1">{item.price.toLocaleString("vi-VN")}đ</p>
                                                    </div>
                                                    {(() => {
                                                        const style = PLATFORM_MAP[item.platform] || DEFAULT_PLATFORM
                                                        return (
                                                            <div className={`px-2 py-1 rounded-md text-xs font-bold border flex flex-col items-center justify-center gap-1 ${style.bg} ${style.color} ${style.border}`}>
                                                                <style.icon className="h-4 w-4" />
                                                                {style.shortAppLogo}
                                                            </div>
                                                        )
                                                    })()}
                                                </Link>
                                            </li>
                                        ))}
                                    </ul>
                                ) : (
                                    <div className="p-6 text-center text-muted-foreground text-lg cursor-pointer hover:bg-zinc-50 transition-colors" onClick={() => navigate(`/products?query=${encodeURIComponent(query)}`)}>
                                        <div className="flex items-center justify-center gap-2">
                                            <Search className="h-5 w-5" />
                                            <span>Search for "{query}"</span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </section>

            {/* Best Deals Platform Section */}
            <section className="space-y-8 px-4">
                <div className="flex items-center gap-3 border-b border-border/50 pb-4">
                    <TrendingUp className="h-8 w-8 text-red-500" />
                    <h2 className="text-3xl font-extrabold">Trending Hot Deals</h2>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
                    {BEST_DEALS.map((deal) => (
                        <Card key={deal.id} className="overflow-hidden hover:shadow-lg transition-all duration-300 group cursor-pointer border-border/50">
                            <div className="relative h-48 w-full bg-zinc-100 flex items-center justify-center p-4">
                                <img
                                    src={deal.image_url}
                                    alt={deal.title}
                                    className="max-h-full object-contain group-hover:scale-105 transition-transform duration-300 mix-blend-multiply"
                                />
                                <Badge className="absolute top-3 right-3 bg-red-500 hover:bg-red-600">
                                    -{deal.discount}%
                                </Badge>
                                <div className="absolute top-3 left-3 flex gap-2">
                                    {(() => {
                                        const style = PLATFORM_MAP[deal.platform] || DEFAULT_PLATFORM
                                        return (
                                            <Badge className={`shadow-sm border flex items-center gap-1.5 font-bold tracking-wider ${style.bg} ${style.color} ${style.border} hover:${style.bg}`}>
                                                <style.icon className="h-3.5 w-3.5" />
                                                {deal.platform}
                                            </Badge>
                                        )
                                    })()}
                                </div>
                            </div>
                            <CardHeader className="pt-6 pb-2">
                                <CardTitle className="text-xl line-clamp-2 leading-tight font-bold">
                                    {deal.title}
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="flex flex-col gap-1 pb-6 px-6">
                                <span className="text-3xl font-extrabold text-red-600">
                                    {deal.price.toLocaleString("vi-VN")}đ
                                </span>
                                <span className="text-lg text-muted-foreground line-through mb-1">
                                    {deal.original_price.toLocaleString("vi-VN")}đ
                                </span>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </section>

            {/* Vouchers Highlight */}
            <section className="bg-primary/5 rounded-3xl p-12 border border-primary/10 mt-20 flex flex-col items-center text-center space-y-6 mx-4">
                <Tag className="h-14 w-14 text-primary" />
                <h3 className="text-4xl font-extrabold">Super Voucher Hunt!</h3>
                <p className="max-w-2xl text-xl text-muted-foreground leading-relaxed">
                    Check out our daily updated vouchers from major e-commerce platforms. Combine vouchers with our best price matches to maximize your savings immensely.
                </p>
                <button className="h-14 px-10 text-lg bg-zinc-900 text-white dark:bg-white dark:text-black font-bold rounded-full mt-4 hover:scale-105 transition-transform">
                    View All Vouchers
                </button>
            </section>
        </div>
    )
}
