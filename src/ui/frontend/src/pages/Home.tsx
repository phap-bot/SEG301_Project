import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tag, TrendingUp, Search, ImageOff, Flame } from "lucide-react"
import { useState, useEffect, useRef } from "react"
import { useNavigate, Link } from "react-router-dom"
import { PLATFORM_MAP, DEFAULT_PLATFORM } from "@/lib/platforms"

const ProductImage = ({ src, alt, className }: { src?: string; alt: string; className?: string }) => {
    const [error, setError] = useState(false)
    if (!src || error) {
        return (
            <div className="flex flex-col items-center justify-center w-full h-full bg-zinc-50/80 rounded-xl overflow-hidden">
                <ImageOff className="w-8 h-8 mb-2 text-zinc-300" strokeWidth={1.5} />
                <span className="text-[11px] uppercase tracking-widest font-bold text-zinc-400">No Image</span>
            </div>
        )
    }
    return <img src={src} alt={alt} className={className} onError={() => setError(true)} loading="lazy" />
}

// Mock Data for "Best Deals" section
const BEST_DEALS = [
    {
        id: 1,
        title: "Apple iPhone 15 Pro Max 256GB - VN/A",
        platform: "Tiki",
        price: 24990000,
        original_price: 34990000,
        discount: 30,
        image_url: "https://cdn2.cellphones.com.vn/insecure/rs:fill:358:358/q:90/plain/https://cellphones.com.vn/media/catalog/product/i/p/iphone-15-pro-max_2__5_2_1_1_1_1.jpg",
        voucher: "TIKIAPP500"
    },
    {
        id: 2,
        title: "MacBook Air M2 13.6\" 256GB",
        platform: "Lazada",
        price: 19500000,
        original_price: 28990000,
        discount: 35,
        image_url: "https://cdn2.cellphones.com.vn/insecure/rs:fill:0:358/q:90/plain/https://cellphones.com.vn/media/catalog/product/t/e/text_ng_n_2__9_14.png",
        voucher: "LAZPLUS1M"
    },
    {
        id: 3,
        title: "Tai Nghe Apple AirPods Pro 2 (Type C)",
        platform: "CellphoneS",
        price: 4500000,
        original_price: 6490000,
        discount: 31,
        image_url: "https://cdn2.cellphones.com.vn/insecure/rs:fill:358:358/q:90/plain/https://cellphones.com.vn/media/catalog/product/g/r/group_111_1_1.png",
        voucher: "CPSAUDIOVIP"
    },
    {
        id: 4,
        title: "Smart Tivi Samsung 4K 65 inch 65AU7002",
        platform: "Điện Máy Xanh",
        price: 9990000,
        original_price: 15400000,
        discount: 36,
        image_url: "https://images.samsung.com/is/image/samsung/p6pim/vn/qa65qef1akxxv/gallery/vn-qled-tv-qa65qef1akxxv-m-t-tr--c-m-u-x-m-547801204?$Q90_1920_1280_F_PNG$",
        voucher: "TVSAMSUNG"
    },
    {
        id: 5,
        title: "Máy lạnh Panasonic Inverter 1 HP",
        platform: "Chợ Tốt",
        price: 6500000,
        original_price: 10990000,
        discount: 41,
        image_url: "https://cdn.tgdd.vn/Products/Images/7498/334158/Slider/1-1020x570.jpg",
        voucher: "CHOTOT100K"
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
                const userId = localStorage.getItem("user_id")
                if (userId) {
                    url.searchParams.append("user_id", userId)
                }
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
        <div className="space-y-4">
            {/* Hero Section */}
            <section className="relative w-full flex flex-col items-center justify-center text-center pt-24 pb-32 px-4 overflow-hidden mb-16">
                <div className="absolute top-[40%] left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/20 blur-[150px] rounded-full pointer-events-none -z-10" />
                <div className="absolute top-[20%] right-[10%] w-[500px] h-[500px] bg-blue-600/10 blur-[120px] rounded-full pointer-events-none -z-10" />
                <div className="absolute bottom-[20%] left-[10%] w-[600px] h-[600px] bg-indigo-500/10 blur-[140px] rounded-full pointer-events-none -z-10" />

                <div className="max-w-5xl mx-auto space-y-10 relative z-10 w-full">

                    <h1 className="text-5xl md:text-7xl lg:text-8xl font-black tracking-tight leading-[1.05]">
                        Never Overpay.<br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-primary to-indigo-600">
                            Seek The Best Deals.
                        </span>
                    </h1>
                    <p className="text-xl md:text-2xl text-zinc-500 font-medium max-w-3xl mx-auto leading-relaxed">
                        Compare prices instantly across Lazada, CellphoneS, DienMayXanh and more. Save money effortlessly on autopilot.
                    </p>
                    <div className="pt-8 flex justify-center px-2">
                        <div ref={searchRef} className="w-full max-w-4xl relative">
                            <form onSubmit={handleSearch} className="flex w-full items-center relative group">
                                <Search className="absolute left-8 h-7 w-7 text-primary z-10" strokeWidth={2.5} />
                                <input
                                    type="text"
                                    value={query}
                                    onChange={(e) => {
                                        setQuery(e.target.value)
                                        setShowSuggestions(true)
                                    }}
                                    onFocus={() => setShowSuggestions(true)}
                                    placeholder="Search for MacBook, iPhone, Airpods..."
                                    className="w-full h-20 pl-20 pr-44 rounded-full border-[3px] border-zinc-100 bg-white/80 backdrop-blur-md text-xl md:text-2xl font-medium shadow-[0_8px_30px_rgb(0,0,0,0.06)] focus:border-primary/50 focus:bg-white focus:outline-none transition-all placeholder:text-zinc-400"
                                />
                                <button type="submit" className="absolute right-3 top-3 bottom-3 px-10 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-xl font-bold tracking-wide hover:shadow-xl hover:shadow-primary/30 transition-all hover:scale-[1.02] active:scale-[0.98]">
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
                                                    <div className="w-16 h-16 shrink-0 rounded-lg overflow-hidden border bg-white flex items-center justify-center">
                                                        <ProductImage src={item.image_url} alt={item.product_name} className="w-full h-full object-contain mix-blend-multiply p-1" />
                                                    </div>
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
            </div>
        </section>

            {/* Best Deals Platform Section */}
            <section className="space-y-12 px-4 max-w-[1400px] mx-auto w-full pt-10">
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-border/50 pb-6 mb-8">
                    <div className="space-y-2">
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-red-100 rounded-2xl text-red-600 shadow-sm">
                                <TrendingUp className="h-8 w-8" strokeWidth={2.5} />
                            </div>
                            <h2 className="text-4xl md:text-5xl font-black tracking-tight text-zinc-900">Trending Hot Deals</h2>
                        </div>
                        <p className="text-muted-foreground md:ml-[72px] text-lg font-medium">Flash sales and deep discount items selected from top marketplaces.</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
                    {BEST_DEALS.map((deal) => (
                        <Card key={deal.id} className="overflow-hidden hover:shadow-xl transition-all duration-300 group cursor-pointer border-border/50 flex flex-col h-full bg-white group-hover:-translate-y-1">
                            <div className="relative h-[240px] w-full bg-white flex items-center justify-center p-4 border-b group-hover:bg-zinc-50/50 transition-colors">
                                <ProductImage
                                    src={deal.image_url}
                                    alt={deal.title}
                                    className="w-full h-full object-contain mix-blend-multiply group-hover:scale-105 transition-transform duration-500 ease-out"
                                />
                                {deal.discount >= 30 ? (
                                    <div className="absolute top-2 right-2 flex items-center gap-1.5 px-2.5 py-1 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-full shadow-lg shadow-red-500/30 animate-pulse pointer-events-none">
                                        <Flame className="w-3.5 h-3.5 fill-current" />
                                        <span className="text-[11px] font-black uppercase tracking-wider">-{deal.discount}%</span>
                                    </div>
                                ) : deal.discount > 0 ? (
                                    <Badge className="absolute top-2 right-2 bg-red-500 hover:bg-red-600 shadow-md border-0 text-[11px] px-2 py-0.5 pointer-events-none">
                                        -{deal.discount}%
                                    </Badge>
                                ) : null}
                                <div className="absolute top-2 left-2 flex flex-col gap-2 items-start">
                                    {(() => {
                                        const style = PLATFORM_MAP[deal.platform] || DEFAULT_PLATFORM
                                        return (
                                            <Badge className={`shadow-md border-0 flex items-center gap-1.5 px-2.5 py-1.5 ${style.bg} ${style.color} pointer-events-none`}>
                                                <style.icon className="h-4 w-4" />
                                                <span className="font-extrabold text-[11px] uppercase tracking-widest">{deal.platform}</span>
                                            </Badge>
                                        )
                                    })()}
                                    {deal.voucher && (
                                        <Badge className="bg-blue-600 text-white shadow-md border-0 text-[10px] px-2.5 py-1 uppercase tracking-wider font-bold gap-1 pointer-events-none">
                                            <Tag className="w-3.5 h-3.5" />
                                            Voucher: {deal.voucher}
                                        </Badge>
                                    )}
                                </div>
                            </div>
                            <div className="flex flex-col flex-1 p-5 bg-zinc-50/30">
                                <h3 className="text-lg line-clamp-2 leading-snug font-semibold text-zinc-900 mb-4 group-hover:text-primary transition-colors">
                                    {deal.title}
                                </h3>
                                <div className="mt-auto flex flex-col gap-1.5">
                                    <span className="text-2xl font-extrabold text-red-600 tabular-nums leading-none">
                                        {deal.price.toLocaleString("vi-VN")}đ
                                    </span>
                                    <div className="flex items-center gap-2 min-h-[1.5rem]">
                                        <span className="text-sm text-muted-foreground line-through font-medium">
                                            {deal.original_price.toLocaleString("vi-VN")}đ
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </Card>
                    ))}
                </div>
            </section>

            {/* Vouchers Highlight */}
            <section className="relative overflow-hidden bg-gradient-to-br from-blue-600 via-primary to-indigo-600 rounded-[3rem] p-12 md:p-24 mt-24 mb-16 flex flex-col items-center text-center space-y-8 mx-4 max-w-7xl lg:mx-auto shadow-2xl shadow-primary/20">
                <div className="absolute -top-24 -right-24 w-72 h-72 bg-white/20 blur-3xl rounded-full pointer-events-none" />
                <div className="absolute -bottom-24 -left-24 w-80 h-80 bg-black/20 blur-3xl rounded-full pointer-events-none" />
                
                <div className="p-6 bg-white/10 backdrop-blur-md rounded-3xl border border-white/20 text-white shadow-lg">
                    <Tag className="h-14 w-14" strokeWidth={2.5} />
                </div>
                <h3 className="text-4xl md:text-6xl font-black text-white tracking-tight leading-[1.1]">The Super Voucher Hunt!</h3>
                <p className="max-w-3xl text-xl md:text-2xl text-white/90 font-medium leading-relaxed">
                    Check out our daily updated vouchers from major e-commerce platforms. Combine vouchers with our matching engine to maximize your savings instantly.
                </p>
                <button className="h-16 px-12 text-xl bg-white text-primary font-black rounded-full mt-6 shadow-xl hover:shadow-2xl hover:scale-105 transition-all active:scale-95 uppercase tracking-wide">
                    View All Vouchers
                </button>
            </section>
        </div>
    )
}
