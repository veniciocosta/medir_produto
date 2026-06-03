import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.files.base import ContentFile
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import Avg
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


from .forms import (
    MeasurementUploadForm, CompanyForm, DepartmentForm, 
    SectorForm, ProductionLineForm, ProductSKUForm, SKUConfigurationForm
)
from .models import (
    Company, Department, Sector, ProductionLine, 
    ProductSKU, SKUConfiguration, MeasurementRecord, MeasurementItem
)
from .services.cv_engine import analyze_product_image

class LandingPageView(TemplateView):
    """
    B2B SaaS public storefront landing page.
    """
    template_name = 'medicoes/landing_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['container_class'] = 'w-full max-w-full p-0'
        context['header_container_class'] = 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8'
        context['footer_container_class'] = 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8'
        return context


class DashboardHubView(ListView):
    """
    Main organizational tree dashboard listing Companies, Departments,
    Sectors, Production Lines, and their target Product SKUs.
    """
    model = ProductSKU
    template_name = 'medicoes/index.html'
    context_object_name = 'skus'

    def get_context_data(self, **kwargs):
        # Override CBV get_context_data adhering strictly to Django CBV rules
        context = super().get_context_data(**kwargs)
        context['companies'] = Company.objects.all().prefetch_related('departments__sectors__production_lines__skus')
        context['total_records'] = MeasurementRecord.objects.count()
        context['recent_records'] = MeasurementRecord.objects.all().select_related('product_sku')[:5]
        return context


# ==========================================
# HIERARCHICAL CRUD REGISTRATION VIEWS
# ==========================================

class CompanyCreateView(CreateView):
    model = Company
    form_class = CompanyForm
    template_name = 'medicoes/crud_form.html'
    success_url = reverse_lazy('medicoes:dashboard_hub')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Cadastrar Nova Empresa"
        context['description'] = "Inicialize um limite corporativo para segmentação de dados multi-tenant."
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Empresa '{form.cleaned_data['name']}' criada com sucesso!")
        return super().form_valid(form)


class DepartmentCreateView(CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'medicoes/crud_form.html'
    success_url = reverse_lazy('medicoes:dashboard_hub')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Cadastrar Novo Departamento"
        context['description'] = "Adicione um departamento operacional a uma entidade corporativa cadastrada."
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Departamento '{form.cleaned_data['name']}' cadastrado com sucesso!")
        return super().form_valid(form)


class SectorCreateView(CreateView):
    model = Sector
    form_class = SectorForm
    template_name = 'medicoes/crud_form.html'
    success_url = reverse_lazy('medicoes:dashboard_hub')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Cadastrar Novo Setor"
        context['description'] = "Estabeleça um setor operacional para o roteamento do fluxo de trabalho."
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Setor '{form.cleaned_data['name']}' cadastrado com sucesso!")
        return super().form_valid(form)


class ProductionLineCreateView(CreateView):
    model = ProductionLine
    form_class = ProductionLineForm
    template_name = 'medicoes/crud_form.html'
    success_url = reverse_lazy('medicoes:dashboard_hub')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Cadastrar Nova Linha de Produção"
        context['description'] = "Identifique uma linha de embalagem ou empacotamento em operação física."
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Linha de Produção '{form.cleaned_data['name']}' cadastrada com sucesso!")
        return super().form_valid(form)


class ProductSKUCreateView(CreateView):
    model = ProductSKU
    form_class = ProductSKUForm
    template_name = 'medicoes/crud_form.html'
    success_url = reverse_lazy('medicoes:dashboard_hub')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Cadastrar Novo SKU de Produto"
        context['description'] = "Adicione uma marca e um código de item (SKU) a uma linha de produção com metas de validação."
        return context

    def form_valid(self, form):
        # Automatically generate default SKUConfiguration upon creation
        with transaction.atomic():
            response = super().form_valid(form)
            SKUConfiguration.objects.get_or_create(product_sku=self.object)
        messages.success(self.request, f"SKU de Produto '{form.cleaned_data['name']}' criado com sucesso!")
        return response


# ==========================================
# SKU CONFIGURATION & PARAMETERS COPY VIEW
# ==========================================

class SKUConfigurationUpdateView(UpdateView):
    model = SKUConfiguration
    form_class = SKUConfigurationForm
    template_name = 'medicoes/sku_config.html'

    def get_object(self, queryset=None):
        # Allow fetching configuration directly using 'sku_id' parameter
        sku_id = self.kwargs.get('sku_id')
        sku = get_object_or_404(ProductSKU, id=sku_id)
        config, _ = SKUConfiguration.objects.get_or_create(product_sku=sku)
        return config

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Feed product_sku context to initiate corporate-bounded queryset filtering
        kwargs['product_sku'] = self.get_object().product_sku
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sku'] = self.get_object().product_sku
        return context

    def form_valid(self, form):
        instance = form.save(commit=False)
        copy_source = form.cleaned_data.get('copy_from_sku')
        
        # Check copy parameter
        if copy_source:
            try:
                source_config = copy_source.configuration
                # Copy settings
                instance.object_format = source_config.object_format
                instance.canny_threshold_low = source_config.canny_threshold_low
                instance.canny_threshold_high = source_config.canny_threshold_high
                instance.blur_kernel_size = source_config.blur_kernel_size
                instance.erosion_amount = source_config.erosion_amount
                instance.resolution_width = source_config.resolution_width
                instance.resolution_height = source_config.resolution_height
                instance.brightness_target = source_config.brightness_target
                instance.width_offset_mm = source_config.width_offset_mm
                instance.length_offset_mm = source_config.length_offset_mm
                
                # Copy color settings
                instance.gray_target_value = source_config.gray_target_value
                instance.gray_tolerance_range = source_config.gray_tolerance_range
                instance.rgb_target_r = source_config.rgb_target_r
                instance.rgb_target_g = source_config.rgb_target_g
                instance.rgb_target_b = source_config.rgb_target_b
                instance.rgb_spectrum_variance = source_config.rgb_spectrum_variance
                
                messages.info(self.request, f"Configuração copiada com sucesso do SKU '{copy_source.code}'!")
            except SKUConfiguration.DoesNotExist:
                messages.warning(self.request, f"O SKU de origem '{copy_source.code}' não possui uma configuração.")
        
        instance.save()
        messages.success(self.request, f"Configuração para o SKU '{instance.product_sku.code}' salva com sucesso!")
        return redirect('medicoes:dashboard', sku_id=instance.product_sku.id)


# ==========================================
# MEASUREMENT INSPECTION DASHBOARD VIEWS
# ==========================================

class MeasurementDashboardView(View):
    """
    Surgically functional View handling the measurement capture interface
    demanding a specific product_sku_id context for quality inspection.
    """
    template_name = 'medicoes/dashboard.html'

    def get_paginated_records(self, request, sku):
        all_records = MeasurementRecord.objects.filter(product_sku=sku).select_related('operator').order_by('-measured_at')
        paginator = Paginator(all_records, 5)
        page_number = request.GET.get('page')
        return paginator.get_page(page_number)

    def get_common_context(self, sku, page_obj, form=None, result_record=None):
        if form is None:
            form = MeasurementUploadForm(initial={'product_sku': sku})
        return {
            'form': form,
            'sku': sku,
            'page_obj': page_obj,
            'result_record': result_record,
            'container_class': 'w-full max-w-full px-1.5 py-1.5 sm:px-3 sm:py-3',
            'header_container_class': 'w-full max-w-full px-2 sm:px-3',
            'footer_container_class': 'w-full max-w-full px-2 sm:px-3',
        }

    def get(self, request, sku_id, *args, **kwargs):
        # Enforce that SKU exists before landing on camera feed
        sku = get_object_or_404(ProductSKU, id=sku_id)
        form = MeasurementUploadForm(initial={'product_sku': sku})
        page_obj = self.get_paginated_records(request, sku)
        
        context = self.get_common_context(sku, page_obj, form)
        return render(request, self.template_name, context)

    def post(self, request, sku_id, *args, **kwargs):
        sku = get_object_or_404(ProductSKU, id=sku_id)
        form = MeasurementUploadForm(request.POST, request.FILES)
        
        if not form.is_valid():
            page_obj = self.get_paginated_records(request, sku)
            context = self.get_common_context(sku, page_obj, form)
            return render(request, self.template_name, context)
            
        uploaded_file = request.FILES.get('image')
        if not uploaded_file:
            form.add_error('image', "Por favor, selecione um arquivo de imagem para fazer o upload.")
            page_obj = self.get_paginated_records(request, sku)
            context = self.get_common_context(sku, page_obj, form)
            return render(request, self.template_name, context)

        # Read the uploaded file's raw bytes into memory
        try:
            image_bytes = uploaded_file.read()
        except Exception as e:
            form.add_error('image', f"Erro ao ler imagem: {str(e)}")
            page_obj = self.get_paginated_records(request, sku)
            context = self.get_common_context(sku, page_obj, form)
            return render(request, self.template_name, context)

        # Trigger our decoupled Computer Vision engine with dynamic SKU configuration
        config, _ = SKUConfiguration.objects.get_or_create(product_sku=sku)
        config.refresh_from_db()
        cv_result = analyze_product_image(
            image_bytes,
            config=config,
            width_offset_mm_override=float(config.width_offset_mm),
            length_offset_mm_override=float(config.length_offset_mm)
        )

        if not cv_result['success']:
            # Render descriptive error back to the operator (A4 not found, etc.)
            form.add_error('image', cv_result['error'])
            page_obj = self.get_paginated_records(request, sku)
            context = self.get_common_context(sku, page_obj, form)
            return render(request, self.template_name, context)

        # Use an atomic transaction block to guarantee database integrity
        try:
            with transaction.atomic():
                record = form.save(commit=False)
                record.total_items = cv_result['total_items']
                record.raw_data = cv_result['items']
                
                if request.user.is_authenticated:
                    record.operator = request.user
                
                # Save the original un-annotated raw image uploaded by the webcam/user
                uploaded_file.seek(0)
                record.original_image = uploaded_file
                
                # Save the annotated JPEG generated by the cv_engine to Django Media root
                annotated_filename = f"annotated_{uploaded_file.name}"
                record.image.save(annotated_filename, ContentFile(cv_result['annotated_image']), save=False)
                
                # Save the main record
                record.save()
                
                # Save each individual contour detection inside a highly efficient bulk insert
                items_to_create = []
                for item in cv_result['items']:
                    items_to_create.append(
                        MeasurementItem(
                            measurement_record=record,
                            item_index=item['item_index'],
                            length_cm=item['length_cm'],
                            width_cm=item['width_cm'],
                            grayscale_value=item['grayscale_value'],
                            r_value=item['r_value'],
                            g_value=item['g_value'],
                            b_value=item['b_value']
                        )
                    )
                
                if items_to_create:
                    MeasurementItem.objects.bulk_create(items_to_create)
                    
            messages.success(request, f"{record.total_items} itens processados com sucesso!")
            
            # Re-fetch page_obj to include the new one (defaults to page 1)
            page_obj = self.get_paginated_records(request, sku)
            
            reset_form = MeasurementUploadForm(initial={'product_sku': sku})
            context = self.get_common_context(sku, page_obj, form=reset_form, result_record=record)
            return render(request, self.template_name, context)
            
        except Exception as e:
            form.add_error(None, f"Falha na transação do banco de dados: {str(e)}")
            page_obj = self.get_paginated_records(request, sku)
            context = self.get_common_context(sku, page_obj, form)
            return render(request, self.template_name, context)


@method_decorator(csrf_exempt, name='dispatch')
class AnalyzeLiveStreamView(View):
    """
    Highly optimized preview endpoint designed to receive captured frames via AJAX,
    execute A4 perspective homography and metrics, and return real-time feedback
    as a base64 encoded image and items count. DOES NOT save anything to database.
    """
    def post(self, request, sku_id, *args, **kwargs):
        uploaded_file = request.FILES.get('image')
        if not uploaded_file:
            return JsonResponse({'success': False, 'error': "Nenhum arquivo de imagem fornecido."}, status=400)

        try:
            sku = get_object_or_404(ProductSKU, id=sku_id)
            config, _ = SKUConfiguration.objects.get_or_create(product_sku=sku)
            config.refresh_from_db()
            image_bytes = uploaded_file.read()
            cv_result = analyze_product_image(
                image_bytes,
                config=config,
                width_offset_mm_override=float(config.width_offset_mm),
                length_offset_mm_override=float(config.length_offset_mm)
            )
            
            if not cv_result['success']:
                return JsonResponse({'success': False, 'error': cv_result['error']})
                
            # Base64 encode the annotated JPEG bytes
            encoded_image = base64.b64encode(cv_result['annotated_image']).decode('utf-8')
            
            return JsonResponse({
                'success': True,
                'total_items': cv_result['total_items'],
                'annotated_image': encoded_image,
                'items': cv_result['items']
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class MeasurementDetailJsonView(View):
    """
    JSON Endpoint returning child MeasurementItem records for a specific MeasurementRecord.
    """
    def get(self, request, record_id, *args, **kwargs):
        record = get_object_or_404(MeasurementRecord, id=record_id)
        # Fetch associated items
        items = MeasurementItem.objects.filter(measurement_record=record).order_by('item_index')
        items_data = []
        for item in items:
            items_data.append({
                'item_index': item.item_index,
                'width_cm': float(item.width_cm),
                'length_cm': float(item.length_cm),
                'grayscale_value': item.grayscale_value,
                'r_value': item.r_value,
                'g_value': item.g_value,
                'b_value': item.b_value,
            })
        return JsonResponse({
            'success': True,
            'record_id': record.id,
            'total_items': record.total_items,
            'timestamp': record.measured_at.strftime('%d/%m/%Y %H:%M:%S') if record.measured_at else '',
            'items': items_data
        })


class SKUAnalyticsJsonView(View):
    """
    Lightweight JSON view returning averaged inspection metrics for SPC trend charts.
    """
    def get(self, request, sku_id, *args, **kwargs):
        sku = get_object_or_404(ProductSKU, id=sku_id)
        config, _ = SKUConfiguration.objects.get_or_create(product_sku=sku)
        
        # Get limit parameter from query string, defaulting to 30
        limit_param = request.GET.get('limit', '30')
        try:
            limit = int(limit_param)
            if limit <= 0:
                limit = 30
        except ValueError:
            limit = 30

        # Query the latest MeasurementRecord entries annotated with the average values of their items
        records = MeasurementRecord.objects.filter(product_sku=sku).annotate(
            width_avg=Avg('items__width_cm'),
            length_avg=Avg('items__length_cm'),
            grayscale_avg=Avg('items__grayscale_value'),
            rgb_r_avg=Avg('items__r_value'),
            rgb_g_avg=Avg('items__g_value'),
            rgb_b_avg=Avg('items__b_value')
        ).order_by('-measured_at')[:limit]

        data = []
        for r in records:
            if r.width_avg is None:
                continue
            
            local_time = timezone.localtime(r.measured_at)
            today = timezone.localtime(timezone.now()).date()
            if local_time.date() == today:
                timestamp = local_time.strftime('%H:%M')
            else:
                timestamp = local_time.strftime('%d/%m')

            data.append({
                'timestamp': timestamp,
                'width_avg': float(r.width_avg),
                'length_avg': float(r.length_avg),
                'grayscale_avg': float(r.grayscale_avg),
                'rgb_r_avg': float(r.rgb_r_avg),
                'rgb_g_avg': float(r.rgb_g_avg),
                'rgb_b_avg': float(r.rgb_b_avg),
            })

        # CRITICAL: Reverse the array before returning the JsonResponse
        data.reverse()

        return JsonResponse({
            'success': True,
            'sku': {
                'id': sku.id,
                'code': sku.code,
                'name': sku.name,
                'target_width_cm': float(sku.target_width_cm),
                'target_length_cm': float(sku.target_length_cm),
                'gray_target_value': config.gray_target_value,
                'gray_tolerance_range': config.gray_tolerance_range,
                'rgb_target_r': config.rgb_target_r,
                'rgb_target_g': config.rgb_target_g,
                'rgb_target_b': config.rgb_target_b,
                'rgb_spectrum_variance': config.rgb_spectrum_variance,
            },
            'data': data
        })


