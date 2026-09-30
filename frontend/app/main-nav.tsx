"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function MainNav() {
  const pathname = usePathname();
  return <nav aria-label="Main navigation" className="main-nav">
    <Link href="/" className={`nav-link${pathname === "/" ? " active" : ""}`} aria-current={pathname === "/" ? "page" : undefined}><span className="nav-icon" aria-hidden="true">◫</span>Overview</Link>
    <Link href="/employees" className={`nav-link${pathname.startsWith("/employees") ? " active" : ""}`} aria-current={pathname.startsWith("/employees") ? "page" : undefined}><span className="nav-icon" aria-hidden="true">♙</span>Employees</Link>
  </nav>;
}
