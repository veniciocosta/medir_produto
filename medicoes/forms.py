import re
from django import forms
from .models import (
    Company, Department, Sector, ProductionLine, 
    ProductSKU, SKUConfiguration, MeasurementRecord
)

def clean_cnpj_string(value):
    """Strips all punctuation from CNPJ, leaving only digits."""
    return re.sub(r'\D', '', value)

def validate_cnpj(value):
    """Robust Brazilian CNPJ mathematical validator."""
    cnpj = clean_cnpj_string(value)
    if len(cnpj) != 14:
        raise forms.ValidationError("O CNPJ deve conter exatamente 14 dígitos.")
    if len(cnpj) == 1:
        raise forms.ValidationError("O CNPJ não pode ser uma sequência de dígitos idênticos.")
    if len(set(cnpj)) == 1:
        raise forms.ValidationError("O CNPJ não pode ser uma sequência de dígitos idênticos.")
        
    # First verifying digit weights
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total1 = sum(int(digit) * weight for digit, weight in zip(cnpj[:12], weights1))
    remainder1 = total1 % 11
    digit1 = 0 if remainder1 < 2 else 11 - remainder1
    
    # Second verifying digit weights
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total2 = sum(int(digit) * weight for digit, weight in zip(cnpj[:13], weights2))
    remainder2 = total2 % 11
    digit2 = 0 if remainder2 < 2 else 11 - remainder2
    
    if int(cnpj[12]) != digit1 or int(cnpj[13]) != digit2:
        raise forms.ValidationError("Falha na validação dos dígitos verificadores do CNPJ.")


class MeasurementUploadForm(forms.ModelForm):
    class Meta:
        model = MeasurementRecord
        fields = ['product_sku', 'image']
        widgets = {
            'product_sku': forms.Select(attrs={
                'class': 'block w-full rounded-lg border border-slate-300 bg-white py-2 px-3 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 text-sm'
            }),
            'image': forms.FileInput(attrs={
                'class': 'block w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200 transition cursor-pointer',
                'accept': 'image/*'
            }),
        }


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'cnpj']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ex: Antigravity Alimentos S/A', 'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'cnpj': forms.TextInput(attrs={'placeholder': 'XX.XXX.XXX/XXXX-XX', 'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
        }

    def clean_cnpj(self):
        cnpj_value = self.cleaned_data.get('cnpj')
        if cnpj_value:
            validate_cnpj(cnpj_value)
            # Format and save only the digits for database clean state
            return clean_cnpj_string(cnpj_value)
        return cnpj_value


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['company', 'name']
        widgets = {
            'company': forms.Select(attrs={'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'name': forms.TextInput(attrs={'placeholder': 'Ex: Departamento de Controle de Qualidade', 'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
        }


class SectorForm(forms.ModelForm):
    class Meta:
        model = Sector
        fields = ['department', 'name']
        widgets = {
            'department': forms.Select(attrs={'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'name': forms.TextInput(attrs={'placeholder': 'Ex: Setor de Embalagem A', 'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
        }


class ProductionLineForm(forms.ModelForm):
    class Meta:
        model = ProductionLine
        fields = ['sector', 'name']
        widgets = {
            'sector': forms.Select(attrs={'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'name': forms.TextInput(attrs={'placeholder': 'Ex: Embaladora de Biscoitos #12', 'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
        }


class ProductSKUForm(forms.ModelForm):
    class Meta:
        model = ProductSKU
        fields = ['production_line', 'code', 'name', 'target_width_cm', 'target_length_cm']
        widgets = {
            'production_line': forms.Select(attrs={'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'code': forms.TextInput(attrs={'placeholder': 'Ex: 48019', 'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'name': forms.TextInput(attrs={'placeholder': 'Ex: ESTRELA CREAM CRACKER 20X400', 'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'target_width_cm': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Ex: 12.00', 'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'target_length_cm': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Ex: 12.00', 'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
        }


class SKUConfigurationForm(forms.ModelForm):
    # Optional field allowing copying properties from an existing SKU configuration
    copy_from_sku = forms.ModelChoiceField(
        queryset=ProductSKU.objects.all(),
        required=False,
        empty_label="-- Não copiar configurações (manter/definir valores personalizados) --",
        label="Copiar Configurações de SKU Existente",
        widget=forms.Select(attrs={'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'})
    )

    class Meta:
        model = SKUConfiguration
        fields = [
            'object_format', 'canny_threshold_low', 'canny_threshold_high', 
            'blur_kernel_size', 'erosion_amount', 'resolution_width', 
            'resolution_height', 'brightness_target', 'width_offset_mm', 'length_offset_mm',
            'gray_target_value', 'gray_tolerance_range', 'rgb_target_r', 
            'rgb_target_g', 'rgb_target_b', 'rgb_spectrum_variance'
        ]
        widgets = {
            'object_format': forms.Select(attrs={'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'canny_threshold_low': forms.NumberInput(attrs={'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'canny_threshold_high': forms.NumberInput(attrs={'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'blur_kernel_size': forms.NumberInput(attrs={'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'erosion_amount': forms.NumberInput(attrs={'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'resolution_width': forms.NumberInput(attrs={'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'resolution_height': forms.NumberInput(attrs={'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'brightness_target': forms.NumberInput(attrs={'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'width_offset_mm': forms.NumberInput(attrs={'step': '0.01', 'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'length_offset_mm': forms.NumberInput(attrs={'step': '0.01', 'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'gray_target_value': forms.NumberInput(attrs={'min': '0', 'max': '255', 'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'gray_tolerance_range': forms.NumberInput(attrs={'min': '0', 'max': '255', 'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'rgb_target_r': forms.NumberInput(attrs={'min': '0', 'max': '255', 'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'rgb_target_g': forms.NumberInput(attrs={'min': '0', 'max': '255', 'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'rgb_target_b': forms.NumberInput(attrs={'min': '0', 'max': '255', 'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
            'rgb_spectrum_variance': forms.NumberInput(attrs={'min': '0', 'max': '255', 'class': 'block w-full rounded-lg border border-slate-300 py-2 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 bg-white'}),
        }

    def __init__(self, *args, **kwargs):
        # We pop product_sku out of kwargs to establish corporate boundary filtering
        product_sku = kwargs.pop('product_sku', None)
        super().__init__(*args, **kwargs)
        
        if product_sku:
            # Trace the corporate identifier (company ID)
            current_company_id = product_sku.production_line.sector.department.company_id
            
            # Enforce SAME company boundary, excluding the current SKU itself
            self.fields['copy_from_sku'].queryset = ProductSKU.objects.filter(
                production_line__sector__department__company_id=current_company_id
            ).exclude(id=product_sku.id)
        else:
            self.fields['copy_from_sku'].queryset = ProductSKU.objects.none()

    def clean_blur_kernel_size(self):
        blur_val = self.cleaned_data.get('blur_kernel_size')
        if blur_val and blur_val % 2 == 0:
            raise forms.ValidationError("O tamanho do kernel de desfoque gaussiano deve ser um número ímpar (ex: 3, 5, 7).")
        return blur_val
