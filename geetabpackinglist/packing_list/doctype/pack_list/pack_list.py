# Copyright (c) 2025, Geetab Technologies Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model import no_value_fields
from frappe.model.document import Document
from frappe.utils import cint, flt


class PackList(Document):
	# Get submittedd sales invoices
    @frappe.whitelist()
    def get_submitted_sales_invoices_and_items(self):
        #Validations
        
        if not self.from_date:
            frappe.throw(_("Please select the From Date Filter"),title=_("From Date Required"))

        if not self.to_date:
            frappe.throw(_("Please select the To Date Filter"),title=_("To Date Required"))
        #End Validations
        
        if self.get_items_from == "Sales Invoice":
            """ Pull sales invoices based on criteria selected"""
            submitted_si = get_sales_invoices(self)

            if submitted_si:
                self.add_si_in_table(submitted_si)
                self.get_items()
                frappe.msgprint(_("Packing List generation completed"),title=_("Packing List Generation"))
            else:
                frappe.msgprint(_("Sales invoices are not available for packing list"))
                
        elif self.get_items_from == "Delivery Note":
            """ Pull delivery notes based on criteria selected"""
            submitted_dn = get_delivery_notes(self)

            if submitted_dn:
                self.add_dn_in_table(submitted_dn)
                self.get_items()
                frappe.msgprint(_("Packing List generation completed"),title=_("Packing List Generation"))
            else:
                frappe.msgprint(_("Delivery Note are not available for packing list"))


    # Add submittedd delivery notes in table
    def add_dn_in_table(self, submitted_dn):
        """ Add delivery notes in the table"""
        self.set('delivery_notes', [])

        for data in submitted_dn:
            credit_note_base_grand_total = 0
            credit_note_total_qty = 0
            self.append('delivery_notes', {
                'delivery_note': data.name,
                'customer': data.customer,
                'delivery_note_date': data.posting_date,
                'grand_total': data.base_grand_total,
                'returned_total': credit_note_base_grand_total,
                'net_total': (data.base_grand_total + credit_note_base_grand_total),
                'total_qty': data.total_qty,                        
                'returned_total_qty': credit_note_total_qty,
            })

    # Add submittedd sales invoices in table
    def add_si_in_table(self, submitted_si):
        """ Add sales invoices in the table"""
        self.set('sales_invoices', [])

        for data in submitted_si:
            credit_note_base_grand_total = get_credit_notes(self,data.name,"p_base_grand_total")
            credit_note_total_qty = get_credit_notes(self,data.name,"p_total_qty")
            self.append('sales_invoices', {
                'sales_invoice': data.name,
                'customer': data.customer,
                'sales_invoice_date': data.posting_date,
                'grand_total': data.base_grand_total,
                'returned_grand_total': credit_note_base_grand_total,
                'net_total': (data.base_grand_total + credit_note_base_grand_total),
                'total_qty': data.total_qty,                        
                'returned_total_qty': credit_note_total_qty,
                'net_qty': (data.total_qty + credit_note_total_qty)
            })

    # Get Items
    @frappe.whitelist()
    def get_items(self):
        if self.get_items_from == "Sales Invoice":
            self.get_si_items()
        elif self.get_items_from == "Delivery Note":
            self.get_dn_items()

    # Get list of Sales Invoices for Items
    def get_si_list(self, field, table):
        """Returns a list of data from the respective tables"""
        si_list = [d.get(field) for d in self.get(table) if d.get(field)]
        return si_list

    # Get list of Sales Invoice Items query
    def get_si_items(self):
        # Check for empty table or empty rows
        if not self.get("sales_invoices") or not self.get_si_list("sales_invoice", "sales_invoices"):
            frappe.throw(_("Please fill the Sales Invoices table"),
                         title=_("Sales Invoices Required"))

        si_list = self.get_si_list("sales_invoice", "sales_invoices")

        items = frappe.db.sql("""SELECT  sii.name, sii.item_code, sii.item_name, sii.warehouse,
            sii.uom, sii.description, sii.parent, ifnull(sum(sii.qty),0) as qty
            FROM `tabSales Invoice Item` sii
            WHERE sii.parent in (%s)
            GROUP BY sii.item_code, sii.item_name, sii.warehouse, sii.uom, sii.description 
            ORDER BY sii.item_name """ % \
            (", ".join(["%s"] * len(si_list))), tuple(si_list), as_dict=1)

        self.add_items(items)

    # Add sales invoice items
    def add_items(self, items):
        self.set('pl_items', [])
        for data in items:
            if self.source_warehouse:
                if data.warehouse == self.source_warehouse:
                    self.append('pl_items', self.get_item_data(data))
            else:
                self.append('pl_items', self.get_item_data(data))
        
    def get_item_data(self, data):
        credit_note_qty = get_credit_note_items(self, data.item_code) if self.get_items_from == "Sales Invoice" else 0
        itm = {
            'item_code': data.item_code,
            'item_name': data.item_name,
            'warehouse': data.warehouse,
            'invoiced_qty': data.qty,
            'returned_qty': credit_note_qty,
            'packed_qty': (data.qty + credit_note_qty),
            'uom': data.uom,
            'description': data.description,
        } 
        if self.get_items_from == "Sales Invoice":
            itm.update({
                'sales_invoice': data.parent,
                'sales_invoice_item_name': data.name
            })
        if self.get_items_from == "Delivery Note":
            itm.update({
                'delivery_note': data.parent,
                'delivery_note_item': data.name
            })
        return itm
                
    # Get list of Delivery Note Items query
    def get_dn_items(self):
        # Check for empty table or empty rows
        if not self.get("delivery_notes") or not self.get_si_list("delivery_note", "delivery_notes"):
            frappe.throw(_("Please fill the Delivery Notes Table table"),
                         title=_("Delivery Notes Required"))

        si_list = self.get_si_list("delivery_note", "delivery_notes")

        items = frappe.db.sql("""SELECT  sii.name, sii.item_code, sii.item_name, sii.warehouse,
            sii.uom, sii.description, sii.parent, ifnull(sum(sii.qty),0) as qty
            FROM `tabDelivery Note Item` sii
            WHERE sii.parent in (%s)
            GROUP BY sii.item_code, sii.item_name, sii.warehouse, sii.uom, sii.description 
            ORDER BY sii.item_name """ % \
            (", ".join(["%s"] * len(si_list))), tuple(si_list), as_dict=1)

        self.add_items(items)

# Get submittedd sales invoices query
def get_sales_invoices(self):
    si_filter = ""
    if self.territory:
        si_filter += " and si.territory = %(territory)s"
    if self.customer:
        si_filter += " and si.customer = %(customer)s"
    if self.source_warehouse:
        si_filter += " and sii.warehouse = %(source_warehouse)s"
    if self.from_date:
        si_filter += " and si.posting_date >= %(from_date)s"
    if self.to_date:
        si_filter += " and si.posting_date <= %(to_date)s"

    submitted_si = frappe.db.sql("""
        SELECT DISTINCT si.name, si.posting_date, si.customer, si.base_grand_total, si.total_qty
        FROM `tabSales Invoice` si, `tabSales Invoice Item` sii
        WHERE si.name = sii.parent
            AND si.docstatus = 1
            AND si.is_return != 1
	    AND is_pos != 1
            AND si.company = %(company)s {0}
            AND (si.total_qty > (SELECT  ifnull(sum(pli.invoiced_qty),0) as invoiced_qty
                                  FROM `tabPack List Item` pli, `tabPack List` pl
                                  WHERE pli.parent = pl.name
                                  AND pli.sales_invoice = si.name
                                  AND pl.docstatus != 2)
            )
        ORDER BY si.customer
        """.format(si_filter), {
        "territory": self.territory,
        "customer": self.customer,
        "source_warehouse": self.source_warehouse,
        "from_date": self.from_date,
        "to_date": self.to_date,
        "company": self.company
    }, as_dict=1)
    return submitted_si

# Get submittedd sales invoices query
def get_delivery_notes(self):
    si_filter = ""
    if self.customer:
        si_filter += " and si.customer = %(customer)s"
    if self.source_warehouse:
        si_filter += " and sii.warehouse = %(source_warehouse)s"
    if self.from_date:
        si_filter += " and si.posting_date >= %(from_date)s"
    if self.to_date:
        si_filter += " and si.posting_date <= %(to_date)s"

    submitted_dn = frappe.db.sql("""
        SELECT DISTINCT si.name, si.posting_date, si.customer, si.grand_total as base_grand_total, si.total_qty
        FROM `tabDelivery Note` si, `tabDelivery Note Item` sii
        WHERE si.name = sii.parent
            AND si.docstatus = 1
            AND si.company = %(company)s {0}
            AND (si.total_qty > (SELECT  ifnull(sum(pli.invoiced_qty),0) as invoiced_qty
                                  FROM `tabPack List Item` pli, `tabPack List` pl
                                  WHERE pli.parent = pl.name
                                  AND pli.delivery_note = si.name
                                  AND pl.docstatus != 2)
            )
        ORDER BY si.customer
        """.format(si_filter), {
        "customer": self.customer,
        "source_warehouse": self.source_warehouse,
        "from_date": self.from_date,
        "to_date": self.to_date,
        "company": self.company
    }, as_dict=1)
    return submitted_dn


# Get submittedd credit notes query
def get_credit_notes(self,original_sales_invoice,pwhich):
    si_filter = ""
    if original_sales_invoice:
        si_filter += " and si.return_against = %(original_sales_invoice)s"

    cr_grand_total = 0
    cr_total_qty = 0

    submitted_cr = frappe.db.sql("""
        SELECT DISTINCT si.name, ifnull(sum(si.base_grand_total),0) as base_grand_total,
                        ifnull(sum(si.total_qty),0) as total_qty
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
        AND si.is_return = 1
        AND si.company = %(company)s {0}
        GROUP BY si.name
        """.format(si_filter), {
        "original_sales_invoice": original_sales_invoice,
        "company": self.company
    }, as_dict=1)

    if submitted_cr:
        for credit_note in submitted_cr:
            cr_grand_total += credit_note.base_grand_total
            cr_total_qty += credit_note.total_qty
    
    if pwhich == "p_base_grand_total":
        return cr_grand_total
    else:
        return cr_total_qty

# Get list of Credit Note Items query
def get_credit_note_items(self,item_code):

        si_list = self.get_si_list("sales_invoice", "sales_invoices")      

        cr_total_qty = 0

        cr_items = frappe.db.sql("""SELECT item_code, ifnull(sum(qty),0) as qty
            FROM `tabSales Invoice Item` si_item, `tabSales Invoice` si
            WHERE si_item.parent = si.name            
            AND si_item.item_code = %s
            AND si.return_against in (%s)            
            GROUP BY si_item.item_code """ %
            ('%s', ', '.join(["%s"] * len(si_list))), tuple([item_code] + si_list), as_dict=1)

        if cr_items:
            for credit_note_qty in cr_items:
                cr_total_qty += credit_note_qty.qty
    
        return cr_total_qty

