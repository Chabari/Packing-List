// Copyright (c) 2025, Geetab Technologies Limited and contributors
// For license information, please see license.txt

frappe.query_reports["Picking List"] = {
	"filters": [
		{
			fieldname: "pack_list",
			label: __("Packing List"),
			fieldtype: "Link",
			options: "Pack List",
			reqd: 1,
		},
		
	],
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.bold) {
			value = value.bold();
		}
		return value;
	},
};
