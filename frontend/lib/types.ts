export type ApiError = { error?: { code?: string; message?: string; details?: { field?: string; message?: string }[] } };

export type Employee = {
  id: string;
  employee_code: string;
  first_name: string;
  last_name: string;
  email: string;
  country: string;
  department: string;
  job_title: string;
  created_at: string;
  updated_at: string;
};

export type EmployeeList = {
  items: Employee[];
  pagination: { page: number; page_size: number; total: number; total_pages: number };
};

export type Compensation = {
  employee_id: string;
  amount: string;
  currency: string;
  created_at: string;
  updated_at: string;
};

export type Insights = {
  coverage: { total_employee_count: number; employees_with_compensation: number; employees_without_compensation: number };
  salary_by_currency: SalaryStatistics[];
  employee_breakdowns: {
    by_country: { country: string; employee_count: number; employees_with_compensation: number }[];
    by_department: { department: string; employee_count: number; employees_with_compensation: number }[];
    by_job_title: { job_title: string; employee_count: number; employees_with_compensation: number }[];
  };
  department_salary_by_currency: (SalaryStatistics & { department: string; currency: string })[];
};

export type SalaryStatistics = {
  currency: string;
  employee_count: number;
  average_amount: string;
  median_amount: string;
  minimum_amount: string;
  maximum_amount: string;
};
