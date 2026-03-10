import { useState, useEffect, useRef } from "react"
import { useSearchParams, Link } from "react-router-dom"
import { Search, Filter } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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
}

const PLATFORMS = ["Điện Máy Xanh", "CellphoneS", "Lazada", "Tiki", "Chợ Tốt", "FPT Shop"]

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

    // Filters
    const [minPrice, setMinPrice] = useState("")
    const [maxPrice, setMaxPrice] = useState("")
    const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([])

    const fetchProducts = async (currentQuery = query) => {
        if (!currentQuery.trim()) {
            setResults([])
            setTotal(0)
            return
        }

        setLoading(true)
        try {
            const url = new URL(`${import.meta.env.VITE_API_URL}/api/v1/search`)
            url.searchParams.append("query", currentQuery)
            url.searchParams.append("limit", "20")
            if (minPrice) url.searchParams.append("min_price", minPrice)
            if (maxPrice) url.searchParams.append("max_price", maxPrice)
            selectedPlatforms.forEach(p => url.searchParams.append("platforms", p))

            const res = await fetch(url.toString())
            if (!res.ok) throw new Error("Failed to fetch products")
            const data = await res.json()

            setResults(data.results || [])
            setTotal(data.total_results || 0)
        } catch (error) {
            console.error(error)
        } finally {
            setLoading(false)
        }
    }

    // Trigger search on mount if query exists in URL
    useEffect(() => {
        if (initialQuery) {
            fetchProducts(initialQuery)
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
        fetchProducts()
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
            <aside className="w-full md:w-64 space-y-6">
                <div>
                    <h3 className="text-xl font-bold flex items-center gap-2 mb-4">
                        <Filter className="h-6 w-6" />
                        Filters
                    </h3>

                    <div className="space-y-4">
                        <div>
                            <h4 className="font-medium mb-3 text-base text-muted-foreground">Platforms</h4>
                            <div className="flex flex-col gap-3 items-start w-full">
                                {PLATFORMS.map(platform => {
                                    const style = PLATFORM_MAP[platform] || DEFAULT_PLATFORM
                                    const isSelected = selectedPlatforms.includes(platform)
                                    return (
                                        <button
                                            key={platform}
                                            className={`w-full flex items-center justify-start gap-3 px-4 py-3 rounded-xl border text-base font-medium transition-all ${isSelected
                                                ? `${style.bg} ${style.color} ${style.border} ring-1 ring-current`
                                                : 'bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-50 hover:border-zinc-300'
                                                }`}
                                            onClick={() => togglePlatform(platform)}
                                            type="button"
                                        >
                                            <style.icon className="h-5 w-5" />
                                            {platform}
                                        </button>
                                    )
                                })}
                            </div>
                        </div>

                        <div>
                            <h4 className="font-medium mb-3 text-base text-muted-foreground">Price Range (VND)</h4>
                            <div className="flex items-center gap-3">
                                <Input
                                    type="number"
                                    placeholder="Min"
                                    value={minPrice}
                                    onChange={e => setMinPrice(e.target.value)}
                                    className="h-12 text-base rounded-xl"
                                />
                                <span className="text-muted-foreground font-medium">-</span>
                                <Input
                                    type="number"
                                    placeholder="Max"
                                    value={maxPrice}
                                    onChange={e => setMaxPrice(e.target.value)}
                                    className="h-12 text-base rounded-xl"
                                />
                            </div>
                        </div>

                        <Button className="w-full h-12 text-base rounded-xl font-bold mt-2" onClick={() => handleSearch()}>
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
                                                    {item.image_url ? (
                                                        <img src={item.image_url} alt={item.product_name} className="w-14 h-14 object-contain mix-blend-multiply" />
                                                    ) : (
                                                        <div className="w-14 h-14 bg-zinc-100 rounded-lg flex items-center justify-center text-xs text-muted-foreground border">No img</div>
                                                    )}
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-base font-medium leading-tight text-zinc-900 line-clamp-1">{item.product_name}</p>
                                                        <p className="text-lg font-bold text-red-600 mt-1">{item.price.toLocaleString("vi-VN")}đ</p>
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

                <div className="flex items-center justify-between text-muted-foreground">
                    <p>{total > 0 ? `Found ${total} matching results` : "Start searching to see best deals"}</p>
                </div>

                {loading ? (
                    <div className="py-20 text-center text-muted-foreground animate-pulse">
                        Analyzing prices across platforms...
                    </div>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
                        {results.map((product) => (
                            <Link to={`/products/${product.id}`} key={product.id} className="block group">
                                <Card className="overflow-hidden hover:shadow-lg transition-shadow h-full border-border/50 cursor-pointer">
                                    <div className="relative h-48 w-full bg-zinc-50 flex items-center justify-center p-4">
                                        {product.image_url ? (
                                            <img
                                                src={product.image_url}
                                                alt={product.product_name}
                                                className="max-h-full object-contain group-hover:scale-105 transition-transform mix-blend-multiply"
                                            />
                                        ) : (
                                            <div className="text-muted-foreground">No image</div>
                                        )}
                                        {product.discount_percent && product.discount_percent > 0 && (
                                            <Badge className="absolute top-3 right-3 bg-red-500 hover:bg-red-600">
                                                -{product.discount_percent}%
                                            </Badge>
                                        )}
                                        {(() => {
                                            const style = PLATFORM_MAP[product.platform] || DEFAULT_PLATFORM
                                            return (
                                                <Badge className={`absolute top-3 left-3 shadow-sm border flex items-center gap-1.5 ${style.bg} ${style.color} ${style.border} hover:${style.bg}`}>
                                                    <style.icon className="h-3.5 w-3.5" />
                                                    <span className="font-bold tracking-wide">{product.platform}</span>
                                                </Badge>
                                            )
                                        })()}
                                    </div>
                                    <CardHeader className="p-4 pb-2">
                                        <CardTitle className="text-lg line-clamp-2 leading-snug font-medium text-zinc-800">
                                            {product.product_name}
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent className="px-4 pb-4">
                                        <div className="flex flex-col gap-1 mt-2">
                                            <span className="text-2xl font-bold text-red-600">
                                                {product.price.toLocaleString("vi-VN")}đ
                                            </span>
                                            {product.original_price && product.original_price > product.price && (
                                                <span className="text-sm text-muted-foreground line-through">
                                                    {product.original_price.toLocaleString("vi-VN")}đ
                                                </span>
                                            )}
                                        </div>
                                    </CardContent>
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
            </div>
        </div>
    )
}
