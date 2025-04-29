import json
import frappe

@frappe.whitelist(allow_guest=True)
def render_salary_register(data):
  context = json.loads(data)
  return frappe.render_template('templates/salary_register.html', context)

@frappe.whitelist(allow_guest=True)
def render_salary_report(data):
  context = json.loads(data)
  return frappe.render_template('templates/salary_register.html', context)

