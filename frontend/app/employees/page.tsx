"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiRequest, formatCount } from "../../lib/api";
import type { EmployeeList } from "../../lib/types";

export default function EmployeesPage() {
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState({ country: "", department: "", job_title: "" });
  const [page, setPage] = useState(1);
  const [data, setData] = useState<EmployeeList | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      const params = new URLSearchParams({ page: String(page), page_size: "25" });
      if (search.trim()) params.set("search", search.trim());
      Object.entries(filters).forEach(([key, value]) => { if (value.trim()) params.set(key, value.trim()); });
      setLoading(true);
      setError(null);
      apiRequest<EmployeeList>(`/api/v1/employees?${params.toString()}`, { signal: controller.signal })
        .then((result) => { setData(result); setLoading(false); })
        .catch((reason: unknown) => {
          if (controller.signal.aborted) return;
          setError(reason instanceof Error ? reason.message : "Unable to load employees.");
          setLoading(false);
        });
    }, 180);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [search, filters, page]);

  function changeFilter(key: keyof typeof filters, value: string) {
    setFilters((current) => ({ ...current, [key]: value }));
    setPage(1);
  }
  function clearFilters() { setSearch(""); setFilters({ country: "", department: "", job_title: "" }); setPage(1); }
  const pagination = data?.pagination;
  const first = pagination && pagination.total ? (pagination.page - 1) * pagination.page_size + 1 : 0;
  const last = pagination ? Math.min(pagination.page * pagination.page_size, pagination.total) : 0;

  return <div className="content">
    <div className="page-heading"><div><p className="eyebrow">PEOPLE</p><h1>Employee directory</h1><p className="subtitle">Search and explore your organization.</p></div></div>
    <section className="panel directory-panel">
      <div className="filter-grid">
        <label className="search-field"><span>Search employees</span><div className="input-with-icon"><span aria-hidden="true">⌕</span><input aria-label="Search employees" placeholder="Name, email or employee code" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} /></div></label>
        <label><span>Country code</span><input placeholder="e.g. US" value={filters.country} onChange={(event) => changeFilter("country", event.target.value)} /></label>
        <label><span>Department</span><input placeholder="Exact department" value={filters.department} onChange={(event) => changeFilter("department", event.target.value)} /></label>
        <label><span>Job title</span><input placeholder="Exact job title" value={filters.job_title} onChange={(event) => changeFilter("job_title", event.target.value)} /></label>
        <button className="button button-quiet clear-button" onClick={clearFilters} type="button">Clear filters</button>
      </div>
      <div className="results-bar"><div>{loading ? "Updating results…" : pagination ? <><strong>{formatCount(pagination.total)}</strong> employee{pagination.total === 1 ? "" : "s"} <span className="muted">· Showing {first}–{last}</span></> : "Employee results"}</div><span className="results-caption">Search and filters run against the directory</span></div>
      {error && <div className="alert alert-error" role="alert"><strong>Couldn’t load employees</strong><span>{error}</span></div>}
      {loading && <div className="loading-card compact"><span className="spinner" />Loading employees…</div>}
      {!loading && !error && data && data.items.length === 0 && <div className="empty-state"><span className="empty-mark">⌕</span><h2>No employees found</h2><p>Try another search or clear the current filters.</p><button className="button button-secondary" type="button" onClick={clearFilters}>Clear filters</button></div>}
      {!loading && !error && data && data.items.length > 0 && <>
        <div className="table-wrap directory-table"><table><thead><tr><th>Employee</th><th>Employee code</th><th>Department</th><th>Job title</th><th>Country</th><th></th></tr></thead><tbody>
          {data.items.map((employee) => <tr key={employee.id}><td><Link className="employee-cell" href={`/employees/${employee.id}`}><span className="person-avatar">{employee.first_name[0]}{employee.last_name[0]}</span><span><strong>{employee.first_name} {employee.last_name}</strong><small>{employee.email}</small></span></Link></td><td className="code-cell">{employee.employee_code}</td><td>{employee.department}</td><td>{employee.job_title}</td><td><span className="country-pill">{employee.country}</span></td><td><Link className="row-link" href={`/employees/${employee.id}`} aria-label={`View ${employee.first_name} ${employee.last_name}`}>View <span aria-hidden="true">→</span></Link></td></tr>)}
        </tbody></table></div>
        <div className="pagination"><span>Page <strong>{pagination?.page}</strong> of <strong>{pagination?.total_pages || 1}</strong></span><div className="pagination-actions"><button className="button button-secondary" type="button" disabled={!pagination || page <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))}>← Previous</button><button className="button button-secondary" type="button" disabled={!pagination || page >= pagination.total_pages} onClick={() => setPage((value) => value + 1)}>Next →</button></div></div>
      </>}
    </section>
    <footer className="page-foot">Select an employee to view their details and current compensation.</footer>
  </div>;
}
