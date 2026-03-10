import { Link } from "react-router-dom"
import { ShoppingBag } from "lucide-react"
import { useEffect, useState } from "react"
import { supabase } from "@/lib/supabase"
import type { User } from "@supabase/supabase-js"
import { UserDropdown } from "./UserDropdown"

export function Navbar() {
    const [user, setUser] = useState<User | null>(null)

    useEffect(() => {
        supabase.auth.getSession().then(({ data: { session } }) => {
            setUser(session?.user ?? null)
        })

        const { data: authListener } = supabase.auth.onAuthStateChange((_event, session) => {
            setUser(session?.user ?? null)
        })

        return () => {
            authListener.subscription.unsubscribe()
        }
    }, [])
    return (
        <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="max-w-7xl mx-auto flex h-16 items-center justify-between px-4 md:px-8 w-full">
                <div className="flex gap-6 md:gap-10">
                    <Link to="/" className="flex items-center space-x-2">
                        <ShoppingBag className="h-6 w-6 text-primary" />
                        <span className="inline-block font-bold text-2xl">
                            PriceSaver
                        </span>
                    </Link>
                    <nav className="hidden md:flex gap-6">
                        <Link
                            to="/products"
                            className="flex items-center text-base font-medium text-muted-foreground transition-colors hover:text-foreground"
                        >
                            All Products
                        </Link>
                        <Link
                            to="/deals"
                            className="flex items-center text-base font-medium text-muted-foreground transition-colors hover:text-foreground"
                        >
                            Best Deals
                        </Link>
                    </nav>
                </div>
                <div className="flex flex-1 items-center justify-end space-x-4">
                    <div className="w-full flex-1 md:w-auto md:flex-none" />
                    <nav className="flex items-center gap-2">
                        {user ? (
                            <UserDropdown user={user} />
                        ) : (
                            <Link
                                to="/login"
                                className="text-base font-medium bg-primary text-primary-foreground px-4 py-2 rounded-md transition-colors hover:bg-primary/90"
                            >
                                Login to Dashboard
                            </Link>
                        )}
                    </nav>
                </div>
            </div>
        </header>
    )
}
