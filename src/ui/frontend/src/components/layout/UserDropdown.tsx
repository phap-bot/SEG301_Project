import { useNavigate } from "react-router-dom"
import { supabase } from "@/lib/supabase"
import type { User } from "@supabase/supabase-js"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Smile, Package, Heart, Star, XCircle, LogOut, ChevronDown } from "lucide-react"

export function UserDropdown({ user }: { user: User }) {
    const navigate = useNavigate()

    const handleLogout = async () => {
        await supabase.auth.signOut()
        navigate("/login")
    }

    return (
        <DropdownMenu>
            <DropdownMenuTrigger className="flex items-center gap-2 outline-none text-sm font-medium hover:text-primary transition-colors cursor-pointer group px-2 py-1 rounded-md mb-0">
                <span className="truncate max-w-[120px] lg:max-w-[200px]">
                    {user.user_metadata?.full_name || user.email?.split("@")[0] || "Account"}
                </span>
                <ChevronDown className="h-4 w-4 opacity-70 group-hover:opacity-100 transition-transform group-data-[state=open]:rotate-180" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-64 mt-2 p-2 rounded-xl border border-zinc-200 shadow-xl bg-white">
                <DropdownMenuItem onClick={() => navigate("/profile")} className="mb-1 p-3 cursor-pointer rounded-lg hover:bg-zinc-50 outline-none flex items-center w-full">
                    <Smile className="mr-3 h-5 w-5 text-zinc-500" />
                    <span className="font-medium">Quản lý tài khoản</span>
                </DropdownMenuItem>

                <DropdownMenuItem onClick={() => navigate("/orders")} className="mb-1 p-3 cursor-pointer rounded-lg hover:bg-zinc-50 outline-none flex items-center w-full">
                    <Package className="mr-3 h-5 w-5 text-zinc-500" />
                    <span className="font-medium">Đơn hàng của tôi</span>
                </DropdownMenuItem>

                <DropdownMenuItem onClick={() => navigate("/wishlist")} className="mb-1 p-3 cursor-pointer rounded-lg hover:bg-zinc-50 outline-none flex items-center w-full">
                    <Heart className="mr-3 h-5 w-5 text-zinc-500" />
                    <span className="font-medium">Danh sách yêu thích & Theo dõi</span>
                </DropdownMenuItem>

                <DropdownMenuItem onClick={() => navigate("/reviews")} className="mb-1 p-3 cursor-pointer rounded-lg hover:bg-zinc-50 outline-none flex items-center w-full">
                    <Star className="mr-3 h-5 w-5 text-zinc-500" />
                    <span className="font-medium">Nhận xét của tôi</span>
                </DropdownMenuItem>

                <DropdownMenuItem onClick={() => navigate("/returns")} className="mb-1 p-3 cursor-pointer rounded-lg hover:bg-zinc-50 outline-none flex items-center w-full">
                    <XCircle className="mr-3 h-5 w-5 text-zinc-500" />
                    <span className="font-medium">Quản lý đơn hàng và đổi trả</span>
                </DropdownMenuItem>

                <DropdownMenuSeparator className="h-px bg-zinc-200 my-2" />

                <DropdownMenuItem onClick={handleLogout} className="p-3 cursor-pointer rounded-lg hover:bg-red-50 hover:text-red-700 outline-none focus:bg-red-50 focus:text-red-700">
                    <LogOut className="mr-3 h-5 w-5 opacity-70" />
                    <span className="font-medium">Đăng xuất</span>
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    )
}
