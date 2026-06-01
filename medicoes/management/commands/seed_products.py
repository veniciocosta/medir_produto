from django.core.management.base import BaseCommand
from medicoes.models import Company, Department, Sector, ProductionLine, ProductSKU, SKUConfiguration

class Command(BaseCommand):
    help = "Seeds initial Company structure and Product SKUs from the original script."

    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding...")
        
        # 1. Create Company
        company, _ = Company.objects.get_or_create(
            name="Antigravity Foods",
            defaults={"cnpj": "12.345.678/0001-90"}
        )
        
        # 2. Create Department
        department, _ = Department.objects.get_or_create(
            company=company,
            name="Packaging Operations"
        )
        
        # 3. Create Sector
        sector, _ = Sector.objects.get_or_create(
            department=department,
            name="Biscuit Wrapping"
        )
        
        # 4. Create Production Line
        prod_line, _ = ProductionLine.objects.get_or_create(
            sector=sector,
            name="Packaging Line #1"
        )
        
        # 5. Cream Cracker SKU Dictionary from original script
        dict_produtos = {
            '48019': "ESTRELA CREAM CRACKER 20X400",
            '8952': "PREDILLETO BISCOITO CRACKER 20X400",
            '89019': "PREDILLETO CREAM CRACKER 20X400",
            '48219': "PELAGGIO CREAM CRACKER 20X400",
            '348219': "PELAGGIO CREAM CRACKER 20X400 - EXPORTAÇÃO",
            '48018': "ESTRELA CREAM CRACKER AGUA E SAL 20X400",
            '48215': "PELAGGIO CREAM CRACKER AMANTEIGADO 20X400",
            '348213': "PELAGGIO SAUDAVEL CREAM CRACKER INTEGRAL 20X400 - EXPORTAÇÃO",
            '48213': "PELAGGIO SAUDAVEL CREAM CRACKER INTEGRAL 20X400",
            '80146': "BIRIBA CREAM CRACKER20X400G",
            '89205': "BONSABOR CREAM CRACKER 20X400",
            '32119': "FORTALEZA CREAM CRACKER 20X400G",
            '89426': "CARVALHO CREAM CRACKER 20X400G",
            '389205': "BONSABOR CREAM CRACKER 20X400 – EXPORTAÇÃO",
            '348215': "PELAGGIO CREAM CRACKER AMANTEIGADO 20X400 - EXPORTAÇÃO",
            '348019': "ESTRELA CREAM CRACKER 20X400 - EXPORTAÇÃO",
            '348018': "ESTRELA CREAM CRACKER AGUA E SAL 20X400 - EXPORTAÇÃO",
            '75032': "PILAR CRACKER TRADICION 20X400",
            '75027': "VIT CREAM CRACKER 20X400",
            '48622': "PELAGGIO BISCOITO CREAM CRACKER TRADICIONAL 20X400",
            '30105': "RICHESTER SUPERIORE CREAM CRACKER 20X400",
            '330105': "RICHESTER SUPERIORE CREAM CRACKER 20X400 - EXPORTACAO"
        }

        # Seed SKUs (Assuming standard cream cracker is roughly 12.0 cm x 12.0 cm)
        count = 0
        for code, name in dict_produtos.items():
            sku, created = ProductSKU.objects.get_or_create(
                production_line=prod_line,
                code=code,
                defaults={
                    "name": name,
                    "target_width_cm": 12.00,
                    "target_length_cm": 12.00
                }
            )
            # Ensure a default SKUConfiguration is mapped to this product
            SKUConfiguration.objects.get_or_create(product_sku=sku)
            if created:
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded company structure and {count} product SKUs!"))
