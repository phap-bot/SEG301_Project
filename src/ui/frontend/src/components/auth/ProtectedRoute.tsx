import { useEffect, useState } from "react"
import { Navigate, useLocation } from "react-router-dom"
import { supabase } from "@/lib/supabase"
import type { User } from "@supabase/supabase-js"

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null)
    const [loading, setLoading] = useState(true)
    const location = useLocation()

    useEffect(() => {
        supabase.auth.getSession().then(({ data: { session } }) => {
            setUser(session?.user ?? null)
            setLoading(false)
        })

        const { data: authListener } = supabase.auth.onAuthStateChange((_event, session) => {
            setUser(session?.user ?? null)
            setLoading(false)
        })

        return () => {
            authListener.subscription.unsubscribe()
        }
    }, [])

    if (loading) {
        return <div className="min-h-screen flex items-center justify-center">Loading...</div>
    }

    if (!user) {
        return <Navigate to="/login" state={{ from: location }} replace />
    }

    return <>{children}</>
}
