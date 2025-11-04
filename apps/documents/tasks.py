"""
Tareas asíncronas de Celery para generación de documentos
"""
from celery import shared_task
from django.core.files import File
from django.utils import timezone
import time
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_document_task(self, document_id):
    """
    Tarea asíncrona para generar un documento PDF
    
    Args:
        document_id: ID del GeneratedDocument a generar
    """
    from .models import GeneratedDocument, DocumentLog
    from .pdf_generator import generate_profile_pdf, generate_candidate_report_pdf
    
    try:
        # Obtener el documento
        document = GeneratedDocument.objects.get(id=document_id)
        
        # Cambiar estado a generando
        document.status = GeneratedDocument.STATUS_GENERATING
        document.save(update_fields=['status'])
        
        # Iniciar contador de tiempo
        start_time = time.time()
        
        # Generar el PDF según el tipo
        if document.profile:
            # Generar PDF de perfil
            pdf_buffer = generate_profile_pdf(
                profile=document.profile,
                template=document.template
            )
            filename = f"perfil_{document.profile.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
        elif document.candidate:
            # Generar PDF de candidato
            pdf_buffer = generate_candidate_report_pdf(
                candidate=document.candidate,
                profile=document.profile,  # Puede ser None
                template=document.template
            )
            filename = f"candidato_{document.candidate.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
        else:
            # Generar PDF personalizado (TODO: implementar generador genérico)
            raise ValueError("Generación de documentos personalizados aún no implementada")
        
        # Guardar el archivo
        document.file.save(filename, File(pdf_buffer), save=False)
        document.file_size = pdf_buffer.getbuffer().nbytes
        
        # Calcular tiempo de generación
        generation_time = time.time() - start_time
        document.generation_time = generation_time
        
        # Cambiar estado a completado
        document.status = GeneratedDocument.STATUS_COMPLETED
        document.save()
        
        logger.info(f"Documento {document_id} generado exitosamente en {generation_time:.2f}s")
        
        return {
            'status': 'success',
            'document_id': document_id,
            'filename': filename,
            'generation_time': generation_time
        }
        
    except GeneratedDocument.DoesNotExist:
        logger.error(f"Documento {document_id} no encontrado")
        return {'status': 'error', 'message': 'Documento no encontrado'}
        
    except Exception as e:
        logger.error(f"Error al generar documento {document_id}: {str(e)}", exc_info=True)
        
        # Marcar como fallido
        try:
            document = GeneratedDocument.objects.get(id=document_id)
            document.status = GeneratedDocument.STATUS_FAILED
            document.error_message = str(e)
            document.save()
        except:
            pass
        
        # Reintentar si no se ha alcanzado el máximo
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        
        return {'status': 'error', 'message': str(e)}


def generate_document_sync(document_id):
    """
    Versión síncrona de la generación de documentos
    Útil para tests o generación inmediata
    """
    return generate_document_task.apply(args=[document_id]).get()


@shared_task
def generate_bulk_documents_task(document_ids):
    """
    Genera múltiples documentos de forma asíncrona
    
    Args:
        document_ids: Lista de IDs de GeneratedDocument
    """
    from .models import GeneratedDocument
    
    results = {
        'total': len(document_ids),
        'successful': 0,
        'failed': 0,
        'errors': []
    }
    
    for doc_id in document_ids:
        try:
            result = generate_document_task.apply(args=[doc_id]).get()
            if result.get('status') == 'success':
                results['successful'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'document_id': doc_id,
                    'error': result.get('message')
                })
        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'document_id': doc_id,
                'error': str(e)
            })
            logger.error(f"Error en generación masiva del documento {doc_id}: {e}")
    
    logger.info(f"Generación masiva completada: {results['successful']}/{results['total']} exitosos")
    return results


@shared_task
def cleanup_old_documents():
    """
    Tarea programada para limpiar documentos antiguos
    Se ejecuta periódicamente (configurar en Celery Beat)
    """
    from datetime import timedelta
    from .models import GeneratedDocument
    
    # Eliminar documentos temporales más antiguos de 30 días
    threshold_date = timezone.now() - timedelta(days=30)
    old_documents = GeneratedDocument.objects.filter(
        created_at__lt=threshold_date,
        custom_data__temporary=True  # Solo temporales
    )
    
    count = old_documents.count()
    old_documents.delete()
    
    logger.info(f"Limpieza automática: {count} documentos antiguos eliminados")
    return {'deleted_count': count}


@shared_task
def regenerate_failed_documents():
    """
    Reintenta generar documentos que fallaron
    Se ejecuta periódicamente
    """
    from .models import GeneratedDocument
    
    # Buscar documentos fallidos de las últimas 24 horas
    failed_documents = GeneratedDocument.objects.filter(
        status=GeneratedDocument.STATUS_FAILED,
        created_at__gte=timezone.now() - timedelta(hours=24)
    )
    
    results = {
        'total_attempts': failed_documents.count(),
        'successful': 0,
        'failed': 0
    }
    
    for document in failed_documents:
        try:
            # Reintentar generación
            result = generate_document_task.apply(args=[document.id]).get()
            if result.get('status') == 'success':
                results['successful'] += 1
            else:
                results['failed'] += 1
        except Exception as e:
            results['failed'] += 1
            logger.error(f"Error al reintentar documento {document.id}: {e}")
    
    logger.info(
        f"Reintento de documentos fallidos: "
        f"{results['successful']}/{results['total_attempts']} exitosos"
    )
    return results


@shared_task
def update_document_stats():
    """
    Actualiza estadísticas de documentos
    Se ejecuta cada hora
    """
    from django.db.models import Count, Avg
    from .models import GeneratedDocument
    
    stats = {
        'total': GeneratedDocument.objects.count(),
        'by_status': dict(
            GeneratedDocument.objects.values('status').annotate(count=Count('id'))
        ),
        'avg_generation_time': GeneratedDocument.objects.filter(
            status=GeneratedDocument.STATUS_COMPLETED
        ).aggregate(avg=Avg('generation_time'))['avg'] or 0,
        'total_downloads': GeneratedDocument.objects.aggregate(
            total=models.Sum('download_count')
        )['total'] or 0
    }
    
    # Aquí podrías guardar estas estadísticas en caché o en un modelo específico
    logger.info(f"Estadísticas actualizadas: {stats}")
    return stats


@shared_task
def generate_scheduled_reports():
    """
    Genera reportes programados automáticamente
    Por ejemplo, reportes mensuales, semanales, etc.
    """
    from .models import DocumentTemplate, GeneratedDocument, Profile
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Ejemplo: Generar reporte mensual de perfiles aprobados
    approved_profiles = Profile.objects.filter(
        status='approved',
        updated_at__gte=timezone.now() - timedelta(days=30)
    )
    
    if approved_profiles.exists():
        # Obtener plantilla de reporte
        template = DocumentTemplate.objects.filter(
            document_type=DocumentTemplate.TYPE_CLIENT_REPORT,
            is_default=True
        ).first()
        
        if template:
            # Obtener un usuario admin para asignar el documento
            admin_user = User.objects.filter(role='admin').first()
            
            for profile in approved_profiles:
                document = GeneratedDocument.objects.create(
                    title=f"Reporte Mensual - {profile.position_title}",
                    description="Reporte generado automáticamente",
                    template=template,
                    profile=profile,
                    status=GeneratedDocument.STATUS_PENDING,
                    generated_by=admin_user,
                    custom_data={'scheduled': True, 'type': 'monthly'}
                )
                
                # Generar el PDF
                generate_document_task.delay(document.id)
            
            logger.info(f"Generados {approved_profiles.count()} reportes programados")
            return {'generated': approved_profiles.count()}
    
    return {'generated': 0}