"""
Servicio para interpretar prompts de reportes usando Google Gemini AI
"""
import json
import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)


def configurar_gemini():
    """Configura Google Gemini AI con la API Key"""
    if not settings.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY no está configurada en settings")
    
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    
    # Configurar ajustes de seguridad más permisivos para reportes de negocio
    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE"
        }
    ]
    
    # Usar gemini-1.5-flash que es más permisivo con contenido de negocio
    return genai.GenerativeModel('gemini-2.5-flash', safety_settings=safety_settings)


def interpretar_prompt_reporte(prompt_usuario):
    """
    Interpreta un prompt en lenguaje natural y lo convierte en una estructura
    JSON que puede ser ejecutada para generar reportes.
    
    Args:
        prompt_usuario (str): Prompt en lenguaje natural del usuario
        
    Returns:
        dict: Estructura JSON con los parámetros del reporte
        
    Raises:
        ValueError: Si el prompt no puede ser interpretado
        Exception: Si hay error con la API de Gemini
        
    Ejemplo de respuesta:
    {
        "tipo_reporte": "ventas",
        "filtros": {
            "fecha_desde": "2024-10-01",
            "fecha_hasta": "2024-10-31",
            "estado": "pagada"
        },
        "campos": ["total", "created_at", "usuario"],
        "agrupacion": "dia",
        "orden": "desc"
    }
    """
    try:
        modelo = configurar_gemini()
        
        # Construir el prompt completo con instrucciones del sistema
        prompt_completo = f"""Eres un asistente experto en análisis de datos que convierte solicitudes 
de reportes en lenguaje natural a estructuras JSON para consultas de base de datos.

**TABLAS Y CAMPOS DISPONIBLES:**

1. **PRODUCTOS** (products_producto)
   - id, nombre, descripcion, precio, stock
   - categoria_id, marca_id, garantia_id
   - imagen (URL), created_at, updated_at
   
2. **VENTAS** (sales_notaventa)
   - id, total, estado (pendiente, pagada, fallida, cancelada, reembolsada)
   - usuario_id, metodo_pago_id
   - stripe_session_id, stripe_payment_intent
   - created_at, updated_at
   
3. **DETALLES DE VENTA** (sales_detalle_venta)
   - id, nota_venta_id, producto_id
   - cantidad, precio_unitario, subtotal
   
4. **USUARIOS** (users_usuario)
   - id, correo, is_active, fcm_token
   - created_at, last_login
   
5. **CLIENTES** (users_cliente)
   - id, usuario_id, nombres, apellidoPaterno, apellidoMaterno
   - ci, telefono
   
6. **CATEGORÍAS** (products_categoria)
   - id, nombre, descripcion
   
7. **MARCAS** (products_marca)
   - id, nombre
   
8. **BITÁCORA** (bitacora_bitacora)
   - id, accion, usuario, fecha_hora, detalles, resultado

**RESPUESTA REQUERIDA:**

Debes responder ÚNICAMENTE con un objeto JSON válido con esta estructura:

{{
    "tipo_reporte": "ventas" | "productos" | "usuarios" | "bitacora" | "clientes",
    "filtros": {{
        "fecha_desde": "YYYY-MM-DD" (opcional),
        "fecha_hasta": "YYYY-MM-DD" (opcional),
        "campo": "valor" (otros filtros específicos)
    }},
    "campos": ["campo1", "campo2", ...],
    "agrupacion": "dia" | "mes" | "año" | "categoria" | "marca" | null,
    "orden": "desc" | "asc" (por defecto "desc" si no se especifica),
    "limite": número (opcional, máximo 1000)
}}

**REGLAS:**
- Interpreta fechas relativas ("último mes" = desde hace 30 días hasta hoy)
- Si no se especifica fecha_hasta, usa la fecha actual (2025-11-09)
- Si no se especifican campos, incluye los más relevantes
- Usa nombres de campos exactos de las tablas
- Para "orden", usa "desc" por defecto (más recientes primero) a menos que el usuario pida explícitamente orden ascendente
- NO incluyas explicaciones, solo el JSON puro
- NO uses bloques de código con ``` - responde SOLO el JSON
- Asegúrate de que sea JSON válido sin comentarios

**PROMPT DEL USUARIO:**
{prompt_usuario}

**RESPONDE SOLO CON EL JSON:**"""

        logger.info(f"[GEMINI] Interpretando prompt: {prompt_usuario}")
        
        # Configurar parámetros de generación
        generation_config = {
            'temperature': 0.1,  # Baja temperatura para respuestas consistentes
            'top_p': 0.95,
            'top_k': 40,
            'max_output_tokens': 1024,
        }
        
        # Hacer la llamada a Gemini
        respuesta = modelo.generate_content(
            prompt_completo,
            generation_config=generation_config
        )
        
        # Verificar si la respuesta fue bloqueada por seguridad
        if not respuesta.candidates or len(respuesta.candidates) == 0:
            logger.error("[GEMINI ERROR] No se devolvieron candidatos de respuesta")
            raise ValueError("No se recibió respuesta válida de Gemini. Intenta reformular el prompt.")
        
        candidate = respuesta.candidates[0]
        
        # Verificar el finish_reason
        finish_reason = candidate.finish_reason
        logger.info(f"[GEMINI] Finish reason: {finish_reason}")
        
        # finish_reason: 0 = UNSPECIFIED, 1 = STOP (normal), 2 = SAFETY, 3 = RECITATION, 4 = OTHER
        if finish_reason == 2:  # SAFETY
            logger.error("[GEMINI ERROR] Respuesta bloqueada por filtros de seguridad")
            raise ValueError("El contenido fue bloqueado por filtros de seguridad. Intenta reformular el prompt de manera más neutral.")
        
        if finish_reason == 3:  # RECITATION
            logger.error("[GEMINI ERROR] Respuesta bloqueada por recitacion de contenido protegido")
            raise ValueError("El prompt parece estar solicitando contenido protegido. Reformula la consulta.")
        
        # Extraer el contenido de manera segura
        if not candidate.content or not candidate.content.parts:
            logger.error("[GEMINI ERROR] No hay contenido en la respuesta")
            raise ValueError("No se recibió contenido válido de Gemini")
        
        contenido_respuesta = candidate.content.parts[0].text.strip()
        logger.info(f"[GEMINI] Respuesta recibida: {contenido_respuesta}")
        
        # Intentar parsear como JSON
        try:
            resultado = json.loads(contenido_respuesta)
        except json.JSONDecodeError:
            # Si no es JSON puro, intentar extraer el JSON del texto
            inicio_json = contenido_respuesta.find('{')
            fin_json = contenido_respuesta.rfind('}') + 1
            
            if inicio_json != -1 and fin_json > inicio_json:
                json_str = contenido_respuesta[inicio_json:fin_json]
                resultado = json.loads(json_str)
            else:
                raise ValueError("La respuesta de Gemini no contiene JSON válido")
        
        # Validar que tenga los campos mínimos requeridos
        if 'tipo_reporte' not in resultado:
            raise ValueError("La respuesta no contiene 'tipo_reporte'")
        
        # Agregar campos por defecto si no están presentes o son null
        if 'filtros' not in resultado:
            resultado['filtros'] = {}
        if 'campos' not in resultado:
            resultado['campos'] = []
        if 'orden' not in resultado or resultado['orden'] is None:
            resultado['orden'] = 'desc'
        
        logger.info(f"[GEMINI SUCCESS] Interpretacion exitosa: {resultado}")
        
        return resultado
        
    except json.JSONDecodeError as e:
        logger.error(f"[GEMINI ERROR] Error al parsear JSON: {str(e)}")
        raise ValueError(f"No se pudo interpretar la respuesta como JSON: {str(e)}")
    
    except Exception as e:
        logger.error(f"[GEMINI ERROR] Error al interpretar prompt: {str(e)}")
        raise Exception(f"Error al comunicarse con Google Gemini: {str(e)}")


def validar_estructura_reporte(estructura):
    """
    Valida que la estructura del reporte sea correcta y segura
    
    Args:
        estructura (dict): Estructura del reporte
        
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    tipos_validos = ['ventas', 'productos', 'usuarios', 'bitacora', 'clientes']
    
    # Validar tipo de reporte
    if estructura.get('tipo_reporte') not in tipos_validos:
        return False, f"Tipo de reporte inválido. Debe ser uno de: {', '.join(tipos_validos)}"
    
    # Validar límite si existe
    limite = estructura.get('limite')
    if limite:
        try:
            limite_int = int(limite)
            if limite_int > 1000:
                return False, "El límite máximo es 1000 registros"
            if limite_int < 1:
                return False, "El límite debe ser mayor a 0"
        except (ValueError, TypeError):
            return False, "El límite debe ser un número entero"
    
    # Validar orden (puede ser null, 'asc' o 'desc')
    orden = estructura.get('orden')
    if orden is not None and orden not in ['asc', 'desc']:
        return False, "El orden debe ser 'asc', 'desc' o null"
    
    return True, ""
