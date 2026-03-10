import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { supabase } from "@/lib/supabase"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export function Login() {
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [fullName, setFullName] = useState("")
    const [error, setError] = useState("")
    const [successMessage, setSuccessMessage] = useState("")
    const [loading, setLoading] = useState(false)
    const [activeTab, setActiveTab] = useState("login")
    const navigate = useNavigate()

    const handleAuth = async (isSignUp: boolean) => {
        try {
            setLoading(true)
            setError("")
            setSuccessMessage("")
            let res;
            if (isSignUp) {
                res = await supabase.auth.signUp({
                    email,
                    password,
                    options: {
                        data: {
                            full_name: fullName
                        }
                    }
                })
                if (res.error) throw res.error
                setSuccessMessage("Account created successfully! Please log in.")
                setActiveTab("login")
            } else {
                res = await supabase.auth.signInWithPassword({ email, password })
                if (res.error) throw res.error
                navigate("/dashboard")
            }
        } catch (error: any) {
            setError(error.message || "An error occurred during authentication")
        } finally {
            setLoading(false)
        }
    }

    const oAuthLogin = async (provider: 'google' | 'facebook') => {
        try {
            const { error } = await supabase.auth.signInWithOAuth({
                provider: provider,
                options: {
                    redirectTo: `${window.location.origin}/dashboard`
                }
            })
            if (error) throw error
        } catch (error: any) {
            setError(error.message || `An error occurred during ${provider} authentication`)
        }
    }

    return (
        <div className="flex h-[calc(100vh-14rem)] items-center justify-center pt-10 px-4">
            <Card className="w-full max-w-md border-0 shadow-lg sm:border sm:bg-white rounded-2xl">
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                    <CardHeader className="space-y-1 pb-4">
                        <TabsList className="grid w-full grid-cols-2 mb-4 h-12 rounded-xl bg-zinc-100">
                            <TabsTrigger value="login" className="rounded-lg text-base font-medium">Log in</TabsTrigger>
                            <TabsTrigger value="register" className="rounded-lg text-base font-medium">Sign up</TabsTrigger>
                        </TabsList>

                        <CardTitle className="text-2xl font-bold text-center">Welcome to PriceSaver</CardTitle>
                        <CardDescription className="text-center text-base">
                            The best deals from all over the internet.
                        </CardDescription>
                    </CardHeader>

                    <CardContent className="space-y-6">
                        <TabsContent value="login" className="space-y-4 m-0">
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="login-email">Email</Label>
                                    <Input
                                        id="login-email"
                                        type="email"
                                        placeholder="m@example.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        className="h-12 rounded-xl"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <Label htmlFor="login-password">Password</Label>
                                        <a href="#" className="text-sm font-medium text-primary hover:underline">Forgot password?</a>
                                    </div>
                                    <Input
                                        id="login-password"
                                        type="password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                        className="h-12 rounded-xl"
                                    />
                                </div>
                                {error && <p className="text-sm text-red-500 font-medium text-center">{error}</p>}
                                {successMessage && <p className="text-sm text-green-600 font-medium text-center">{successMessage}</p>}
                                <Button
                                    className="w-full h-12 rounded-xl text-base font-bold shadow-md hover:shadow-lg transition-all"
                                    onClick={() => handleAuth(false)}
                                    disabled={loading || !email || !password}
                                >
                                    {loading ? "Logging in..." : "Log in"}
                                </Button>
                            </div>
                        </TabsContent>

                        <TabsContent value="register" className="space-y-4 m-0">
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="register-fullname">Full Name</Label>
                                    <Input
                                        id="register-fullname"
                                        type="text"
                                        placeholder="John Doe"
                                        value={fullName}
                                        onChange={(e) => setFullName(e.target.value)}
                                        required
                                        className="h-12 rounded-xl"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="register-email">Email</Label>
                                    <Input
                                        id="register-email"
                                        type="email"
                                        placeholder="m@example.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        className="h-12 rounded-xl"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="register-password">Password</Label>
                                    <Input
                                        id="register-password"
                                        type="password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                        className="h-12 rounded-xl"
                                    />
                                </div>
                                {error && <p className="text-sm text-red-500 font-medium text-center">{error}</p>}
                                <Button
                                    className="w-full h-12 rounded-xl text-base font-bold shadow-md hover:shadow-lg transition-all"
                                    onClick={() => handleAuth(true)}
                                    disabled={loading || !email || !password || !fullName}
                                >
                                    {loading ? "Creating account..." : "Sign up"}
                                </Button>

                                <p className="px-8 text-center text-sm text-muted-foreground">
                                    By clicking continue, you agree to our{" "}
                                    <a href="#" className="underline underline-offset-4 hover:text-primary">Terms of Service</a>{" "}
                                    and{" "}
                                    <a href="#" className="underline underline-offset-4 hover:text-primary">Privacy Policy</a>.
                                </p>
                            </div>
                        </TabsContent>

                        <div className="relative">
                            <div className="absolute inset-0 flex items-center">
                                <span className="w-full border-t border-zinc-200" />
                            </div>
                            <div className="relative flex justify-center text-xs uppercase">
                                <span className="bg-white px-2 text-muted-foreground font-medium">
                                    Or continue with
                                </span>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <Button
                                variant="outline"
                                className="h-12 rounded-xl border-zinc-200 hover:bg-zinc-50 font-semibold"
                                onClick={() => oAuthLogin('google')}
                                type="button"
                            >
                                <svg className="mr-2 h-4 w-4" aria-hidden="true" focusable="false" data-prefix="fab" data-icon="google" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 488 512">
                                    <path fill="currentColor" d="M488 261.8C488 403.3 391.1 504 248 504 110.8 504 0 393.2 0 256S110.8 8 248 8c66.8 0 123 24.5 166.3 64.9l-67.5 64.9C258.5 52.6 94.3 116.6 94.3 256c0 86.5 69.1 156.6 153.7 156.6 98.2 0 135-70.4 140.8-106.9H248v-85.3h236.1c2.3 12.7 3.9 24.9 3.9 41.4z"></path>
                                </svg>
                                Google
                            </Button>
                            <Button
                                variant="outline"
                                className="h-12 rounded-xl hover:bg-[#1877F2]/10 hover:text-[#1877F2] font-semibold"
                                onClick={() => oAuthLogin('facebook')}
                                type="button"
                            >
                                <svg className="mr-2 h-5 w-5 fill-[#1877F2]" aria-hidden="true" focusable="false" data-prefix="fab" data-icon="facebook" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
                                    <path fill="currentColor" d="M504 256C504 119 393 8 256 8S8 119 8 256c0 123.78 90.69 226.38 209.25 245V327.69h-63V256h63v-54.64c0-62.15 37-96.48 93.67-96.48 27.14 0 55.52 4.84 55.52 4.84v61h-31.28c-30.8 0-40.41 19.12-40.41 38.73V256h68.78l-11 71.69h-57.78V501C413.31 482.38 504 379.78 504 256z"></path>
                                </svg>
                                Facebook
                            </Button>
                        </div>
                    </CardContent>
                </Tabs>
            </Card>
        </div>
    )
}
