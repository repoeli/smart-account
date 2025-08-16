import csv
from io import StringIO
from typing import List, Dict, Any
from domain.accounts.entities import User
from infrastructure.database.models import Transaction

class ReportingService:
    """Service for generating financial reports."""

    def generate_financial_overview_csv(self, user: User, start_date, end_date) -> str:
        """
        Generate a CSV report of financial overview.
        """
        transactions = Transaction.objects.filter(
            user=user,
            transaction_date__range=[start_date, end_date]
        ).order_by('transaction_date')

        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(['Date', 'Description', 'Type', 'Amount', 'Currency', 'Category'])

        # Write data
        for tx in transactions:
            writer.writerow([
                tx.transaction_date.isoformat(),
                tx.description,
                tx.type,
                str(tx.amount),
                tx.currency,
                tx.category
            ])

        return output.getvalue()
