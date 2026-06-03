from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import Company, Department, Sector, ProductionLine, ProductSKU, SKUConfiguration, MeasurementRecord, MeasurementItem

class SKUAnalyticsJsonViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Set up organization tree
        self.company = Company.objects.create(name="Test Company", cnpj="12.345.678/0001-90")
        self.department = Department.objects.create(company=self.company, name="Test Department")
        self.sector = Sector.objects.create(department=self.department, name="Test Sector")
        self.line = ProductionLine.objects.create(sector=self.sector, name="Test Line")
        
        # Set up SKU
        self.sku = ProductSKU.objects.create(
            production_line=self.line,
            code="TEST-SKU",
            name="Test SKU Item",
            target_width_cm=10.00,
            target_length_cm=15.00
        )
        
        # Set up configuration
        self.config, _ = SKUConfiguration.objects.get_or_create(product_sku=self.sku)
        self.config.gray_target_value = 120
        self.config.gray_tolerance_range = 15
        self.config.rgb_target_r = 100
        self.config.rgb_target_g = 110
        self.config.rgb_target_b = 120
        self.config.rgb_spectrum_variance = 25
        self.config.save()

    def test_analytics_empty_data(self):
        url = reverse('medicoes:sku_analytics_data', kwargs={'sku_id': self.sku.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['sku']['code'], "TEST-SKU")
        self.assertEqual(data['sku']['target_width_cm'], 10.0)
        self.assertEqual(data['sku']['gray_target_value'], 120)
        self.assertEqual(len(data['data']), 0)

    def test_analytics_with_data(self):
        # Create records
        for i in range(5):
            record = MeasurementRecord.objects.create(
                product_sku=self.sku,
                total_items=2
            )
            # Add items with different values
            MeasurementItem.objects.create(
                measurement_record=record,
                item_index=1,
                width_cm=9.5 + i,
                length_cm=14.5 + i,
                grayscale_value=100 + i * 10,
                r_value=90 + i * 5,
                g_value=95 + i * 5,
                b_value=100 + i * 5
            )
            MeasurementItem.objects.create(
                measurement_record=record,
                item_index=2,
                width_cm=10.5 + i,
                length_cm=15.5 + i,
                grayscale_value=110 + i * 10,
                r_value=100 + i * 5,
                g_value=105 + i * 5,
                b_value=110 + i * 5
            )

        url = reverse('medicoes:sku_analytics_data', kwargs={'sku_id': self.sku.id})
        response = self.client.get(url + "?limit=3")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['success'])
        
        # Since limit is 3, we expect exactly 3 entries in chronologically ascending order (reversed from latest 3)
        self.assertEqual(len(data['data']), 3)
        
        # Latest entries in db are index 4, 3, 2. Reversed, they should be rendered as index 2, 3, 4.
        # Let's check averages for index 2: width_cm avg should be (9.5+2 + 10.5+2) / 2 = 12.0
        self.assertEqual(data['data'][0]['width_avg'], 12.0)
        # index 3: width_cm avg = 13.0
        self.assertEqual(data['data'][1]['width_avg'], 13.0)
        # index 4: width_cm avg = 14.0
        self.assertEqual(data['data'][2]['width_avg'], 14.0)

