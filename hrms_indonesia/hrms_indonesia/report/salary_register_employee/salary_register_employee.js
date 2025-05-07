frappe.query_reports["Salary Register Employee"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            reqd: 1,
            width: "100px",
        },
        {
            fieldname: "to_date",
            label: __("To"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1,
            width: "100px",
        },
        {
            fieldname: "currency",
            fieldtype: "Link",
            options: "Currency",
            label: __("Currency"),
            default: erpnext.get_currency(frappe.defaults.get_default("Company")),
            width: "50px",
        },
        {
            fieldname: "employee",
            label: __("Employee"),
            fieldtype: "Link",
            options: "Employee",
            width: "100px",
        },
        {
            fieldname: "grade",
            label: __("Grade"),
            fieldtype: "Link",
            options: "Employee Grade",
            width: "100px",
        },
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
            width: "100px",
            reqd: 1,
        },
        {
            fieldname: "docstatus",
            label: __("Document Status"),
            fieldtype: "Select",
            options: ["Draft", "Submitted", "Cancelled"],
            default: "Submitted",
            width: "100px",
        },
        {
            fieldname: "salary_structure",
            label: __("Salary Structure"),
            fieldtype: "Link",
            options: "Salary Structure",
            width: "100px",
        },
    ],
    onload: function(report) {
        report.page.add_inner_button(__('Custom Print'), function() {
            let filters = report.get_values();
			console.log('filters', filters)
            get_salary_register_data(filters);
        }, __("Print"));
    }
};

function print_salary_register(context) {
    console.log("Context received in print_salary_register:", context); // Log context to verify
    frappe.call({
        method: "hrms_indonesia.api.render_salary_register",
        args: {
            data: { ...context }
        },
        callback: ({ message }) => {
            console.log("Rendered message:", message); // Log rendered message for verification
            var wnd = window.open("about:blank", "_blank");
            wnd.document.write(message);
            wnd.print();
        }
    })
}

function get_salary_register_data(filters) {
    const report_name = 'Salary Register Employee';
    frappe.call({
        method: 'frappe.desk.query_report.run',
        type: 'GET',
        args: {
            report_name,
            filters,
            ignore_prepared_report: false,
            is_tree: true,
            parent_field: 'parent_account',
            are_default_filters: false
        },
        callback: (response) => {
            const columns = response.message.columns || []; // Ensure columns are included
            console.log("Response from report:", response);
            console.log("Columns: ", columns); 
            const data = response.message.result;
            console.log("Data: ", data); 
            const print_context = { columns, filters, report_name, data }; // Add columns to print_context
            print_salary_register(print_context); // Pass print_context including columns
        }
    });
}

function format_currency(number) {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR' }).format(number);
}
