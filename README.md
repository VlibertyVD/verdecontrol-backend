# 🌿 VerdeControl - Guía Rápida de Instalación

Este proyecto se compone de dos partes: un **Backend (API)** construido con Django y un **Frontend (Web)** construido con Nuxt 3 y Vue.

A continuación, los pasos para levantar el backend en tu máquina local.

---

## ⚙️ PARTE 1: Levantar el Backend (Django)

Abre una terminal, entra a la carpeta del backend (`verdecontrol-backend`) y ejecuta:

1. **Crear y activar el entorno virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate

   # 🌿 VerdeControl - Guía Rápida de Instalación

Este proyecto se compone de dos partes: un **Backend (API)** construido con Django y un **Frontend (Web)** construido con Nuxt 3 y Vue.

A continuación, los pasos para levantar ambas partes en tu máquina local.

---

## ⚙️ PARTE 1: Levantar el Backend (Django)

Abre una terminal, entra a la carpeta del backend (`verdecontrol-backend`) y ejecuta:

### 1. Crear y activar el entorno virtual:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar dependencias y preparar la base de datos:
```bash
pip install -r requirements.txt
python manage.py migrate
```

### 3. Crear un usuario administrador (opcional):
```bash
python manage.py createsuperuser
```

### 4. Encender el servidor:
```bash
python manage.py runserver 9093
```

---