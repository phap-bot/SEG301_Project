import type { ReactNode } from "react"

export function ProtectedRoute({ children }: { children: ReactNode }) {
    // Supabase auth was removed; all routes are accessible now.
    return <>{children}</>
}

