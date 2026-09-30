"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { apiRequest } from "../../../lib/api";
import type { Compensation, Employee } from "../../../lib/types";

export default function EmployeeDetailPage() {
  const params = useParams<{ employeeId: string }>();
  const employeeId = params.employeeId;
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [compensation, setCompensation] = useState<Compensation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<{ kind: "success" | "error"; message: string } | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    Promise.all([
      apiRequest<Employee>(`/api/v1/employees/${employeeId}`, { signal: controller.signal }),
      apiRequest<Compensation>(`/api/v1/employees/${employeeId}/compensation`, { signal: controller.signal }).catch((reason: unknown) => {
        if (reason instanceof Error && reason.message === "Compensation not found") return null;
        throw reason;
      }),
    ]).then(([person, pay]) => {
      setEmployee(person); setCompensation(pay); setError(null);
      setAmount(pay?.amount ?? ""); setCurrency(pay?.currency ?? "USD");
      setLoading(false);
    }).catch((reason: unknown) => {
      if (controller.signal.aborted) return;
      setError(reason instanceof Error ? reason.message : "Unable to load employee details.");
      setLoading(false);
    });
    return () => controller.abort();
  }, [employeeId]);

  async function saveCompensation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setFeedback(null);
    if (!/^\d+(?:\.\d{1,3})?$/.test(amount) || Number(amount) <= 0) {
      setFeedback({ kind: "error", message: "Enter a positive amount with no more than 3 decimal places." }); return;
    }
    if (!/^[A-Z]{3}$/.test(currency)) {
      setFeedback({ kind: "error", message: "Enter a 3-letter uppercase currency code." }); return;
    }
    setSaving(true);
    try {
      const result = await apiRequest<Compensation>(`/api/v1/employees/${employeeId}/compensation`, {
        method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ amount, currency }),
      });
      setCompensation(result); setAmount(result.amount); setCurrency(result.currency);
      setFeedback({ kind: "success", message: "Current compensation saved successfully." });
    } catch (reason) {
      setFeedback({ kind: "error", message: reason instanceof Error ? reason.message : "Unable to save compensation." });
    } finally { setSaving(false); }
  }

  return <div className="content">
    <div className="breadcrumbs"><Link href="/employees">Employees</Link><span>/</span><span>{employee ? `${employee.first_name} ${employee.last_name}` : "Employee details"}</span></div>
    {loading && <div className="loading-card"><span className="spinner" />Loading employee…</div>}
    {error && !loading && <div className="alert alert-error" role="alert"><strong>Employee unavailable</strong><span>{error}</span><Link className="button button-secondary" href="/employees">Back to directory</Link></div>}
    {employee && !loading && <>
      <div className="detail-heading"><div className="detail-person"><div className="detail-avatar">{employee.first_name[0]}{employee.last_name[0]}</div><div><p className="eyebrow">EMPLOYEE PROFILE</p><h1>{employee.first_name} {employee.last_name}</h1><p className="subtitle">{employee.job_title} <span>·</span> {employee.department}</p></div></div><span className="country-pill country-large">{employee.country}</span></div>
      <div className="detail-grid">
        <section className="panel"><div className="panel-heading"><div><p className="eyebrow">IDENTITY &amp; ORGANIZATION</p><h2>Employee details</h2></div></div><dl className="detail-list">
          <div><dt>Employee code</dt><dd>{employee.employee_code}</dd></div><div><dt>Email address</dt><dd><a href={`mailto:${employee.email}`}>{employee.email}</a></dd></div><div><dt>Department</dt><dd>{employee.department}</dd></div><div><dt>Job title</dt><dd>{employee.job_title}</dd></div><div><dt>Country</dt><dd>{employee.country}</dd></div>
        </dl></section>
        <section className="panel compensation-panel"><div className="panel-heading"><div><p className="eyebrow">CURRENT COMPENSATION</p><h2>Annual gross base salary</h2></div><span className={compensation ? "status-badge status-active" : "status-badge status-missing"}>{compensation ? "Recorded" : "Missing"}</span></div>
          {compensation ? <div className="salary-display"><strong>{compensation.amount}</strong><span>{compensation.currency} <i>per year</i></span></div> : <p className="missing-note">No current compensation is recorded for this employee. Add their annual gross base salary below.</p>}
          {feedback && <div className={`alert ${feedback.kind === "success" ? "alert-success" : "alert-error"}`} role={feedback.kind === "success" ? "status" : "alert"}>{feedback.message}</div>}
          <form className="compensation-form" onSubmit={saveCompensation}>
            <label><span>Annual salary amount</span><div className="amount-input"><input aria-label="Annual salary amount" inputMode="decimal" placeholder="e.g. 85000.125" value={amount} onChange={(event) => setAmount(event.target.value)} required /><span>{currency}</span></div><small>Positive amount, up to 3 decimal places</small></label>
            <label><span>Currency</span><input aria-label="Currency" autoCapitalize="characters" maxLength={3} placeholder="USD" value={currency} onChange={(event) => setCurrency(event.target.value)} required /><small>Three uppercase letters; local currency</small></label>
            <button className="button button-primary save-button" disabled={saving} type="submit">{saving ? "Saving…" : compensation ? "Update compensation" : "Add compensation"}</button>
          </form>
          <p className="currency-note">Salary is shown in the employee’s local currency. No currency conversion is applied.</p>
        </section>
      </div>
    </>}
  </div>;
}
