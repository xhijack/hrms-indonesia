frappe.views.QueryReport.prototype.get_menu_items = function () {
    let items = [
      {
        label: __("Refresh"),
        action: () => this.refresh(),
        class: "visible-xs",
      },
      {
        label: __("Edit"),
        action: () => frappe.set_route("Form", "Report", this.report_name),
        condition: () => frappe.user.is_report_manager(),
        standard: true,
      },
      {
        label: __("Print"),
        action: () => {
          let dialog = frappe.ui.get_print_settings(
            false,
            (print_settings) => this.print_report(print_settings),
            this.report_doc.letter_head,
            this.get_visible_columns()
          );
          this.add_portrait_warning(dialog);
        },
        condition: () => frappe.model.can_print(this.report_doc.ref_doctype),
        standard: true,
      },
      {
        label: __("PDF"),
        action: () => {
          let dialog = frappe.ui.get_print_settings(
            false,
            (print_settings) => this.pdf_report(print_settings),
            this.report_doc.letter_head,
            this.get_visible_columns()
          );
  
          this.add_portrait_warning(dialog);
        },
        condition: () => frappe.model.can_print(this.report_doc.ref_doctype),
        standard: true,
      },
      {
        label: __("Export"),
        action: () => this.export_report(),
        condition: () => frappe.model.can_export(this.report_doc.ref_doctype),
        standard: true,
      },
      {
        label: __("Setup Auto Email"),
        action: () =>
          frappe.set_route("List", "Auto Email Report", { report: this.report_name }),
        standard: true,
      },
      {
        label: __("Add Column"),
        action: () => {
          let d = new frappe.ui.Dialog({
            title: __("Add Column"),
            fields: [
              {
                fieldtype: "Select",
                fieldname: "doctype",
                label: __("From Document Type"),
                options: this.linked_doctypes.map((df) => ({
                  label: df.doctype,
                  value: df.doctype,
                })),
                change: () => {
                  let doctype = d.get_value("doctype");
                  frappe.model.with_doctype(doctype, () => {
                    let options = frappe.meta
                      .get_docfields(doctype)
                      .filter(frappe.model.is_value_type)
                      .map((df) => ({
                        label: df.label,
                        value: df.fieldname,
                      }));
  
                    d.set_df_property(
                      "field",
                      "options",
                      options.sort(function (a, b) {
                        if (a.label < b.label) {
                          return -1;
                        }
                        if (a.label > b.label) {
                          return 1;
                        }
                        return 0;
                      })
                    );
                  });
                },
              },
              {
                fieldtype: "Select",
                label: __("Field"),
                fieldname: "field",
                options: [],
              },
              {
                fieldtype: "Select",
                label: __("Insert After"),
                fieldname: "insert_after",
                options: this.columns.map((df) => df.label),
              },
            ],
            primary_action: (values) => {
              const custom_columns = [];
              let df = frappe.meta.get_docfield(values.doctype, values.field);
              const insert_after_index = this.columns.findIndex(
                (column) => column.label === values.insert_after
              );
  
              custom_columns.push({
                fieldname: this.columns
                  .map((column) => column.fieldname)
                  .includes(df.fieldname)
                  ? df.fieldname + "-" + frappe.scrub(values.doctype)
                  : df.fieldname,
                fieldtype: df.fieldtype,
                label: df.label,
                insert_after_index: insert_after_index,
                link_field: this.doctype_field_map[values.doctype],
                doctype: values.doctype,
                options: df.options,
                width: 100,
              });
  
              this.custom_columns = this.custom_columns.concat(custom_columns);
              frappe.call({
                method: "frappe.desk.query_report.get_data_for_custom_field",
                args: {
                  field: values.field,
                  doctype: values.doctype,
                  names: Array.from(
                    this.doctype_field_map[values.doctype].names
                  ),
                },
                callback: (r) => {
                  const custom_data = r.message;
                  const link_field =
                    this.doctype_field_map[values.doctype].fieldname;
                  this.add_custom_column(
                    custom_columns,
                    custom_data,
                    link_field,
                    values,
                    insert_after_index
                  );
                  d.hide();
                },
              });
              this.set_menu_items();
            },
          });
  
          d.show();
        },
        standard: true,
      },
      {
        label: __("User Permissions"),
        action: () =>
          frappe.set_route("List", "User Permission", {
            doctype: "Report",
            name: this.report_name,
          }),
        condition: () => frappe.user.has_role("System Manager"),
        standard: true,
      },
    ];
  
    if (this.report_name === 'Salary Register') {
      items.push({
        label: __("Print Salary Register"),
        action: () => {
          const filters = this.get_filter_values();
          get_salary_register_data(filters)
        },
      })
    } 
  
    if (frappe.user.is_report_manager()) {
      items.push({
        label: __("Save"),
        action: () => {
          let d = new frappe.ui.Dialog({
            title: __("Save Report"),
            fields: [
              {
                fieldtype: "Data",
                fieldname: "report_name",
                label: __("Report Name"),
                default:
                  this.report_doc.is_standard == "No" ? this.report_name : "",
                reqd: true,
              },
            ],
            primary_action: (values) => {
              frappe.call({
                method: "frappe.desk.query_report.save_report",
                args: {
                  reference_report: this.report_name,
                  report_name: values.report_name,
                  columns: this.get_visible_columns(),
                  filters: this.get_filter_values(),
                },
                callback: function (r) {
                  this.show_save = false;
                  d.hide();
                  frappe.set_route("query-report", r.message);
                },
              });
            },
          });
          d.show();
        },
        standard: true,
      });
    }
    
    return items;
  }
  
  
  
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
    const report_name = 'Salary Register';
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
  
  