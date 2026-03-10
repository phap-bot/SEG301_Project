import { MonitorPlay, Smartphone, ShoppingCart, ShoppingBag, Store, Package } from "lucide-react"
import React from "react"

export interface PlatformStyle {
    name: string
    color: string
    bg: string
    border: string
    icon: React.ElementType
    shortAppLogo: string
}

export const PLATFORM_MAP: Record<string, PlatformStyle> = {
    "Điện Máy Xanh": {
        name: "Điện Máy Xanh",
        color: "text-[#008de6]",
        bg: "bg-[#008de6]/10",
        border: "border-[#008de6]/20",
        icon: MonitorPlay,
        shortAppLogo: "ĐMX"
    },
    "CellphoneS": {
        name: "CellphoneS",
        color: "text-[#d70018]",
        bg: "bg-[#d70018]/10",
        border: "border-[#d70018]/20",
        icon: Smartphone,
        shortAppLogo: "CPS"
    },
    "Lazada": {
        name: "Lazada",
        color: "text-[#0f146d]",
        bg: "bg-[#0f146d]/10",
        border: "border-[#0f146d]/20",
        icon: ShoppingCart,
        shortAppLogo: "LAZ"
    },
    "Tiki": {
        name: "Tiki",
        color: "text-[#1a94ff]",
        bg: "bg-[#1a94ff]/10",
        border: "border-[#1a94ff]/20",
        icon: ShoppingBag,
        shortAppLogo: "TIKI"
    },
    "Chợ Tốt": {
        name: "Chợ Tốt",
        color: "text-[#ffb600]",
        bg: "bg-[#ffb600]/10",
        border: "border-[#ffb600]/20",
        icon: Store,
        shortAppLogo: "CTOT"
    },
    "FPT Shop": {
        name: "FPT Shop",
        color: "text-[#cd1818]",
        bg: "bg-[#cd1818]/10",
        border: "border-[#cd1818]/20",
        icon: Package,
        shortAppLogo: "FPT"
    }
}

// Default fallback for any unknown platforms
export const DEFAULT_PLATFORM: PlatformStyle = {
    name: "Unknown",
    color: "text-zinc-600",
    bg: "bg-zinc-100",
    border: "border-zinc-200",
    icon: ShoppingBag,
    shortAppLogo: "UNK"
}
