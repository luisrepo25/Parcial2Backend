"""
Vistas para el módulo de bitácora
Maneja endpoints para consulta de acciones del sistema
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import logging

from bitacora import service_bitacora
from users.services.jwt import jwt_required

# Configurar logging
logger = logging.getLogger(__name__)


@csrf_exempt
@jwt_required
@require_http_methods(["GET"])
def obtener_bitacora(request):
    """
    Obtiene las últimas acciones registradas en la bitácora del sistema
    
    Query params:
    - page: Número de página (default: 1)
    - page_size: Tamaño de página (default: 50, max: 200)
    - accion: Filtrar por tipo de acción (opcional)
    - usuario: Filtrar por usuario (opcional)
    - resultado: Filtrar por resultado (opcional)
    
    Response:
    {
        "ok": true,
        "acciones": [
            {
                "id": 1,
                "accion": "Login exitoso",
                "usuario": "admin@example.com",
                "fecha_hora": "2025-11-09T10:30:00.123456",
                "detalles": "IP: 192.168.1.1",
                "resultado": "exitoso"
            }
        ],
        "pagination": {
            "page": 1,
            "page_size": 50,
            "total_items": 1500,
            "total_pages": 30,
            "has_next": true,
            "has_previous": false
        }
    }
    """
    try:
        # Obtener parámetros
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        accion = request.GET.get('accion', None)
        usuario = request.GET.get('usuario', None)
        resultado = request.GET.get('resultado', None)
        
        # Llamar al servicio
        resultado_data = service_bitacora.obtener_ultimas_acciones(
            page=page,
            page_size=page_size,
            accion=accion,
            usuario=usuario,
            resultado=resultado
        )
        
        # # Registrar la consulta en la bitácora
        # service_bitacora.registrar_accion(
        #     accion="Consulta de bitácora",
        #     usuario=request.usuario.correo,
        #     detalles=f"Página: {page}, Tamaño: {page_size}, Filtros: accion={accion}, usuario={usuario}, resultado={resultado}",
        #     resultado="exitoso"
        # )
        
        logger.info(f"📋 Bitácora consultada - Página {resultado_data['pagination']['page']}/{resultado_data['pagination']['total_pages']}")
        
        return JsonResponse({
            'ok': True,
            **resultado_data
        })
        
    except ValueError as e:
        logger.warning(f"⚠️ Parámetros inválidos: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error': f'Parámetros inválidos: {str(e)}'
        }, status=400)
    except Exception as e:
        logger.error(f"❌ Error al obtener bitácora: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error': f'Error al obtener bitácora: {str(e)}'
        }, status=500)
