import type { Metadata } from "next";
import Link from "next/link";
import { MainNav } from "./main-nav";
import "./globals.css";

export const metadata: Metadata = {
  title: "People & Pay | Salary Management",
  description: "Employee directory and current compensation overview.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <div className="app-shell">
          <aside className="sidebar">
            <Link className="brand" href="/">
              <span className="brand-mark">P</span>
              <span>People<span className="brand-light">&amp;Pay</span></span>
            </Link>
            <p className="nav-label">WORKSPACE</p>
            <MainNav />
            <div className="sidebar-foot"><span className="status-dot" />Salary management<br /><small>HR workspace</small></div>
          </aside>
          <main className="main-area">
            <header className="topbar">
              <div className="topbar-title">People Operations <span>/</span> Salary Management</div>
              <div className="user-chip"><span className="avatar">HR</span><span>HR Manager</span></div>
            </header>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
