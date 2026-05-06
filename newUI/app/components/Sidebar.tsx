import { LayoutDashboard, FileSpreadsheet, BookOpen, Wand2 } from "lucide-react";
import { Link, useLocation } from "react-router";

const menuItems = [
  { icon: LayoutDashboard, label: "Dashboard", path: "/" },
  { icon: FileSpreadsheet, label: "Clean Data", path: "/clean-data" },
  { icon: BookOpen, label: "Dictionary", path: "/dictionary" },
  { icon: Wand2, label: "Dictionary Generator", path: "/dictionary-generator" },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <div className="w-64 h-screen bg-sidebar border-r border-sidebar-border flex flex-col">
      <div className="p-6">
        <h1 className="text-sidebar-foreground">Excel Data Cleaner</h1>
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
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
