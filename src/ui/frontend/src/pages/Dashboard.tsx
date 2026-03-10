import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { supabase } from "@/lib/supabase"
import type { User } from "@supabase/supabase-js"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LogOut, Activity, ShoppingCart, Heart } from "lucide-react"

export function Dashboard() {
    const [user, setUser] = useState<User | null>(null)
    const navigate = useNavigate()

    useEffect(() => {
        supabase.auth.getUser().then(({ data: { user } }) => {
            if (!user) {
                navigate("/login")
            } else {
                setUser(user)
            }
        })

        const { data: authListener } = supabase.auth.onAuthStateChange(
            (_, session) => {
                if (!session?.user) {
                    navigate("/login")
                } else {
                    setUser(session.user)
                }
            }
        )

        return () => {
            authListener.subscription.unsubscribe()
        }
    }, [navigate])

    const handleLogout = async () => {
        await supabase.auth.signOut()
        navigate("/")
    }

    if (!user) return <div className="p-8 text-center text-muted-foreground">Loading...</div>

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between border-b pb-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
                    <p className="text-muted-foreground">Welcome back, {user.email}</p>
                </div>
                <Button variant="outline" onClick={handleLogout} className="flex gap-2">
                    <LogOut className="h-4 w-4" />
                    Logout
                </Button>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">
                            Total Saved
                        </CardTitle>
                        <Activity className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-green-600">0đ</div>
                        <p className="text-xs text-muted-foreground">
                            +0% from last month
                        </p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">
                            Tracked Products
                        </CardTitle>
                        <Heart className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">0</div>
                        <p className="text-xs text-muted-foreground">
                            Your watchlist is empty
                        </p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Vouchers Used</CardTitle>
                        <ShoppingCart className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">0</div>
                        <p className="text-xs text-muted-foreground">
                            Applied on past purchases
                        </p>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
