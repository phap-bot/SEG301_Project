import type { ReactNode } from "react"
import { Navbar } from "./Navbar"

export function Layout({ children }: { children: ReactNode }) {
    return (
        <div className="min-h-screen bg-background font-sans antialiased">
            <Navbar />
            <main className="max-w-7xl mx-auto px-4 md:px-8 py-8 w-full">
                {children}
            </main>
            <footer className="border-t py-6 mt-12 text-center text-sm text-muted-foreground">
                <p>© {new Date().getFullYear()} PriceSaver. All rights reserved.</p>
            </footer>
        </div>
    )
}
