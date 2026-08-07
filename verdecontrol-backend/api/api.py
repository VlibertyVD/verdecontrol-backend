from ninja import NinjaAPI, Schema
from django.contrib.auth import get_user_model
from api.models import Company, GreenZone
from django.db import transaction
from datetime import date
from typing import List
from django.contrib.auth import authenticate
from django.core.signing import dumps, loads, BadSignature, SignatureExpired
from ninja.security import HttpBearer

api = NinjaAPI(title="VerdeControl API", version="1.0.0")
User = get_user_model()

# 1. Definimos qué datos esperamos recibir del frontend
class RegisterSchema(Schema):
    full_name: str
    company_email: str
    company_name: str
    role: str
    password: str

# 2. Creamos el endpoint que procesa el registro
@api.post("/register")
def register_user(request, payload: RegisterSchema):
    try:
        # Usamos transaction.atomic para asegurar que si algo falla, no se guarde a medias
        with transaction.atomic():
            # Creamos la empresa primero
            company = Company.objects.create(
                name=payload.company_name,
                email=payload.company_email
            )
            
            # Separamos el nombre completo (básico para first/last name)
            names = payload.full_name.split(" ", 1)
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else ""

            # Creamos el usuario vinculándolo a su email (y usando create_user para hashear la clave)
            user = User.objects.create_user(
                username=payload.company_email, # Usaremos el email como username
                email=payload.company_email,
                password=payload.password,
                first_name=first_name,
                last_name=last_name,
                role=payload.role
            )
            
            return {"success": True, "message": "Cuenta corporativa creada con éxito"}
            
    except Exception as e:
        return api.create_response(request, {"success": False, "error": str(e)}, status=400)

class TimerOut(Schema):
    id: int
    name: str
    company_name: str
    location_details: str | None
    timer_status: str
    next_maintenance: date | None
    reminder_frequency: str
    days_left: int

@api.get("/timers", response=List[TimerOut])
def get_timers(request):
    zones = GreenZone.objects.select_related('company').all()
    result = []
    today = date.today()
    
    for zone in zones:
        # Calculamos los días restantes matemáticamente
        days_left = 0
        if zone.next_maintenance:
            days_left = (zone.next_maintenance - today).days
            
        result.append({
            "id": zone.id,
            "name": zone.name,
            "company_name": zone.company.name,
            "location_details": zone.location_details,
            "timer_status": zone.timer_status,
            "next_maintenance": zone.next_maintenance,
            "reminder_frequency": zone.reminder_frequency,
            "days_left": days_left
        })
    return result

# 1. Esquema para recibir los datos de login
class LoginSchema(Schema):
    email: str
    password: str

# 2. Endpoint de validación
@api.post("/login")
def login_user(request, payload: LoginSchema):
    user = authenticate(request, username=payload.email, password=payload.password)
    
    if user is not None:
        # Generamos un token firmado criptográficamente con el ID del usuario
        token = dumps({"user_id": user.id})
        # Ahora devolvemos el token real al frontend
        return {"success": True, "token": token, "message": "Acceso concedido"}
    else:
        return api.create_response(
            request, 
            {"success": False, "error": "Correo o contraseña incorrectos"}, 
            status=401
        )

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            # Intentamos leer el token. Si tiene más de 24 horas (86400 seg), lo rechaza.
            data = loads(token, max_age=86400)
            # Si es válido, guardamos el ID del usuario en request.auth
            return data.get("user_id") 
        except (BadSignature, SignatureExpired):
            return None # Esto lanza un error 401 Unauthorized automáticamente