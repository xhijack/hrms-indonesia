# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.utils import flt

import erpnext

salary_slip = frappe.qb.DocType("Salary Slip")
salary_detail = frappe.qb.DocType("Salary Detail")
salary_component = frappe.qb.DocType("Salary Component")


def execute(filters=None):
	if not filters:
		filters = {}

	currency = None
	if filters.get("currency"):
		currency = filters.get("currency")
	company_currency = erpnext.get_company_currency(filters.get("company"))

	salary_slips = get_salary_slips(filters, company_currency)
	if not salary_slips:
		return [], []

	earning_types, ded_types = get_earning_and_deduction_types(salary_slips, filters.get("salary_structure"))
	columns = get_columns(earning_types, ded_types)

	ss_earning_map = get_salary_slip_details(salary_slips, currency, company_currency, "earnings")
	ss_ded_map = get_salary_slip_details(salary_slips, currency, company_currency, "deductions")

	doj_map = get_employee_doj_map()

	data = []
	for ss in salary_slips:
		employee_number = frappe.db.get_value("Employee", ss.employee, "employee_number")

		row = {
			"salary_slip_id": ss.name,
			"employee": employee_number,
			"employee_name": ss.employee_name,
			"data_of_joining": doj_map.get(ss.employee),
			"branch": ss.branch,
			"grade": ss.grade,
			"department": ss.department,
			"designation": ss.designation,
			"company": ss.company,
			"start_date": ss.start_date,
			"end_date": ss.end_date,
			"leave_without_pay": ss.leave_without_pay,
			"absent_days": ss.absent_days,
			"payment_days": ss.payment_days,
			"currency": currency or company_currency,
			"total_loan_repayment": ss.total_loan_repayment,
		}

		# update_column_width(ss, columns)

		for e in earning_types:
			row.update({frappe.scrub(e): ss_earning_map.get(ss.name, {}).get(e, 0.0)})

		for d in ded_types:
			row.update({frappe.scrub(d): ss_ded_map.get(ss.name, {}).get(d, 0.0)})

		if currency == company_currency:
			row.update(
				{
					"gross_pay": flt(ss.gross_pay) * flt(ss.exchange_rate),
					"total_deduction": flt(ss.total_deduction) * flt(ss.exchange_rate),
					"net_pay": flt(ss.net_pay) * flt(ss.exchange_rate),
				}
			)

		else:
			row.update(
				{"gross_pay": ss.gross_pay, "total_deduction": ss.total_deduction, "net_pay": ss.net_pay}
			)

		data.append(row)

	return columns, data


# def get_earning_and_deduction_types(salary_slips):
# 	salary_component_and_type = {_("Earning"): [], _("Deduction"): []}

# 	for salary_component in get_salary_components(salary_slips):
# 		component_type = get_salary_component_type(salary_component)
# 		salary_component_and_type[_(component_type)].append(salary_component)

# 	return sorted(salary_component_and_type[_("Earning")]), sorted(salary_component_and_type[_("Deduction")])


def update_column_width(ss, columns):
	if ss.branch is not None:
		columns[3].update({"width": 120})
	if ss.department is not None:
		columns[4].update({"width": 120})
	if ss.designation is not None:
		columns[5].update({"width": 120})
	if ss.leave_without_pay is not None:
		columns[9].update({"width": 120})


def get_columns(earning_types, ded_types):
	columns = [
		{
			"label": _("Employee Number"),
			"fieldname": "employee",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("NAMA"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 150,
		},
		# {
		# 	"label": _("Grade"),
		# 	"fieldname": "grade",
		# 	"fieldtype": "Link",
		# 	"options": "Employee Grade",
		# 	"width": 80,
		# },
		# {
		# 	"label": _("Leave Without Pay"),
		# 	"fieldname": "leave_without_pay",
		# 	"fieldtype": "Float",
		# 	"width": 50,
		# },
		# {
		# 	"label": _("Absent Days"),
		# 	"fieldname": "absent_days",
		# 	"fieldtype": "Float",
		# 	"width": 50,
		# },
		# {
		# 	"label": _("Payment Days"),
		# 	"fieldname": "payment_days",
		# 	"fieldtype": "Float",
		# 	"width": 120,
		# },
	]

	for sc, desc in earning_types.items():
		columns.append({
			"label": desc,
			"fieldname": frappe.scrub(sc),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150
		})

	# columns.append({
	# 	"label": _("Gross Pay"),
	# 	"fieldname": "gross_pay",
	# 	"fieldtype": "Currency",
	# 	"options": "currency",
	# 	"width": 120
	# })

	for sc, desc in ded_types.items():
		columns.append({
			"label": desc,
			"fieldname": frappe.scrub(sc),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150
		})
	
	columns.extend(
		[
			{
				"label": _("Loan Repayment"),
				"fieldname": "total_loan_repayment",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 150,
			},
			{
				"label": _("JUMLAH POTONGAN"),
				"fieldname": "total_deduction",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 150,
			},
			{
				"label": _("GAJI BERSIH"),
				"fieldname": "net_pay",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 150,
			},
		]
	)
	return columns

def get_earning_and_deduction_types(salary_slips, salary_structure=None):
	salary_component_and_type = {_("Earning"): {}, _("Deduction"): {}}

	if salary_structure:
		earning_components = frappe.get_all(
			"Salary Detail",
			filters={"parent": salary_structure, "parentfield": "earnings"},
			fields=["salary_component"],
			order_by="idx"
		)
		deduction_components = frappe.get_all(
			"Salary Detail",
			filters={"parent": salary_structure, "parentfield": "deductions"},
			fields=["salary_component"],
			order_by="idx"
		)

		earning_list = [e.salary_component for e in earning_components]
		deduction_list = [d.salary_component for d in deduction_components]

	else:
		earning_list = []
		deduction_list = []
		for sc in get_salary_components(salary_slips):
			sc_type = get_salary_component_type(sc)
			if sc_type == "Earning":
				earning_list.append(sc)
			elif sc_type == "Deduction":
				deduction_list.append(sc)

	# Ambil descriptions
	descriptions = frappe.get_all(
		"Salary Component",
		filters={"name": ["in", earning_list + deduction_list]},
		fields=["name", "description"]
	)

	desc_map = {d.name: d.description for d in descriptions}

	salary_component_and_type[_("Earning")] = {e: desc_map.get(e, e) for e in earning_list}
	salary_component_and_type[_("Deduction")] = {d: desc_map.get(d, d) for d in deduction_list}

	return salary_component_and_type[_("Earning")], salary_component_and_type[_("Deduction")]


def get_salary_components(salary_slips):
	return (
		frappe.qb.from_(salary_detail)
		.where((salary_detail.amount != 0) & (salary_detail.parent.isin([d.name for d in salary_slips])))
		.select(salary_detail.salary_component)
		.distinct()
	).run(pluck=True)


def get_salary_component_type(salary_component):
	return frappe.db.get_value("Salary Component", salary_component, "type", cache=True)


def get_salary_slips(filters, company_currency):
    doc_status = {"Draft": 0, "Submitted": 1, "Cancelled": 2}
    salary_slip = frappe.qb.DocType("Salary Slip")
    employee = frappe.qb.DocType("Employee")

    query = (
        frappe.qb.from_(salary_slip)
        .left_join(employee)
        .on(salary_slip.employee == employee.name)
        .select(
            salary_slip.star,
            employee.grade.as_("grade")
        )
    )

    if filters.get("docstatus"):
        query = query.where(salary_slip.docstatus == doc_status[filters.get("docstatus")])

    if filters.get("from_date"):
        query = query.where(salary_slip.start_date >= filters.get("from_date"))

    if filters.get("to_date"):
        query = query.where(salary_slip.end_date <= filters.get("to_date"))

    if filters.get("company"):
        query = query.where(salary_slip.company == filters.get("company"))

    if filters.get("employee"):
        query = query.where(salary_slip.employee == filters.get("employee"))

    if filters.get("grade"):
        query = query.where(employee.grade == filters.get("grade"))

    if filters.get("salary_structure"):
        query = query.where(salary_slip.salary_structure == filters.get("salary_structure"))

    return query.run(as_dict=True)



def get_employee_doj_map():
	employee = frappe.qb.DocType("Employee")

	result = (frappe.qb.from_(employee).select(employee.name, employee.date_of_joining)).run()

	return frappe._dict(result)


def get_salary_slip_details(salary_slips, currency, company_currency, component_type):
	salary_slips = [ss.name for ss in salary_slips]

	result = (
		frappe.qb.from_(salary_slip)
		.join(salary_detail)
		.on(salary_slip.name == salary_detail.parent)
		.where((salary_detail.parent.isin(salary_slips)) & (salary_detail.parentfield == component_type))
		.select(
			salary_detail.parent,
			salary_detail.salary_component,
			salary_detail.amount,
			salary_slip.exchange_rate,
		)
	).run(as_dict=1)

	ss_map = {}

	for d in result:
		ss_map.setdefault(d.parent, frappe._dict()).setdefault(d.salary_component, 0.0)
		if currency == company_currency:
			ss_map[d.parent][d.salary_component] += flt(d.amount) * flt(
				d.exchange_rate if d.exchange_rate else 1
			)
		else:
			ss_map[d.parent][d.salary_component] += flt(d.amount)

	return ss_map
