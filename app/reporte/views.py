"""
Vistas para el módulo de reportes dinámicos
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging

from users.services.jwt import jwt_required
from bitacora import service_bitacora
from .services import openai_service as gemini_service, generador_reportes

logger = logging.getLogger(__name__)


@csrf_exempt
@jwt_required
@require_http_methods(["POST"])
def generar_reporte_dinamico(request):
    """
    Genera un reporte dinámico basado en un prompt en lenguaje natural
    
    Endpoint: POST /reportes/generar
    
    Body:
    {
        "prompt": "Dame las ventas del último mes con estado pagada"
    }
    
    Response:
    {
        "ok": true,
        "prompt_original": "...",
        "interpretacion": {
            "tipo_reporte": "ventas",
            "filtros": {...},
            "campos": [...],
            ...
        },
        "reporte": {
            "tipo": "ventas",
            "total_registros": 50,
            "datos": [...],
            "estadisticas": {...}
        }
    }
    """
    try:
        # Parsear el body
        data = json.loads(request.body)
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return JsonResponse({
                'ok': False,
                'error': 'El campo "prompt" es requerido'
            }, status=400)
        
        logger.info(f"[REPORTE] Generando reporte para: {prompt}")
        
        # 1. Interpretar el prompt con Gemini AI
        try:
            interpretacion = gemini_service.interpretar_prompt_reporte(prompt)
            logger.info(f"[REPORTE] Interpretacion: {interpretacion}")
        except ValueError as e:
            logger.error(f"[REPORTE ERROR] Error de interpretacion: {str(e)}")
            return JsonResponse({
                'ok': False,
                'error': f'No se pudo interpretar el prompt: {str(e)}'
            }, status=400)
        except Exception as e:
            logger.error(f"[REPORTE ERROR] Error de Gemini AI: {str(e)}")
            return JsonResponse({
                'ok': False,
                'error': f'Error al comunicarse con el servicio de IA: {str(e)}'
            }, status=500)
        
        # 2. Validar la estructura
        es_valido, mensaje_error = gemini_service.validar_estructura_reporte(interpretacion)
        if not es_valido:
            logger.warning(f"[REPORTE WARNING] Estructura invalida: {mensaje_error}")
            return JsonResponse({
                'ok': False,
                'error': mensaje_error,
                'interpretacion': interpretacion
            }, status=400)
        
        # 3. Generar el reporte
        try:
            reporte = generador_reportes.generar_reporte(interpretacion)
            logger.info(f"[REPORTE] Reporte generado: {reporte['total_registros']} registros")
        except Exception as e:
            logger.error(f"[REPORTE ERROR] Error al generar reporte: {str(e)}")
            return JsonResponse({
                'ok': False,
                'error': f'Error al generar el reporte: {str(e)}',
                'interpretacion': interpretacion
            }, status=500)
        
        # 4. Registrar en bitácora
        service_bitacora.registrar_accion(
            accion="GENERAR_REPORTE",
            usuario=request.usuario.correo,
            detalles=f"Reporte generado - Tipo: {interpretacion['tipo_reporte']} - Registros: {reporte['total_registros']} - Prompt: {prompt[:100]}",
            resultado="EXITOSO"
        )
        
        # 5. Retornar respuesta exitosa
        return JsonResponse({
            'ok': True,
            'prompt_original': prompt,
            'interpretacion': interpretacion,
            'reporte': reporte
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'ok': False,
            'error': 'Body JSON invalido'
        }, status=400)
    except Exception as e:
        logger.error(f"[REPORTE ERROR] Error inesperado: {str(e)}")
        
        # Registrar error en bitácora
        service_bitacora.registrar_accion(
            accion="GENERAR_REPORTE",
            usuario=request.usuario.correo if hasattr(request, 'usuario') else None,
            detalles=f"Error al generar reporte: {str(e)}",
            resultado="FALLIDO"
        )
        
        return JsonResponse({
            'ok': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@csrf_exempt
@jwt_required
@require_http_methods(["GET"])
def ejemplos_prompts(request):
    """
    Retorna ejemplos de prompts que pueden usarse
    
    Endpoint: GET /reportes/ejemplos
    
    Response:
    {
        "ok": true,
        "ejemplos": [...]
    }
    """
    ejemplos = {
        "ventas": [
            "Dame todas las ventas del último mes",
            "Muéstrame las ventas pagadas desde el 1 de octubre",
            "Quiero ver las ventas fallidas de esta semana",
            "Dame el reporte de ventas del año 2024",
            "Ventas con estado pagada ordenadas por fecha"
        ],
        "productos": [
            "Lista todos los productos",
            "Muéstrame los productos con stock bajo",
            "Dame los productos de la categoría laptops",
            "Productos de la marca Apple",
            "Lista de productos creados este mes"
        ],
        "usuarios": [
            "Dame todos los clientes registrados",
            "Clientes registrados en octubre 2024",
            "Lista de usuarios activos",
            "Nuevos clientes de la última semana"
        ],
        "bitacora": [
            "Muéstrame las acciones de la bitácora del último día",
            "Dame los registros de login exitosos",
            "Acciones fallidas de la última semana",
            "Bitácora de acciones del usuario admin@example.com",
            "Registros de creación de productos"
        ],
        "consejos": [
            "Sé específico con las fechas: 'última semana', 'octubre 2024', 'desde 2024-10-01'",
            "Puedes filtrar por estado: 'pagadas', 'pendientes', 'fallidas'",
            "Menciona ordenamiento: 'ordenadas por fecha', 'más recientes primero'",
            "Usa nombres de campos: 'con total mayor a 100', 'con stock menor a 10'"
        ]
    }
    
    return JsonResponse({
        'ok': True,
        'ejemplos': ejemplos,
        'mensaje': 'Estos son ejemplos de prompts que puedes usar. ¡Experimenta con tus propias variaciones!'
    })
