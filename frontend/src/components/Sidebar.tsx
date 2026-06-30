import { LayoutDashboard, FileSpreadsheet, BrainCircuit, Settings, LogOut } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";

const mainMenuItems = [
  { icon: LayoutDashboard, label: "Trang Chủ", path: "/dashboard" },
  { icon: FileSpreadsheet, label: "Làm Sạch Dữ Liệu", path: "/clean" },
  { icon: BrainCircuit, label: "Cập Nhật Tri Thức AI", path: "/knowledge-update" },
];


export function Sidebar({ setToken }: { setToken: (token: string | null) => void }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    navigate('/auth/login');
  };

  return (
    <div className="w-64 h-full flex flex-col bg-sidebar border-r border-sidebar-border shadow-2xl">
      <div className="p-6 flex items-center gap-3 group cursor-pointer transition-transform hover:scale-[1.02]">
        <svg width="36" height="36" viewBox="0 0 120 100" fill="none" xmlns="http://www.w3.org/2000/svg" className="shrink-0 transition-transform duration-300 group-hover:translate-x-1">
          <path d="M10 20 L40 50 L10 80 L25 80 L55 50 L25 20 Z" fill="#00A651" />
          <path d="M40 20 L70 50 L40 80 L55 80 L85 50 L55 20 Z" fill="#00A651" />
          <path d="M70 20 L100 50 L70 80 L85 80 L115 50 L85 20 Z" fill="#00A651" />
        </svg>
        <div className="flex flex-col">
          <span className="text-sidebar-foreground font-bold text-lg leading-tight tracking-tight">HQ Clean</span>
          <span className="text-sidebar-foreground/80 font-medium text-sm leading-tight">Data System</span>
        </div>
      </div>
      <nav className="flex-1 px-3 py-2 space-y-1">
        {mainMenuItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`group flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground font-semibold shadow-sm"
                  : "text-sidebar-foreground/90 hover:bg-sidebar-accent/40 hover:text-sidebar-foreground hover:translate-x-1"
              }`}
            >
              <Icon className={`w-5 h-5 transition-transform duration-200 ${isActive ? 'scale-110' : 'group-hover:scale-110'}`} />
              <span>{item.label}</span>
            </Link>
          );
        })}

      </nav>
      <div className="p-4 border-t border-sidebar-border">
        <button
          onClick={handleLogout}
          className="group flex items-center gap-3 px-3 py-2.5 rounded-lg w-full text-destructive hover:bg-destructive/10 hover:text-destructive transition-all duration-200"
        >
          <LogOut className="w-5 h-5 transition-transform duration-200 group-hover:-translate-x-1" />
          <span className="font-medium">Đăng xuất</span>
        </button>
      </div>
    </div>
  );
}
