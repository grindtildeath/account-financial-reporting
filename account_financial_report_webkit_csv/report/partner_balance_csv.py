# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import unicodecsv as csv

from openerp import pooler
from openerp.report.report_sxw import report_sxw
from openerp.addons.account_financial_report_webkit.report.partner_balance \
    import PartnerBalanceWebkit


def amount(text):
    return text.replace('-',
                        '&#8209;')  # replace by a non-breaking hyphen (it will not word-wrap between hyphen and numbers)


def display_line(all_comparison_lines):
    return any([line.get('balance') for line in all_comparison_lines])


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class report_csv(report_sxw):

    def create(self, cr, uid, ids, data, context=None):
        self.pool = pooler.get_pool(cr.dbname)
        self.cr = cr
        self.uid = uid
        report_obj = self.pool.get('ir.actions.report.xml')
        report_ids = report_obj.search(
            cr, uid, [('report_name', '=', self.name[7:])], context=context)
        # import pdb; pdb.set_trace()
        if report_ids:
            report_xml = report_obj.browse(
                cr, uid, report_ids[0], context=context)
            self.title = report_xml.name
            if report_xml.report_type == 'csv':
                return self.create_source_csv(cr, uid, ids, data, report_xml, context)
        elif context.get('csv_export'):
            # use model from 'data' when no ir.actions.report.xml entry
            self.table = data.get('model') or self.table
            return self.create_source_csv(cr, uid, ids, data, context)
        return super(report_csv, self).create(cr, uid, ids, data, context)

    def create_source_csv(self, cr, uid, ids, data, report_xml, context=None):
        if not context:
            context = {}
        parser_instance = self.parser(cr, uid, self.name2, context)
        self.parser_instance = parser_instance
        self.context = context
        objs = self.getObjects(cr, uid, ids, context)
        parser_instance.set_context(objs, data, ids, 'csv')
        # import pdb; pdb.set_trace()
        objs = parser_instance.localcontext['objects']
        _p = AttrDict(parser_instance.localcontext)
        csv = self.generate_csv(_p, data, objs)


class partner_balance_csv(report_csv):

    def generate_csv(self, _p, data, objects):
        import pdb; pdb.set_trace()
        with open('partner_balance.csv', 'rb') as csvfile:

            # report_parameters = TODO do we really want these ?

            field_names = ['Account/Partner_name', 'Code/Ref',
                           'Initial balance', 'Debit', 'Credit', 'Balance']

            csv_writer = csv.DictWriter(csvfile, fieldnames=field_names,
                                        delimiter='|')

            csv_writer.writeheader()

            for current_account in objects:

                partners_order = current_account.partners_order

                # do not display accounts without partners
                if not partners_order:
                    continue

                comparisons = current_account.comparisons

                # in multiple columns mode, we do not want to print accounts without any rows
                if _p.comparison_mode in ('single', 'multiple'):
                    all_comparison_lines = [
                        comp['partners_amounts'][partner_id[1]]
                        for partner_id in partners_order
                        for comp in comparisons]
                    if not display_line(all_comparison_lines):
                        continue

                current_partner_amounts = current_account.partners_amounts

                total_initial_balance = 0.0
                total_debit = 0.0
                total_credit = 0.0
                total_balance = 0.0
                if _p.comparison_mode in ('single', 'multiple'):
                    comparison_total = {}
                    for i, comp in enumerate(comparisons):
                        comparison_total[i] = {'balance': 0.0}



partner_balance_csv('report.account.account_report_partner_balance_csv',
                    'account.account',
                    parser=PartnerBalanceWebkit)
