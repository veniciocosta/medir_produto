from django.contrib.auth.models import AbstractUser
from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    cnpj = models.CharField(max_length=18, blank=True, null=True, unique=True, help_text="Formato: XX.XXX.XXX/XXXX-XX")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    """
    Custom user for authentication, allowing future fields (e.g., operator roles,
    associated department) without breaking database compatibility.
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text="A empresa à qual este usuário pertence."
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"


class Department(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        unique_together = ('company', 'name')

    def __str__(self):
        return f"{self.company.name} - {self.name}"


class Sector(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='sectors')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Setor"
        verbose_name_plural = "Setores"
        unique_together = ('department', 'name')

    def __str__(self):
        return f"{self.department.name} - {self.name}"


class ProductionLine(models.Model):
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name='production_lines')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Linha de Produção"
        verbose_name_plural = "Linhas de Produção"
        unique_together = ('sector', 'name')

    def __str__(self):
        return f"{self.sector.name} - {self.name}"


class ProductSKU(models.Model):
    production_line = models.ForeignKey(ProductionLine, on_delete=models.CASCADE, related_name='skus')
    code = models.CharField(max_length=50, unique=True, help_text="Ex: 48019")
    name = models.CharField(max_length=255, help_text="Ex: Arruela Lisa M12 de Carbono")
    
    # Expected dimensions for quality validation
    target_width_cm = models.DecimalField(max_digits=5, decimal_places=2, help_text="Largura padrão esperada em cm")
    target_length_cm = models.DecimalField(max_digits=5, decimal_places=2, help_text="Comprimento/altura padrão esperado em cm")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "SKU de Produto"
        verbose_name_plural = "SKUs de Produtos"

    def __str__(self):
        return f"[{self.code}] {self.name}"


class MeasurementRecord(models.Model):
    product_sku = models.ForeignKey(ProductSKU, on_delete=models.CASCADE, related_name='measurements')
    operator = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='measurements')
    measured_at = models.DateTimeField(auto_now_add=True)
    
    # Stores the optional inspection image file
    image = models.ImageField(upload_to='measurements/%Y/%m/%d/', blank=True, null=True)
    original_image = models.ImageField(upload_to='original_inspections/%Y/%m/%d/', blank=True, null=True)
    
    # The count of products inside the reference frame
    total_items = models.PositiveIntegerField(default=0)
    
    # A JSONField option containing the array of raw measurements for historical persistence/flexibility
    raw_data = models.JSONField(
        default=list,
        blank=True,
        help_text="Armazena especificações JSON brutas de cada contorno: comprimento, largura, escala de cinza e valores RGB."
    )

    class Meta:
        verbose_name = "Registro de Medição"
        verbose_name_plural = "Registros de Medições"
        ordering = ['-measured_at']

    def __str__(self):
        return f"Record #{self.id} for SKU {self.product_sku.code} at {self.measured_at}"


class MeasurementItem(models.Model):
    """
    Highly queryable relational model representing each detected product contour in a measurement.
    Allows easy analytics (e.g. standard deviation, quality control charts, color drift).
    """
    measurement_record = models.ForeignKey(MeasurementRecord, on_delete=models.CASCADE, related_name='items')
    item_index = models.PositiveIntegerField(help_text="Índice de ordenação visual ou sequência de detecção")
    
    # Dimension specs
    length_cm = models.DecimalField(max_digits=5, decimal_places=2)
    width_cm = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Color spectrum values
    grayscale_value = models.PositiveSmallIntegerField(help_text="Índice de cor em escala de cinza (0-255)")
    r_value = models.PositiveSmallIntegerField(help_text="Valor do canal Vermelho (Red) (0-255)")
    g_value = models.PositiveSmallIntegerField(help_text="Valor do canal Verde (Green) (0-255)")
    b_value = models.PositiveSmallIntegerField(help_text="Valor do canal Azul (Blue) (0-255)")

    class Meta:
        verbose_name = "Item de Medição"
        verbose_name_plural = "Itens de Medição"
        ordering = ['measurement_record', 'item_index']

    def __str__(self):
        return f"Item #{self.item_index} in Record #{self.measurement_record.id}"


class SKUConfiguration(models.Model):
    product_sku = models.OneToOneField(ProductSKU, on_delete=models.CASCADE, related_name='configuration')
    
    FORMAT_CHOICES = [
        ('RECTANGULAR', 'Retangular / Quadrado'),
        ('ROUND', 'Redondo / Circular'),
    ]
    object_format = models.CharField(
        max_length=20, 
        choices=FORMAT_CHOICES, 
        default='RECTANGULAR',
        help_text="A categoria geométrica do produto. Itens circulares ativam métricas radiais específicas."
    )
    
    # CV Parameters
    canny_threshold_low = models.PositiveSmallIntegerField(
        default=30,
        help_text="Limite de histerese inferior para detecção de bordas Canny. Valores mais baixos capturam bordas mais fracas."
    )
    canny_threshold_high = models.PositiveSmallIntegerField(
        default=80,
        help_text="Limite de histerese superior para detecção de bordas Canny. Ajuda a mapear bordas fortes de objetos."
    )
    blur_kernel_size = models.PositiveSmallIntegerField(
        default=5,
        help_text="Tamanho do filtro de desfoque gaussiano em pixels (deve ser ímpar, ex: 3, 5, 7) para mitigar ruídos de captura de alta frequência."
    )
    erosion_amount = models.PositiveSmallIntegerField(
        default=1,
        help_text="Número de repetições de erosão morfológica 3x3 aplicadas para contrair bordas expandidas do produto e neutralizar o blooming."
    )
    
    # Video / Hardware Parameters
    resolution_width = models.PositiveIntegerField(
        default=1280,
        help_text="Largura de resolução do feed de vídeo alvo em pixels (ex: 1280 para captura 720p)."
    )
    resolution_height = models.PositiveIntegerField(
        default=720,
        help_text="Altura de resolução do feed de vídeo alvo em pixels (ex: 720 para captura 720p)."
    )
    brightness_target = models.PositiveSmallIntegerField(
        default=128,
        help_text="Valor alvo ideal da média de escala de cinza para normalização de exposição do backlight."
    )
    
    # Metrology calibration offsets
    width_offset_mm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Offset de calibração fixo em milímetros adicionado à largura bruta. Ex: -1.50 subtrai 1.5mm."
    )
    length_offset_mm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Offset de calibração fixo em milímetros adicionado ao comprimento bruto. Ex: 2.00 adiciona 2.0mm."
    )
    
    # Color Target and Tolerances
    gray_target_value = models.PositiveSmallIntegerField(
        default=128,
        help_text="Média de escala de cinza de referência [0-255]."
    )
    gray_tolerance_range = models.PositiveSmallIntegerField(
        default=20,
        help_text="Desvio aceitável (+/-)."
    )
    rgb_target_r = models.PositiveSmallIntegerField(
        default=128,
        help_text="Componente Vermelho (Red) RGB médio de referência [0-255]."
    )
    rgb_target_g = models.PositiveSmallIntegerField(
        default=128,
        help_text="Componente Verde (Green) RGB médio de referência [0-255]."
    )
    rgb_target_b = models.PositiveSmallIntegerField(
        default=128,
        help_text="Componente Azul (Blue) RGB médio de referência [0-255]."
    )
    rgb_spectrum_variance = models.PositiveSmallIntegerField(
        default=30,
        help_text="Limite aceitável de tolerância de variância de espectro (+/-)."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração do SKU"
        verbose_name_plural = "Configurações dos SKUs"

    def __str__(self):
        return f"Config for SKU: {self.product_sku.code}"
