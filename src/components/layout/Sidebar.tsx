"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Home", icon: "⌂" },
  { href: "/dashboard/path", label: "My Path", icon: "◎" },
  { href: "/dashboard/library", label: "Library", icon: "◻" },
  { href: "/dashboard/agent-lab", label: "Agent Lab", icon: "⬡" },
  { href: "/dashboard/identity", label: "Identity", icon: "◈" },
  { href: "/dashboard/chat", label: "Chat", icon: "◉" },
  { href: "/dashboard/settings", label: "Settings", icon: "⚙" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`flex flex-col border-r border-(--color-border) bg-(--color-bg-offwhite) transition-all duration-300 ${
        collapsed ? "w-16" : "w-60"
      }`}
    >
      {/* Logo */}
      <div className="flex h-16 items-center border-b border-(--color-border) px-5">
        <Link href="/dashboard" className="font-extrabold tracking-tight text-(--color-ink)">
          {collapsed ? "I" : "IABTM"}
        </Link>
      </div>

      {/* Nav items */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-0.5">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-[14px] font-medium transition-colors ${
                    active
                      ? "bg-(--color-ink) text-white"
                      : "text-(--color-text-secondary) hover:bg-(--color-border-subtle) hover:text-(--color-ink)"
                  }`}
                >
                  <span className="text-base">{item.icon}</span>
                  {!collapsed && <span>{item.label}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed((c) => !c)}
        className="flex h-12 items-center justify-center border-t border-(--color-border) text-(--color-text-tertiary) hover:text-(--color-ink)"
      >
        <span className="text-lg">{collapsed ? "→" : "←"}</span>
      </button>
    </aside>
  );
}
