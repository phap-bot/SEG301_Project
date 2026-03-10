import { Package, Heart, Star, XCircle, Smile } from "lucide-react"

export function PlaceholderPage({ title, description, icon: Icon }: { title: string, description: string, icon: any }) {
    return (
        <div className="flex flex-col items-center justify-center min-h-[50vh] text-center space-y-4 px-4">
            <div className="bg-primary/10 p-5 rounded-full mb-2">
                <Icon className="h-10 w-10 text-primary" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
            <p className="text-muted-foreground max-w-md text-lg">
                {description}
            </p>
            <div className="pt-4 text-sm text-zinc-500 bg-zinc-50 px-4 py-2 rounded-lg border">
                Giao diện basic chờ phát triển - Flexible modular setup
            </div>
        </div>
    )
}

export function ProfilePage() { return <PlaceholderPage title="Quản lý tài khoản" description="Cập nhật thông tin cá nhân, định danh, sổ địa chỉ và độ bảo mật của bạn tại đây." icon={Smile} /> }
export function OrdersPage() { return <PlaceholderPage title="Đơn hàng của tôi" description="Theo dõi trạng thái, lịch sử tất cả các đơn hàng bạn đã mua trên các nền tảng." icon={Package} /> }
export function WishlistPage() { return <PlaceholderPage title="Danh sách yêu thích" description="Quản lý các sản phẩm bạn đang theo dõi giá và nhận thông báo khi có flash sale." icon={Heart} /> }
export function ReviewsPage() { return <PlaceholderPage title="Nhận xét của tôi" description="Xem lại các đánh giá, bình luận bạn đã để lại cho các sản phẩm đã mua." icon={Star} /> }
export function ReturnsPage() { return <PlaceholderPage title="Đổi trả & Hủy đơn" description="Tra cứu trạng thái hoàn tiền và quản lý các đơn muốn đổi trả." icon={XCircle} /> }
