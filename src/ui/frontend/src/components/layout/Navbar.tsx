import { Link } from "react-router-dom"
import { ShoppingBag } from "lucide-react"
import { UserDropdown } from "./UserDropdown"
import { useEffect, useState } from "react"

export function Navbar() {
    const [userId, setUserId] = useState<string | null>(null)

    useEffect(() => {
        setUserId(localStorage.getItem("user_id"))
    }, [])

    return (
        <header className="sticky top-0 z-50 w-full border-b border-zinc-200/60 bg-white/80 backdrop-blur-xl transition-all shadow-sm">
            <div className="max-w-7xl mx-auto flex h-[72px] items-center justify-between px-4 md:px-8 w-full">
                <div className="flex gap-8 md:gap-12 items-center">
                    <Link to="/" className="flex items-center space-x-2.5 group">
                        <div className="p-2 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl group-hover:scale-105 transition-transform shadow-md shadow-blue-500/20">
                            <ShoppingBag className="h-5 w-5 text-white" strokeWidth={2.5} />
                        </div>
                        <span className="inline-block font-extrabold text-2xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-zinc-900 to-zinc-600">PriceSaver</span>
                    </Link>
                    <nav className="hidden md:flex gap-8">
                        <Link
                            to="/products"
                            className="relative flex items-center text-sm font-bold text-zinc-500 transition-colors hover:text-zinc-900 group h-full"
                        >
                            All Products
                            <span className="absolute -bottom-[26px] left-0 w-full h-[3px] bg-indigo-600 scale-x-0 group-hover:scale-x-100 transition-transform origin-left rounded-t-full" />
                        </Link>
                        <Link
                            to="/deals"
                            className="relative flex items-center text-sm font-bold text-zinc-500 transition-colors hover:text-zinc-900 group h-full"
                        >
                            Best Deals
                            <span className="absolute -bottom-[26px] left-0 w-full h-[3px] bg-indigo-600 scale-x-0 group-hover:scale-x-100 transition-transform origin-left rounded-t-full" />
                        </Link>
                    </nav>
                </div>
                <div className="flex flex-1 items-center justify-end space-x-4">
                    <nav className="flex items-center gap-2">
                        {userId ? (
                            <UserDropdown />
                        ) : (
                            <Link
                                to="/login"
                                className="text-sm font-bold bg-zinc-900 text-white px-6 py-2.5 rounded-full transition-all hover:bg-zinc-800 hover:scale-105 shadow-md"
                            >
                                Sign In
                            </Link>
                        )}
                    </nav>
                </div>
            </div>
        </header>
    )
}

