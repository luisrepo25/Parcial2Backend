from functools import wraps
from django.http import JsonResponse
from django.conf import settings
import jwt
from ..models import Usuario

# Decorador JWT compatible con multipart/form-data

def jwt_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        # Obtener el token del header Authorization
        auth = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth:
            return JsonResponse({'ok': False, 'error': 'Se requiere Authorization header'}, status=401)
        
        parts = auth.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return JsonResponse({'ok': False, 'error': 'Formato inválido de Authorization header (debe ser: Bearer <token>)'}, status=401)
        
        token = parts[1]
        
        try:
            # Decodificar y validar el token usando PyJWT
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            if user_id is None:
                return JsonResponse({'ok': False, 'error': 'Token inválido - user_id no encontrado'}, status=401)
            
            # Adjuntar el usuario al request para usarlo en la view
            try:
                request.usuario = Usuario.objects.get(pk=user_id)
            except Usuario.DoesNotExist:
                return JsonResponse({'ok': False, 'error': 'Usuario no encontrado'}, status=401)
            
            # Llamar a la vista original
            return view_func(request, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return JsonResponse({'ok': False, 'error': 'Token expirado'}, status=401)
        except jwt.InvalidTokenError as e:
            return JsonResponse({'ok': False, 'error': f'Token inválido: {str(e)}'}, status=401)
        except Exception as e:
            return JsonResponse({'ok': False, 'error': f'Error al validar token: {str(e)}'}, status=500)
    
    return _wrapped