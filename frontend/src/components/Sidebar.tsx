import { LayoutDashboard, FileSpreadsheet, BookOpen, Wand2, Database, LogOut } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";

const menuItems = [
  { icon: LayoutDashboard, label: "Dashboard", path: "/dashboard" },
  { icon: FileSpreadsheet, label: "Clean Data", path: "/clean" },
  { icon: BookOpen, label: "Dictionary", path: "/dictionary" },
  { icon: Wand2, label: "Dictionary Generator", path: "/dictionary/generate" },
  { icon: Database, label: "HS Taxonomy", path: "/taxonomy" },
];

export function Sidebar({ setToken }: { setToken: (token: string | null) => void }) {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    navigate('/auth/login');
  };

  return (
    <div className="w-64 h-screen bg-sidebar border-r border-sidebar-border flex flex-col">
      <div className="p-6 flex items-center gap-3">
        <svg width="36" height="36" viewBox="0 0 120 100" fill="none" xmlns="http://www.w3.org/2000/svg" className="shrink-0">
          <path d="M10 20 L40 50 L10 80 L25 80 L55 50 L25 20 Z" fill="#00A651" />
          <path d="M40 20 L70 50 L40 80 L55 80 L85 50 L55 20 Z" fill="#00A651" />
          <path d="M70 20 L100 50 L70 80 L85 80 L115 50 L85 20 Z" fill="#00A651" />
        </svg>
        <div className="flex flex-col">
          <span className="text-sidebar-foreground font-bold text-lg leading-tight tracking-tight">Excel Data</span>
          <span className="text-sidebar-foreground/80 font-medium text-sm leading-tight">Cleaner</span>
        </div>
      </div>
      <nav className="flex-1 px-3">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 transition-colors ${
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground hover:bg-sidebar-accent/50"
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="p-3 border-t border-sidebar-border">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg w-full text-destructive hover:bg-destructive/10 transition-colors"
        >
          <LogOut className="w-5 h-5" />
          <span className="font-medium">Logout</span>
        </button>
      </div>
    </div>
  );
}
