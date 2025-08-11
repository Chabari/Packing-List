// Copyright (c) 2025, Geetab Technologies Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on("Pack List", {
	refresh(frm) {
        frm.add_custom_button(__("Picking List"), function () {
            frappe.set_route('query-report', 'Picking List', {
                pack_list: frm.doc.name
            });

        });
        frm.add_custom_button(__("Loading Schedule"), function () {
            frappe.set_route('query-report', 'Loading Schedule', {
                pack_list: frm.doc.name
            });
        });
	},
    setup: (frm) => {
		frm.set_query('source_warehouse', () => {
			return {
				filters: {
					'is_group': 0,
					'company': frm.doc.company
				}
			};
		});
	},
	get_sales_invoices_and_items: function (frm) {
		frappe.call({
			method: "get_submitted_sales_invoices_and_items",
			doc: frm.doc,
			callback: function (r) {
				refresh_field("sales_invoices");
				refresh_field('pl_items');
			}
		});
	},
	before_save: function(frm) {
		frappe.call({
			method: "get_items",
			freeze: true,
			doc: frm.doc,
			callback: function() {
				refresh_field('pl_items');
			}
		});
	}
});
