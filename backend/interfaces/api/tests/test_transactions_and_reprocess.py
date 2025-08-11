from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from uuid import uuid4
from unittest.mock import patch

from infrastructure.database.models import User as UserModel, Receipt as ReceiptModel


class TransactionsAndReprocessTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a user
        self.user = UserModel.objects.create(
            id=uuid4(),
            email='test@example.com',
            first_name='Test',
            last_name='User',
            is_active=True,
        )
        self.user.set_password('password123') if hasattr(self.user, 'set_password') else None
        self.user.save()
        self.client.force_authenticate(user=self.user)

        # Create a minimal receipt for the user
        self.receipt = ReceiptModel.objects.create(
            id=uuid4(),
            user_id=self.user.id,
            filename='r1.jpg',
            file_size=1234,
            mime_type='image/jpeg',
            file_url='http://example.com/r1.jpg',
            status='processed',
            receipt_type='purchase',
            ocr_data={'merchant_name': 'LIDL', 'total_amount': '12.34', 'currency': 'GBP', 'date': timezone.now().date().isoformat()},
            metadata={'notes': 'note', 'custom_fields': {}},
        )

    def test_create_transaction_and_list(self):
        payload = {
            'description': 'LIDL receipt',
            'amount': '12.34',
            'currency': 'GBP',
            'type': 'expense',
            'transaction_date': timezone.now().date().isoformat(),
            'receipt_id': str(self.receipt.id),
            'category': 'food_and_drink',
        }
        resp = self.client.post('/api/v1/transactions/', data=payload, format='json')
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertTrue(resp.data.get('success'))
        tx_id = resp.data.get('transaction_id')
        self.assertIsNotNone(tx_id)

        # List transactions and ensure the new one is present
        list_resp = self.client.get('/api/v1/transactions/?limit=50&offset=0')
        self.assertEqual(list_resp.status_code, 200, list_resp.content)
        self.assertTrue(list_resp.data.get('success'))
        items = list_resp.data.get('items') or []
        self.assertTrue(any(i.get('description') == 'LIDL receipt' for i in items))

    def test_transactions_totals_and_pagination(self):
        # Seed transactions: 3 expenses GBP, 2 income GBP, 1 expense USD
        from infrastructure.database.models import Transaction as Tx
        from datetime import date
        Tx.objects.create(user_id=self.user.id, description='e1', amount='10.00', currency='GBP', type='expense', transaction_date=date(2024,1,1))
        Tx.objects.create(user_id=self.user.id, description='e2', amount='5.50', currency='GBP', type='expense', transaction_date=date(2024,1,2))
        Tx.objects.create(user_id=self.user.id, description='e3', amount='2.50', currency='USD', type='expense', transaction_date=date(2024,1,3))
        Tx.objects.create(user_id=self.user.id, description='i1', amount='20.00', currency='GBP', type='income', transaction_date=date(2024,1,4))
        Tx.objects.create(user_id=self.user.id, description='i2', amount='7.00', currency='GBP', type='income', transaction_date=date(2024,1,5))

        # Page 1 (limit 2)
        resp1 = self.client.get('/api/v1/transactions/?limit=2&offset=0&sort=date&order=asc')
        self.assertEqual(resp1.status_code, 200, resp1.content)
        self.assertTrue(resp1.data['page']['hasNext'])
        self.assertFalse(resp1.data['page']['hasPrev'])
        self.assertEqual(resp1.data['page']['totalCount'], 5)
        # Totals should include all filtered items (none filtered → all)
        totals = resp1.data['totals']
        # GBP expense 15.50, USD expense 2.50; GBP income 27.00
        def cur(arr, code):
            for r in arr:
                if r['currency'] == code:
                    return r['sum']
            return None
        self.assertEqual(cur(totals['expense'], 'GBP'), '15.50')
        self.assertEqual(cur(totals['expense'], 'USD'), '2.50')
        self.assertEqual(cur(totals['income'], 'GBP'), '27.00')

        # Page 2
        resp2 = self.client.get('/api/v1/transactions/?limit=2&offset=2&sort=date&order=asc')
        self.assertEqual(resp2.status_code, 200, resp2.content)
        self.assertTrue(resp2.data['page']['hasNext'])
        self.assertTrue(resp2.data['page']['hasPrev'])

        # Filter by type=expense, totals should reflect only expenses
        resp_exp = self.client.get('/api/v1/transactions/?type=expense&limit=50&offset=0')
        self.assertEqual(resp_exp.status_code, 200, resp_exp.content)
        totals_exp = resp_exp.data['totals']
        self.assertIsNone(cur(totals_exp['income'], 'GBP'))
        self.assertEqual(cur(totals_exp['expense'], 'GBP'), '15.50')
        self.assertEqual(cur(totals_exp['expense'], 'USD'), '2.50')

    def test_categories_endpoint(self):
        resp = self.client.get('/api/v1/categories/')
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertTrue(resp.data.get('success'))
        cats = resp.data.get('categories')
        self.assertIsInstance(cats, list)
        self.assertIn('transport', cats)

    @patch('application.receipts.use_cases.ReceiptReprocessUseCase.execute')
    def test_reprocess_normal_path(self, mock_execute):
        mock_execute.return_value = {
            'success': True,
            'receipt_id': str(self.receipt.id),
            'ocr_method': 'paddle_ocr',
            'ocr_data': self.receipt.ocr_data,
        }
        resp = self.client.post(f'/api/v1/receipts/{self.receipt.id}/reprocess/', data={'ocr_method': 'paddle_ocr'}, format='json')
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertTrue(resp.data.get('success'))

    @patch('infrastructure.database.repositories.DjangoReceiptRepository', side_effect=TypeError('abstract'))
    def test_reprocess_fallback_path(self, _patched_repo):
        resp = self.client.post(f'/api/v1/receipts/{self.receipt.id}/reprocess/', data={'ocr_method': 'paddle_ocr'}, format='json')
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertTrue(resp.data.get('success'))
        # Fallback marks needs_review=true and sets status processed
        r = ReceiptModel.objects.get(id=self.receipt.id)
        self.assertEqual(r.status, 'processed')
        self.assertTrue((r.metadata or {}).get('custom_fields', {}).get('needs_review'))


