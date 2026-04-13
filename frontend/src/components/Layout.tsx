import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/positions", label: "岗位管理", icon: "📋" },
  { to: "/settings", label: "系统设置", icon: "⚙️" },
];

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <aside className="w-56 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-5 border-b border-gray-200">
          <h1 className="text-lg font-bold text-gray-900">面试助手</h1>
          <p className="text-xs text-gray-500 mt-1">Interview Assistant</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`
              }
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-gray-200 text-xs text-gray-400 text-center">
          v0.3.0
        </div>
      </aside>
      <main className="flex-1 p-6 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
