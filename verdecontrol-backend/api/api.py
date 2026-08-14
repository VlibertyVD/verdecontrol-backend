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

class RegisterSchema(Schema):
    full_name: str
    company_email: str
    company_name: str
    role: str
    password: str

@api.post("/register")
def register_user(request, payload: RegisterSchema):
    try:
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

class LoginSchema(Schema):
    email: str
    password: str

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

class MapZoneOut(Schema):
    id: int
    name: str
    latitude: float
    longitude: float
    timer_status: str

# Endpoint exclusivo para cargar los pines en el mapa
@api.get("/map-zones2", response=List[MapZoneOut], auth=AuthBearer())
def get_map_zones(request):
    # Filtramos solo las áreas que tengan coordenadas guardadas
    zones = GreenZone.objects.filter(latitude__isnull=False, longitude__isnull=False)
    
    result = []
    for zone in zones:
        result.append({
            "id": zone.id,
            "name": zone.name,
            "latitude": zone.latitude,
            "longitude": zone.longitude,
            "timer_status": zone.timer_status
        })
    return result


class CompanyListOut(Schema):
    id: int
    name: str
    zone: str
    company_code: str

class PersonnelOut(Schema):
    id: int
    full_name: str
    role: str
    avatar_url: str | None

class GreenZoneBasicOut(Schema):
    id: int
    name: str
    area_size: str
    image_url: str | None
    current_metric: str
    needs_attention: bool

class CompanyDetailOut(Schema):
    id: int
    name: str
    company_code: str
    status: str
    personnel: List[PersonnelOut]
    green_zones: List[GreenZoneBasicOut]

@api.get("/companies", response=List[CompanyListOut], auth=AuthBearer())
def list_companies(request):
    return Company.objects.filter(user_id=request.auth)

@api.get("/companies/{company_id}", response=CompanyDetailOut, auth=AuthBearer())
def get_company_detail(request, company_id: int):
    company = Company.objects.get(id=company_id)
    return company

class CompanyCreateIn(Schema):
    name: str
    email: str
    company_code: str = 'COMP-0000'
    zone: str = 'Zone North'

@api.get("/companies", response=List[CompanyListOut], auth=AuthBearer())
def list_companies(request):

    user_id = request.auth
    
    companies = Company.objects.filter(
        Q(user_id=user_id) | Q(operators__id=user_id)
    ).distinct()
    
    return companies

@api.post("/companies", response=CompanyListOut, auth=AuthBearer())
def create_company(request, payload: CompanyCreateIn):

    company = Company.objects.create(
        name=payload.name,
        email=payload.email,
        company_code=payload.company_code,
        zone=payload.zone,
        user_id=request.auth 
    )
    return company

class GreenZoneCreateIn(Schema):
    name: str
    company_id: int
    polygon_coordinates: list
    area_size: str 

class MapZoneOut(Schema):
    id: int
    name: str
    polygon_coordinates: list | None = None
    reminder_frequency: str | None = None
    area_size: str | None = None
    timer_status: str | None = None

class ZoneFrequencyUpdateIn(Schema):
    reminder_frequency: str

@api.post("/green-zones", auth=AuthBearer())
def create_green_zone(request, payload: GreenZoneCreateIn):
    company = Company.objects.get(id=payload.company_id)
    zone = GreenZone.objects.create(
        name=payload.name,
        company=company,
        polygon_coordinates=payload.polygon_coordinates,
        area_size=payload.area_size,  # <-- Guardamos el áre
        timer_status='Scheduled'
    )
    return {"id": zone.id, "name": zone.name}

@api.get("/map-zones", response=List[MapZoneOut], auth=AuthBearer())
def get_map_zones(request):
    # 1. Obtenemos al usuario que hizo la petición. 
    # (Si tu AuthBearer devuelve el ID en request.auth, buscamos el usuario así):
    user = User.objects.get(id=request.auth)
    
    if not user.use_this_company:
        return [] 
        
    zones = GreenZone.objects.filter(company=user.use_this_company)
    
    return zones

@api.patch("/green-zones/{zone_id}/frequency", auth=AuthBearer())
def update_frequency(request, zone_id: int, payload: ZoneFrequencyUpdateIn):
    zone = GreenZone.objects.get(id=zone_id)
    zone.reminder_frequency = payload.reminder_frequency
    zone.save()
    return {"success": True}


class ActiveCompanyUpdateIn(Schema):
    company_id: int

@api.patch("/users/active-company", auth=AuthBearer())
def set_active_company(request, payload: ActiveCompanyUpdateIn):
    user = User.objects.get(id=request.auth)
    
    company = Company.objects.get(id=payload.company_id)
    
    user.use_this_company = company
    user.save()
    
    return {"success": True, "active_company_id": company.id}