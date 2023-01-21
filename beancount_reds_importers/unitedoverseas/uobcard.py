"""SCB Credit .csv importer."""

from beancount_reds_importers.libreader import xlsreader
from beancount_reds_importers.libtransactionbuilder import banking
from collections import namedtuple
import datetime
from beancount.core.number import D


class Importer(xlsreader.Importer, banking.Importer):
    IMPORTER_NAME = 'SCB Card CSV'

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = '^CC_TXN_History[0-9]*'
        self.header_identifier = 'United Overseas Bank Limited.*Account Type:VISA SIGNATURE'
        self.column_labels_line = 'Transaction Date,Posting Date,Description,Foreign Currency Type,Transaction Amount(Foreign),Local Currency Type,Transaction Amount(Local)'  # noqa: E501
        self.date_format = '%d %b %Y'
        self.header_map = {
                'Transaction Date': 'date',
                'Posting Date': 'date_posting',
                'Description': 'payee',
                'Foreign Currency Type': 'currency_foreign',
                'Transaction Amount(Foreign)': 'amount_foreign',
                'Local Currency Type': 'currency',
                'Transaction Amount(Local)': 'amount'
        }
        self.transaction_type_map = {}
        self.skip_transaction_types = []

    # TODO: move into utils, since this is probably a common operation
    def prepare_raw_columns(self, rdr):
        # Remove carriage returns in description
        rdr = rdr.convert('Description', lambda x: x.replace('\n', ' '))
        rdr = rdr.addfield('memo', lambda x: '')

        # delete empty rows
        rdr = rdr.select(lambda x: x['Transaction Date'] != '')
        return rdr

    def prepare_raw_rows(self, rdr):
        # Strip tabs and spaces around each field in the entire file
        rdr = rdr.convertall(lambda x: x.strip(' \t') if isinstance(x, str) else x)

        # Delete empty rows
        rdr = rdr.select(lambda x: any([i != '' for i in x]))

        return rdr

    def get_balance_statement(self, file=None):
        """Return the balance on the first and last dates"""
        max_date = self.get_max_transaction_date()
        if max_date:
            _, units, currency, _, _, _, _ = self.get_row_by_label(file, 'Statement Balance:')
            date = max_date + datetime.timedelta(days=1)
            Balance = namedtuple('Balance', ['date', 'amount', 'currency'])

            yield Balance(date, D(str(units)), currency)
