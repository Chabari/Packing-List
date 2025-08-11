// Copyright (c) 2025, Geetab Technologies Limited and contributors
// For license information, please see license.txt

frappe.query_reports["Loading Schedule"] = {
	"filters": [

		{
			fieldname: "pack_list",
			label: __("Packing List"),
			fieldtype: "Link",
			options: "Pack List",
			reqd: 1,
		},

	]
};
