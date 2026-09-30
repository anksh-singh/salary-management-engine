"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiRequest, formatCount } from "../lib/api";
import type { Insights } from "../lib/types";

function MoneyTable({ rows }: { rows: Insights["salary_by_currency"] }) {
  if (!rows.length) return <p className="table-empty">No current compensation recorded yet.</p>;
  return <div className="table-wrap"><table><thead><tr><th>Currency</th><th>People</th><th>Average</th><th>Median</th><th>Range</th></tr></thead><tbody>
    {rows.map((row) => <tr key={row.currency}><td><span className="currency-pill">{row.currency}</span></td><td>{formatCount(row.employee_count)}</td><td>{row.average_amount}</td><td>{row.median_amount}</td><td>{row.minimum_amount} – {row.maximum_amount}</td></tr>)}
  </tbody></table></div>;
}

function Breakdown({ title, rows, label }: { title: string; rows: { name: string; count: number; covered: number }[]; label: string }) {
  return <section className="panel"><div className="panel-heading"><div><p className="eyebrow">EMPLOYEE MIX</p><h2>{title}</h2></div></div>
    {rows.length ? <div className="table-wrap"><table><thead><tr><th>{label}</th><th>Employees</th><th>Compensated</th></tr></thead><tbody>{rows.map((row) => <tr key={row.name}><td className="strong-cell">{row.name}</td><td>{formatCount(row.count)}</td><td>{formatCount(row.covered)}</td></tr>)}</tbody></table></div> : <p className="table-empty">No employees yet.</p>}
  </section>;
}

export default function DashboardPage() {
  const [data, setData] = useState<Insights | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { apiRequest<Insights>("/api/v1/insights/compensation").then(setData).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Unable to load insights.")); }, []);

  return <div className="content">
    <div className="page-heading"><div><p className="eyebrow">OVERVIEW</p><h1>Compensation insights</h1><p className="subtitle">A clear view of your workforce and current annual base pay.</p></div><Link className="button button-primary" href="/employees">Browse employees <span aria-hidden="true">→</span></Link></div>
    {error && <div className="alert alert-error" role="alert"><strong>Insights unavailable</strong><span>{error}</span></div>}
    {!data && !error && <div className="loading-card"><span className="spinner" />Loading compensation insights…</div>}
    {data && <>
      <div className="stat-grid">
        <article className="stat-card stat-primary"><div className="stat-top"><span>Total employees</span><span className="stat-icon">♙</span></div><strong>{formatCount(data.coverage.total_employee_count)}</strong><small>Across the organization</small></article>
        <article className="stat-card"><div className="stat-top"><span>With compensation</span><span className="stat-icon green">✓</span></div><strong>{formatCount(data.coverage.employees_with_compensation)}</strong><small>Current salary recorded</small></article>
        <article className="stat-card"><div className="stat-top"><span>Missing compensation</span><span className="stat-icon amber">!</span></div><strong>{formatCount(data.coverage.employees_without_compensation)}</strong><small>Needs salary information</small></article>
      </div>
      <section className="panel"><div className="panel-heading"><div><p className="eyebrow">CURRENT ANNUAL GROSS BASE SALARY</p><h2>Salary by currency</h2><p className="panel-note">Each currency is shown separately; values are not converted.</p></div></div><MoneyTable rows={data.salary_by_currency} /></section>
      <section className="panel"><div className="panel-heading"><div><p className="eyebrow">CURRENT ANNUAL GROSS BASE SALARY</p><h2>Department salary by currency</h2><p className="panel-note">Compare compensation within the same currency and department.</p></div></div>
        {data.department_salary_by_currency.length ? <div className="table-wrap"><table><thead><tr><th>Department</th><th>Currency</th><th>People</th><th>Average</th><th>Median</th><th>Range</th></tr></thead><tbody>{data.department_salary_by_currency.map((row) => <tr key={`${row.department}-${row.currency}`}><td className="strong-cell">{row.department}</td><td><span className="currency-pill">{row.currency}</span></td><td>{formatCount(row.employee_count)}</td><td>{row.average_amount}</td><td>{row.median_amount}</td><td>{row.minimum_amount} – {row.maximum_amount}</td></tr>)}</tbody></table></div> : <p className="table-empty">No compensated department groups yet.</p>}
      </section>
      <div className="breakdown-grid">
        <Breakdown title="By country" label="Country" rows={data.employee_breakdowns.by_country.map((row) => ({ name: row.country, count: row.employee_count, covered: row.employees_with_compensation }))} />
        <Breakdown title="By department" label="Department" rows={data.employee_breakdowns.by_department.map((row) => ({ name: row.department, count: row.employee_count, covered: row.employees_with_compensation }))} />
        <Breakdown title="By job title" label="Job title" rows={data.employee_breakdowns.by_job_title.map((row) => ({ name: row.job_title, count: row.employee_count, covered: row.employees_with_compensation }))} />
      </div>
    </>}
    <footer className="page-foot">Compensation figures reflect current annual gross base salary in each employee’s local currency.</footer>
  </div>;
}
