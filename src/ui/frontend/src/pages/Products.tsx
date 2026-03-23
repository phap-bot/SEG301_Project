import { useMemo, useState, useEffect, useRef } from "react"
import { useSearchParams, Link } from "react-router-dom"
import { Search, Filter, Star, ImageOff, Flame } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { PLATFORM_MAP, DEFAULT_PLATFORM } from "@/lib/platforms"

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
    rating?: number
    review_count?: number
}

type Voucher = {
    platform: string
    code: string
    discount_amount?: number | null
    discount_percentage?: number | null
    min_spend?: number | null
    description?: string | null
    valid_until?: string | null
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

const formatVnd = (value: number) =>
    `${Math.round(Number(value)).toLocaleString("vi-VN")}đ`

const formatIntInput = (raw: string) => {
    const digits = raw.replace(/[^\d]/g, "")
    if (!digits) return ""
    return Number(digits).toLocaleString("vi-VN")
}

const normalizeMinMax = (minRaw: string, maxRaw: string) => {
    const minVal = minRaw ? Number(minRaw) : NaN
    const maxVal = maxRaw ? Number(maxRaw) : NaN
    if (!Number.isFinite(minVal) || !Number.isFinite(maxVal)) return { min: minRaw, max: maxRaw }
    if (minVal <= maxVal) return { min: minRaw, max: maxRaw }
    return { min: String(maxVal), max: String(minVal) }
}

const PLATFORMS = ["Điện Máy Xanh", "CellphoneS", "Lazada", "Tiki", "Chợ Tốt", "FPT Shop", "eBay"]

export function Products() {
    const [searchParams, setSearchParams] = useSearchParams()
    const initialQuery = searchParams.get("query") || ""

    const [query, setQuery] = useState(initialQuery)
    const [suggestions, setSuggestions] = useState<any[]>([])
    const [showSuggestions, setShowSuggestions] = useState(false)
    const [isSearching, setIsSearching] = useState(false)
    const searchRef = useRef<HTMLDivElement>(null)
    const [results, setResults] = useState<Product[]>([])
    const [loading, setLoading] = useState(false)
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(1)
    const limit = 20

    // Filters
    const [minPrice, setMinPrice] = useState("")
    const [maxPrice, setMaxPrice] = useState("")
    const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([])
    const [searchType, setSearchType] = useState("hybrid")

    // Compare
    const [compareOpen, setCompareOpen] = useState(false)
    const [compareLoading, setCompareLoading] = useState(false)
    const [compareData, setCompareData] = useState<CompareResponse | null>(null)
    const [compareError, setCompareError] = useState<string | null>(null)
    const compareEnabled = useMemo(() => Boolean(query.trim()), [query])

    const runCompare = async () => {
        const q = query.trim()
        if (!q) return

        setCompareOpen(true)
        setCompareLoading(true)
        setCompareError(null)
        try {
            const url = new URL(`${import.meta.env.VITE_API_URL}/api/v1/compare`)
            url.searchParams.set("query", q)
            url.searchParams.set("search_type", "hybrid")
            url.searchParams.set("max_candidates", "100")
            url.searchParams.set("max_groups", "5")
            const normalized = normalizeMinMax(minPrice, maxPrice)
            if (normalized.min) url.searchParams.set("min_price", normalized.min)
            if (normalized.max) url.searchParams.set("max_price", normalized.max)
            selectedPlatforms.forEach((p) => url.searchParams.append("platforms", p))

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

    const fetchProducts = async (currentQuery = query, nextPage = page) => {
        if (!currentQuery.trim()) {
            setResults([])
            setTotal(0)
            setPage(1)
            setCompareOpen(false)
            setCompareData(null)
            setCompareError(null)
            return
        }

        setLoading(true)
        try {
            const url = new URL(`${import.meta.env.VITE_API_URL}/api/v1/search`)
            url.searchParams.append("query", currentQuery)
            url.searchParams.append("limit", String(limit))
            url.searchParams.append("page", String(nextPage))
            const normalized = normalizeMinMax(minPrice, maxPrice)
            if (normalized.min) url.searchParams.append("min_price", normalized.min)
            if (normalized.max) url.searchParams.append("max_price", normalized.max)
            selectedPlatforms.forEach(p => url.searchParams.append("platforms", p))
            url.searchParams.append("search_type", searchType)

            const userId = localStorage.getItem("user_id")
            if (userId) {
                url.searchParams.append("user_id", userId)
            }
            const res = await fetch(url.toString())
            if (!res.ok) throw new Error("Failed to fetch products")
            const data = await res.json()

            setResults(data.results || [])
            setTotal(data.total_results || 0)
            setPage(data.page || nextPage)
        } catch (error) {
            console.error(error)
        } finally {
            setLoading(false)
        }
    }

    // Trigger search on mount if query exists in URL
    useEffect(() => {
        if (initialQuery) {
            fetchProducts(initialQuery, 1)
        }
    }, []) // eslint-disable-line react-hooks/exhaustive-deps

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

    const handleSearch = (e?: React.FormEvent) => {
        if (e) e.preventDefault()
        setShowSuggestions(false)
        setSearchParams(query ? { query } : {})
        fetchProducts(query, 1)
    }

    const togglePlatform = (platform: string) => {
        setSelectedPlatforms(prev =>
            prev.includes(platform)
                ? prev.filter(p => p !== platform)
                : [...prev, platform]
        )
    }

    return (
        <div className="flex flex-col md:flex-row gap-6">
            {/* Sidebar Filters */}
            <aside className="w-full md:w-[320px] shrink-0">
                <div className="bg-white rounded-3xl border shadow-sm p-6 md:sticky md:top-6">
                    <div className="flex items-center gap-3 border-b-2 border-zinc-100 pb-5 mb-6">
                        <div className="p-2.5 bg-primary/10 text-primary rounded-xl">
                            <Filter className="h-6 w-6" />
                        </div>
                        <h3 className="text-xl font-extrabold tracking-tight">Filters</h3>
                    </div>

                    <div className="space-y-8">
                        {/* Platforms */}
                        <div>
                            <h4 className="font-bold mb-4 text-sm uppercase tracking-wider text-muted-foreground">Platforms</h4>
                            <div className="flex flex-col gap-3">
                                {PLATFORMS.map(platform => {
                                    const style = PLATFORM_MAP[platform] || DEFAULT_PLATFORM
                                    const isSelected = selectedPlatforms.includes(platform)
                                    return (
                                        <button
                                            key={platform}
                                            className={`w-full flex items-center justify-start gap-4 px-4 py-3 rounded-2xl border-2 text-base font-bold transition-all duration-200 ${isSelected
                                                ? `${style.bg} ${style.color} ${style.border} shadow-md scale-[1.02]`
                                                : `bg-white border-zinc-100 text-zinc-600 hover:border-zinc-300 hover:shadow-sm hover:text-zinc-900 hover:scale-[1.01]`
                                                }`}
                                            onClick={() => togglePlatform(platform)}
                                            type="button"
                                        >
                                            <div className={`p-2 rounded-xl flex items-center justify-center transition-colors ${isSelected ? 'bg-white/60 shadow-sm' : 'bg-zinc-100'}`}>
                                                <style.icon className={`h-5 w-5 ${isSelected ? '' : style.color}`} />
                                            </div>
                                            {platform}
                                        </button>
                                    )
                                })}
                            </div>
                        </div>

                        {/* Search Mode */}
                        <div>
                            <h4 className="font-bold mb-4 text-sm uppercase tracking-wider text-muted-foreground">Search Mode</h4>
                            <div className="flex flex-col gap-3">
                                {[
                                    { value: 'hybrid', label: 'Hybrid Search', desc: 'AI + Keyword (Best)' },
                                    { value: 'vector', label: 'Semantic AI', desc: 'Smart meaning match' },
                                    { value: 'bm25', label: 'Exact Keyword', desc: 'Strict word match' },
                                ].map(mode => (
                                    <button
                                        key={mode.value}
                                        onClick={() => setSearchType(mode.value)}
                                        className={`w-full flex flex-col items-start px-4 py-3 rounded-2xl border-2 transition-all duration-200 ${searchType === mode.value 
                                            ? 'border-primary bg-primary/5 text-primary scale-[1.02] shadow-sm' 
                                            : 'border-zinc-100 bg-white text-zinc-600 hover:border-zinc-300 hover:bg-zinc-50 hover:scale-[1.01]'}`}
                                        type="button"
                                    >
                                        <div className="font-extrabold text-sm">{mode.label}</div>
                                        <div className={`text-xs mt-0.5 font-medium ${searchType === mode.value ? 'text-primary/70' : 'text-zinc-400'}`}>{mode.desc}</div>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Price Range */}
                        <div>
                            <h4 className="font-bold mb-4 text-sm uppercase tracking-wider text-muted-foreground">Price Range</h4>
                            <div className="flex items-center gap-2 bg-zinc-50 border-2 border-zinc-100 rounded-2xl p-2 focus-within:border-primary/50 focus-within:ring-4 focus-within:ring-primary/10 transition-all">
                                <Input
                                    type="text"
                                    inputMode="numeric"
                                    placeholder="Min"
                                    value={formatIntInput(minPrice)}
                                    onChange={(e) => setMinPrice(e.target.value.replace(/[^\d]/g, ""))}
                                    className="h-10 text-sm font-bold border-0 focus-visible:ring-0 shadow-none px-2 text-center bg-transparent"
                                />
                                <span className="text-zinc-300 font-extrabold">-</span>
                                <Input
                                    type="text"
                                    inputMode="numeric"
                                    placeholder="Max"
                                    value={formatIntInput(maxPrice)}
                                    onChange={(e) => setMaxPrice(e.target.value.replace(/[^\d]/g, ""))}
                                    className="h-10 text-sm font-bold border-0 focus-visible:ring-0 shadow-none px-2 text-center bg-transparent"
                                />
                            </div>
                        </div>

                        <Button className="w-full h-14 text-lg rounded-2xl font-extrabold mt-6 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-xl shadow-blue-600/20 border-0 hover:scale-[1.02] transition-all" onClick={() => handleSearch()}>
                            Apply Filters
                        </Button>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <div className="flex-1 space-y-6">
                <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-4 relative">
                    <div ref={searchRef} className="flex-1 relative">
                        <Input
                            value={query}
                            onChange={(e) => {
                                setQuery(e.target.value)
                                setShowSuggestions(true)
                            }}
                            onFocus={() => setShowSuggestions(true)}
                            placeholder="Search for MacBook, iPhone, Airpods..."
                            className="w-full h-14 text-lg pl-14 rounded-2xl border-2 border-primary/20 shadow-sm focus-visible:ring-primary focus-visible:ring-2 transition-all"
                        />
                        <Search className="absolute left-5 top-4 h-6 w-6 text-muted-foreground" />

                        {/* Autocomplete Dropdown */}
                        {showSuggestions && query.trim() && (
                            <div className="absolute top-full mt-2 w-full bg-white dark:bg-zinc-950 border rounded-2xl shadow-xl overflow-hidden z-50 text-left">
                                {isSearching ? (
                                    <div className="p-6 text-center text-muted-foreground animate-pulse text-lg">Searching...</div>
                                ) : suggestions.length > 0 ? (
                                    <ul>
                                        {suggestions.map((item) => (
                                            <li key={item.id} className="border-b last:border-0 hover:bg-zinc-50 dark:hover:bg-zinc-900 transition-colors">
                                                <Link
                                                    to={`/products/${item.id}`}
                                                    className="flex items-center gap-4 p-4"
                                                >
                                                    <div className="w-14 h-14 shrink-0 rounded-lg overflow-hidden border bg-white flex items-center justify-center">
                                                        <ProductImage src={item.image_url} alt={item.product_name} className="w-full h-full object-contain mix-blend-multiply p-1" />
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-base font-medium leading-tight text-zinc-900 line-clamp-1">{item.product_name}</p>
                                                        <p className="text-lg font-bold text-red-600 mt-1 tabular-nums">{formatVnd(item.price)}</p>
                                                    </div>
                                                    {(() => {
                                                        const style = PLATFORM_MAP[item.platform] || DEFAULT_PLATFORM
                                                        return (
                                                            <div className={`px-2 py-1 flex flex-col items-center justify-center gap-1 rounded-md text-xs font-bold border ${style.bg} ${style.color} ${style.border}`}>
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
                                    <div className="p-6 text-center text-muted-foreground text-lg cursor-pointer hover:bg-zinc-50 transition-colors" onClick={() => handleSearch()}>
                                        <div className="flex items-center justify-center gap-2">
                                            <Search className="h-5 w-5" />
                                            <span>Search for "{query}"</span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                    <Button type="submit" className="h-14 px-10 text-lg font-bold rounded-2xl w-full sm:w-auto">Search</Button>
                </form>

                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                    <p className="text-muted-foreground">
                        {total > 0
                            ? `Found ${total} matching results — showing ${results.length} on page ${page}`
                            : "Start searching to see best deals"}
                    </p>
                    <div className="flex items-center gap-2">
                        <Button
                            type="button"
                            variant={compareOpen ? "default" : "outline"}
                            className="rounded-xl"
                            disabled={!compareEnabled || compareLoading}
                            onClick={() => {
                                if (!compareEnabled) return
                                setCompareOpen((v) => !v)
                                if (!compareData && !compareLoading) runCompare()
                            }}
                        >
                            {compareLoading ? "Comparing..." : "Compare"}
                        </Button>
                        {compareOpen && (
                            <Button type="button" variant="ghost" className="rounded-xl" onClick={() => setCompareOpen(false)}>
                                Hide
                            </Button>
                        )}
                    </div>
                </div>

                {compareOpen && (
                    <div className="rounded-2xl border bg-white p-4 md:p-5 shadow-sm">
                        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
                            <div className="space-y-1">
                                <div className="text-base font-bold">Compare & Recommendation</div>
                                <div className="text-sm text-muted-foreground">
                                    Group similar listings and recommend the best deal (price + discounts + vouchers when available).
                                </div>
                            </div>
                            <Button type="button" variant="outline" className="rounded-xl" disabled={!compareEnabled || compareLoading} onClick={runCompare}>
                                Refresh
                            </Button>
                        </div>

                        {compareError && <div className="mt-3 text-sm text-red-600">{compareError}</div>}

                        {!compareLoading && compareData?.groups?.length ? (
                            <div className="mt-4 space-y-4">
                                {compareData.groups.map((g) => {
                                    const best = g.best_overall
                                    return (
                                        <div key={g.group_key} className="rounded-xl border p-4 bg-white">
                                            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-2">
                                                <div className="min-w-0">
                                                    <div className="font-semibold line-clamp-1">{g.display_name}</div>
                                                    <div className="text-xs text-muted-foreground line-clamp-1">{g.group_key}</div>
                                                </div>
                                                {best ? (
                                                    <div className="flex items-center gap-2">
                                                        <Badge className="bg-green-600 hover:bg-green-700">Best overall</Badge>
                                                        <span className="text-lg font-extrabold text-red-600">
                                                            {formatVnd(best.effective_price ?? best.product.price)}
                                                        </span>
                                                    </div>
                                                ) : null}
                                            </div>

                                            <div className="mt-3 grid grid-cols-1 lg:grid-cols-2 gap-3">
                                                {g.best_by_platform.map((o) => {
                                                    const style = PLATFORM_MAP[o.platform] || PLATFORM_MAP[o.product.platform] || DEFAULT_PLATFORM
                                                    const eff = o.effective_price ?? o.product.price
                                                    return (
                                                        <a
                                                            key={`${g.group_key}-${o.platform}-${o.product.id}`}
                                                            href={o.product.product_url}
                                                            target="_blank"
                                                            rel="noreferrer"
                                                            className="group block rounded-xl border bg-zinc-50/40 hover:bg-zinc-50 transition-colors"
                                                        >
                                                            <div className="flex gap-3 p-3">
                                                                <div className="h-16 w-16 shrink-0 rounded-lg border bg-white flex items-center justify-center overflow-hidden">
                                                                    <ProductImage src={o.product.image_url} alt={o.product.product_name} className="h-full w-full object-contain mix-blend-multiply p-1.5" />
                                                                </div>
                                                                <div className="min-w-0 flex-1">
                                                                    <div className="flex items-center gap-2 flex-wrap">
                                                                        <Badge className={`border ${style.bg} ${style.color} ${style.border}`}>
                                                                            <style.icon className="h-3.5 w-3.5 mr-1" />
                                                                            {o.platform}
                                                                        </Badge>
                                                                        {o.discount_percent ? (
                                                                            <Badge className="bg-red-500 hover:bg-red-600">-{o.discount_percent}%</Badge>
                                                                        ) : null}
                                                                        {o.voucher ? (
                                                                            <Badge className="bg-blue-600 hover:bg-blue-700">Voucher</Badge>
                                                                        ) : null}
                                                                    </div>
                                                                    <div className="mt-1 text-sm font-medium line-clamp-2 text-zinc-800 group-hover:text-zinc-950">
                                                                        {o.product.product_name}
                                                                    </div>
                                                                    <div className="mt-2 flex items-baseline gap-2">
                                                                        <span className="text-lg font-extrabold text-red-600">
                                                                            {formatVnd(eff)}
                                                                        </span>
                                                                        {o.base_price != null && o.base_price > eff ? (
                                                                            <span className="text-sm text-muted-foreground line-through">
                                                                                {formatVnd(o.base_price)}
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
                                    )
                                })}
                            </div>
                        ) : compareLoading ? (
                            <div className="mt-4 space-y-4">
                                <Skeleton className="h-[180px] w-full rounded-xl" />
                                <Skeleton className="h-[180px] w-full rounded-xl" />
                            </div>
                        ) : compareData ? (
                            <div className="mt-4 text-sm text-muted-foreground">No grouped recommendations found.</div>
                        ) : (
                            <div className="mt-4 text-sm text-muted-foreground">Click “Refresh” to generate recommendations for this query.</div>
                        )}
                    </div>
                )}

                {loading ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-4 gap-6">
                        {Array.from({ length: 8 }).map((_, i) => (
                            <Card key={i} className="overflow-hidden border-border/50 flex flex-col h-full">
                                <div className="relative h-[220px] w-full bg-zinc-50 p-6 border-b">
                                    <Skeleton className="w-full h-full rounded-xl bg-zinc-200" />
                                </div>
                                <div className="p-4 flex flex-col flex-1">
                                    <Skeleton className="h-5 w-full mb-2" />
                                    <Skeleton className="h-5 w-2/3 mb-4" />
                                    <div className="mt-auto">
                                        <Skeleton className="h-7 w-1/2 mb-2" />
                                        <Skeleton className="h-4 w-1/3" />
                                    </div>
                                </div>
                            </Card>
                        ))}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-4 gap-6">
                        {results.map((product) => (
                            <Link to={`/products/${product.id}`} key={product.id} className="block group h-full">
                                <Card className="overflow-hidden hover:shadow-xl transition-all duration-300 h-full border-border/50 cursor-pointer flex flex-col group-hover:-translate-y-1 bg-white">
                                    <div className="relative h-[220px] w-full bg-white flex items-center justify-center p-4 border-b group-hover:bg-zinc-50/50 transition-colors">
                                        <ProductImage src={product.image_url} alt={product.product_name} className="w-full h-full object-contain mix-blend-multiply group-hover:scale-105 transition-transform duration-500 ease-out" />
                                        {(product.discount_percent ?? 0) >= 30 ? (
                                            <div className="absolute top-2 right-2 flex items-center gap-1.5 px-2.5 py-1 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-full shadow-lg shadow-red-500/30 animate-pulse pointer-events-none">
                                                <Flame className="w-3.5 h-3.5 fill-current" />
                                                <span className="text-[11px] font-black uppercase tracking-wider">-{product.discount_percent}%</span>
                                            </div>
                                        ) : (product.discount_percent ?? 0) > 0 ? (
                                            <Badge className="absolute top-2 right-2 bg-red-500 hover:bg-red-600 shadow-md border-0 text-[11px] px-2 py-0.5 pointer-events-none">
                                                -{product.discount_percent}%
                                            </Badge>
                                        ) : null}
                                        {(() => {
                                            const style = PLATFORM_MAP[product.platform] || DEFAULT_PLATFORM
                                            return (
                                                <Badge className={`absolute top-2 left-2 shadow-md border-0 flex items-center gap-1 px-2 py-1 ${style.bg} ${style.color} pointer-events-none`}>
                                                    <style.icon className="h-3.5 w-3.5" />
                                                    <span className="font-bold text-[10px] uppercase tracking-wider">{product.platform}</span>
                                                </Badge>
                                            )
                                        })()}
                                    </div>
                                    <div className="flex flex-col flex-1 p-4 bg-zinc-50/30">
                                        <h3 className="text-sm md:text-base line-clamp-2 leading-snug font-semibold text-zinc-900 mb-3 group-hover:text-primary transition-colors">
                                            {product.product_name}
                                        </h3>
                                        <div className="mt-auto flex flex-col gap-1.5">
                                            <span className="text-lg md:text-xl font-extrabold text-red-600 tabular-nums leading-none">
                                                {formatVnd(product.price)}
                                            </span>
                                            <div className="flex items-center gap-2 min-h-[1.25rem]">
                                                {product.original_price != null && product.original_price > product.price && (
                                                    <span className="text-xs text-muted-foreground line-through font-medium">
                                                        {formatVnd(product.original_price)}
                                                    </span>
                                                )}
                                                {typeof product.rating === "number" && product.rating > 0 ? (
                                                    <span className="inline-flex items-center gap-1 text-[11px] text-amber-600 font-bold ml-auto bg-amber-50 px-1.5 py-0.5 rounded-md border border-amber-100">
                                                        <Star className="h-3 w-3 fill-current" />
                                                        {product.rating.toFixed(1)}
                                                        {typeof product.review_count === "number" && product.review_count > 0 ? (
                                                            <span className="font-medium text-amber-600/80">({product.review_count})</span>
                                                        ) : null}
                                                    </span>
                                                ) : null}
                                            </div>
                                        </div>
                                    </div>
                                </Card>
                            </Link>
                        ))}

                        {!loading && results.length === 0 && query && (
                            <div className="col-span-full py-20 text-center">
                                <p className="text-lg text-muted-foreground mb-2">No deals found for "{query}"</p>
                                <p className="text-sm text-muted-foreground">Try adjusting your filters or spelling.</p>
                            </div>
                        )}
                    </div>
                )}

                {total > 0 && (
                    <div className="flex items-center justify-center gap-3 pt-4">
                        <Button
                            type="button"
                            variant="outline"
                            disabled={loading || page <= 1}
                            onClick={() => fetchProducts(query, page - 1)}
                        >
                            Prev
                        </Button>
                        <span className="text-sm text-muted-foreground">
                            Page {page} / {Math.max(1, Math.ceil(total / limit))}
                        </span>
                        <Button
                            type="button"
                            variant="outline"
                            disabled={loading || page >= Math.ceil(total / limit)}
                            onClick={() => fetchProducts(query, page + 1)}
                        >
                            Next
                        </Button>
                    </div>
                )}
            </div>
        </div>
    )
}
