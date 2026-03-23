import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { LayoutDashboard } from "lucide-react"
import { useNavigate } from "react-router-dom"

// Supabase auth has been removed; keep this component as a simple dropdown for navigation.
export function UserDropdown() {
    const navigate = useNavigate()
    const userName = localStorage.getItem("user_name") || localStorage.getItem("user_id")

    const handleLogout = () => {
        localStorage.removeItem("user_id")
        localStorage.removeItem("user_name")
        localStorage.removeItem("tracked_products")
        localStorage.removeItem("saved_vouchers")
        navigate("/")
        window.location.reload()
    }

    return (
        <DropdownMenu>
            <DropdownMenuTrigger className="flex items-center gap-2 outline-none text-sm font-bold text-blue-600 hover:text-blue-800 transition-colors cursor-pointer group px-3 py-2 bg-blue-50 hover:bg-blue-100 rounded-full mb-0">
                <span className="truncate max-w-[120px] lg:max-w-[200px]">Hi, {userName}</span>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-64 mt-2 p-2 rounded-xl border border-zinc-200 shadow-xl bg-white">
                <DropdownMenuItem
                    onClick={() => navigate("/dashboard")}
                    className="mb-1 p-3 cursor-pointer rounded-lg hover:bg-zinc-50 outline-none flex items-center w-full"
                >
                    <LayoutDashboard className="mr-3 h-5 w-5 text-zinc-500" />
                    <span className="font-medium">Dashboard & Compare</span>
                </DropdownMenuItem>
                <div className="h-px bg-zinc-100 my-1 mx-2"></div>
                <DropdownMenuItem
                    onClick={handleLogout}
                    className="mb-1 p-3 cursor-pointer rounded-lg hover:bg-red-50 text-red-600 outline-none flex items-center w-full"
                >
                    <span className="font-medium">Logout</span>
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    )
}

