import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Eye, EyeOff, Loader2, AlertCircle, TrendingUp } from "lucide-react"

export function Login() {
    const navigate = useNavigate()
    const [isLogin, setIsLogin] = useState(true)
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [showPassword, setShowPassword] = useState(false)
    const [error, setError] = useState("")
    const [loading, setLoading] = useState(false)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError("")
        if (!email.trim() || !password.trim()) {
            setError("Email and password are required")
            return
        }

        setLoading(true)
        try {
            const endpoint = isLogin ? "/api/v1/auth/login" : "/api/v1/auth/signup"
            const res = await fetch(`${import.meta.env.VITE_API_URL}${endpoint}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: email.trim(), password })
            })
            
            const data = await res.json()
            if (!res.ok) {
                setError(data.detail || "Authentication failed")
            } else {
                localStorage.removeItem("tracked_products")
                localStorage.removeItem("saved_vouchers")
                localStorage.setItem("user_id", data.user_id)
                localStorage.setItem("user_name", data.name)
                
                navigate("/dashboard")
                window.location.reload()
            }
        } catch (err) {
            setError("Network error. Make sure your backend API is running.")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-[calc(100vh-4rem)] w-full lg:grid lg:grid-cols-2 bg-white">
            {/* Left Box - Authentication Form */}
            <div className="flex flex-col justify-center items-center px-6 py-12 lg:px-8">
                <div className="w-full max-w-[400px] flex flex-col justify-center space-y-8">
                    <div className="flex flex-col space-y-2 text-center lg:text-left">
                        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">
                            {isLogin ? "Sign in to account" : "Create an account"}
                        </h1>
                        <p className="text-sm text-zinc-500">
                            {isLogin 
                                ? "Enter your email and password below to sign in." 
                                : "Enter your details below to start saving on top deals."}
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-5">
                        {error && (
                            <div className="p-3 text-sm font-medium text-red-600 bg-red-50 rounded-md border border-red-100 flex items-center gap-2">
                                <AlertCircle className="h-4 w-4 shrink-0" />
                                {error}
                            </div>
                        )}
                        
                        <div className="space-y-2">
                            <Label htmlFor="email" className="text-zinc-700">Email Address</Label>
                            <Input
                                id="email"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="name@example.com"
                                className="h-11 rounded-md border-zinc-300 focus:border-zinc-900 focus:ring-zinc-900 transition-colors"
                                required
                            />
                        </div>
                        
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <Label htmlFor="password" className="text-zinc-700">Password</Label>
                                {isLogin && (
                                    <button type="button" className="text-sm text-zinc-500 hover:text-zinc-900 font-medium">
                                        Forgot password?
                                    </button>
                                )}
                            </div>
                            <div className="relative">
                                <Input
                                    id="password"
                                    type={showPassword ? "text" : "password"}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="Enter your password"
                                    className="h-11 rounded-md border-zinc-300 focus:border-zinc-900 focus:ring-zinc-900 transition-colors pr-10"
                                    required
                                    minLength={6}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-700 outline-none"
                                >
                                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                </button>
                            </div>
                        </div>
                        
                        <Button
                            type="submit"
                            disabled={loading}
                            className="w-full h-11 bg-zinc-900 hover:bg-zinc-800 text-white rounded-md font-medium transition-all"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Please wait
                                </>
                            ) : (
                                isLogin ? "Sign In" : "Sign Up"
                            )}
                        </Button>
                    </form>

                    <div className="text-center text-sm text-zinc-500">
                        {isLogin ? "Don't have an account? " : "Already have an account? "}
                        <button
                            type="button"
                            onClick={() => {
                                setIsLogin(!isLogin)
                                setError("")
                            }}
                            className="text-zinc-900 font-semibold hover:underline underline-offset-4"
                        >
                            {isLogin ? "Sign up" : "Sign in"}
                        </button>
                    </div>
                </div>
            </div>

            {/* Right Box - Aesthetic Branding */}
            <div className="hidden lg:flex relative w-full h-full bg-zinc-900 flex-col justify-between p-12 text-white overflow-hidden">
                <div className="absolute inset-0 max-w-full h-full overflow-hidden opacity-20 pointer-events-none">
                    {/* Abstract background styling to match professional SaaS */}
                    <svg className="absolute left-0 top-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                        <polygon points="0,100 100,0 100,100" fill="currentColor" className="text-zinc-800" />
                    </svg>
                </div>
                
                <div className="relative z-10">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="h-8 w-8 bg-blue-600 rounded-md flex items-center justify-center shadow-sm">
                            <TrendingUp className="h-5 w-5 text-white" />
                        </div>
                        <span className="text-2xl font-bold tracking-tight">PriceSaver</span>
                    </div>
                    <p className="text-zinc-400 text-lg font-medium">The intelligent deal tracker.</p>
                </div>

                <div className="relative z-10 max-w-lg mt-auto">
                    <blockquote className="space-y-4">
                        <p className="text-2xl font-medium leading-snug">
                            "Thanks to PriceSaver's automated vouchers and tracking, our team easily sourced office supplies at historically lowest prices."
                        </p>
                        <footer className="text-sm text-zinc-400">
                            Your are the best with buyer
                        </footer>
                    </blockquote>
                </div>
            </div>
        </div>
    )
}
