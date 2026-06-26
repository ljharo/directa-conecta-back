# Directa Conecta — Guía del proyecto

Sistema interno de gestión de personas reportadas durante la emergencia sísmica Venezuela 2026.
Construido con Django 5 + PostgreSQL 16, desplegado en Docker.

---

## Levantar el entorno

```bash
# Primera vez o después de cambiar código
docker compose up --build

# Levantar sin reconstruir
docker compose up

# Apagar
docker compose down

# Apagar y borrar volúmenes (limpia la BD)
docker compose down -v
```

El entrypoint hace automáticamente en cada arranque:
1. `makemigrations centros usuarios personas`
2. `migrate`
3. Crea el superusuario si no existe (variables de `.env`)

---

## Variables de entorno (`.env`)

Copiar `.env.example` como `.env` y ajustar los valores.

| Variable | Descripción |
|---|---|
| `DJANGO_SECRET_KEY` | Clave secreta de Django |
| `DJANGO_DEBUG` | `True` en desarrollo, `False` en producción |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos separados por comas |
| `POSTGRES_DB` | Nombre de la base de datos |
| `POSTGRES_USER` | Usuario de PostgreSQL |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL |
| `POSTGRES_HOST` | Host del servidor PostgreSQL (usar `db` en Docker) |
| `WEB_PORT` | Puerto expuesto del backend en el host (default `8000`) |
| `DB_PORT` | Puerto expuesto de PostgreSQL en el host (default `5432`) |
| `DJANGO_SUPERUSER_USERNAME` | Usuario admin creado en el primer arranque |
| `DJANGO_SUPERUSER_PASSWORD` | Contraseña del admin |
| `DJANGO_SUPERUSER_EMAIL` | Email del admin (puede dejarse vacío) |
| `API_KEY_BOT` | API key del bot de Telegram (header `Authorization: Bearer`) |

> El puerto interno de PostgreSQL dentro de Docker siempre es `5432` (hardcodeado en `settings/base.py`). `DB_PORT` solo controla el mapeo en el host.

---

## Estructura de apps

```
apps/
├── centros/     # Modelos Hospital + Edificio, importación Excel desde Admin
├── personas/    # Modelos PersonaReportada + ActualizacionEstado + choices
├── usuarios/    # Sin modelos propios; administra User estándar de Django
└── api/         # API REST para el chatbot de Telegram
```

### `centros` — Centros y edificios
- **Hospital**: nombre, codigo (único), tipo, estado venezolano, ciudad, dirección, teléfono, capacidad, activo.
- **Edificio**: nombre, estado, ciudad, dirección, estado_estructural, notas.
- Admin permite importar hospitales desde Excel y descargar plantilla.

### `personas` — Personas reportadas
- **PersonaReportada**: id_caso (auto DC-XXXXX), datos personales, estado clínico, ubicación. El hospital es FK opcional — se puede registrar sin conocer el centro.
- **ActualizacionEstado**: auditoría de cambios de estado (quién, cuándo, de qué a qué). Se crea automáticamente al editar `estado_actual` desde el Admin.
- `caso_sensible` se activa automáticamente cuando `estado_actual = fallecido`.

### `usuarios` — Roles
Los roles se manejan con campos nativos de Django `User`:
- `is_superuser = True` → **Admin**: acceso total, gestión de usuarios.
- `is_staff = True` → **Operador**: CRUD de pacientes, hospitales y edificios; no puede gestionar usuarios.

### `api` — API REST
- Autenticación por API key en header `Authorization: Bearer <key>`.
- `GET /api/v1/buscar/?q=<texto>&page=<n>` — búsqueda de personas reportadas.
- `GET /api/v1/edificios/` — listado de edificios con daño estructural.

---

## Roles en el Admin

| Rol | Acceso |
|---|---|
| **Superuser (Admin)** | Todo: pacientes, hospitales, edificios, usuarios, campos sensibles |
| **Operador** | CRUD en pacientes, hospitales y edificios; sin gestión de usuarios; sin campos sensibles (caso_sensible, notas_internas) |

Para crear un Operador:
1. Entrar al Admin como superusuario.
2. Ir a **Autenticación y autorización → Usuarios → Agregar usuario**.
3. Ingresar nombre de usuario y contraseña, guardar.
4. En la pantalla siguiente marcar **Activo** y **Es staff**.
5. En la sección **Grupos**, seleccionar **Operador** y moverlo a "Grupos elegidos".
6. Guardar.

El grupo **Operador** se crea automáticamente al arrancar el contenedor (via `post_migrate`).
No hace falta asignar permisos individuales; el grupo ya los tiene configurados.

---

## Comandos útiles

```bash
# Abrir shell de Django
docker compose exec web python manage.py shell

# Exportar CSV para respond.io (knowledge source)
docker compose exec web python manage.py exportar_knowledge_source

# Crear superusuario manualmente
docker compose exec web python manage.py createsuperuser

# Ver logs del contenedor web
docker compose logs -f web
```

---

## API REST

### Servidor de producción

| | |
|---|---|
| **Base URL** | `http://54.196.236.28:8000` |
| **API Key** | `88g1KftM3tYSK2690eGif11KNPZFdioIZg5` |
| **Header** | `Authorization: Bearer 88g1KftM3tYSK2690eGif11KNPZFdioIZg5` |

### Documentación interactiva
- **Swagger UI**: `http://54.196.236.28:8000/api/docs/`
- **ReDoc**: `http://54.196.236.28:8000/api/redoc/`

---

### Pacientes (`/api/v1/personas/`)

Lookup por `id_caso` (formato `DC-00001`). Todos los campos de tipo choice aceptan el valor interno (`hospitalizado`) o el label legible (`Hospitalizado — Estable`).

| Método | URL | Descripción |
|---|---|---|
| `GET` | `/api/v1/personas/` | Listar todos los pacientes |
| `GET` | `/api/v1/personas/{id_caso}/` | Obtener un paciente |
| `POST` | `/api/v1/personas/` | Crear paciente (solo `nombre_completo` es obligatorio) |
| `PATCH` | `/api/v1/personas/{id_caso}/` | Actualizar campos parcialmente |
| `DELETE` | `/api/v1/personas/{id_caso}/` | Eliminar paciente |

**Campos disponibles en POST/PATCH:**
```
nombre_completo        requerido
cedula                 solo números, sin prefijo
nacionalidad_cedula    V / E / P
alias_o_apodos
edad_aproximada        número entero
sexo                   M / F / no_especifica
tipo_sangre            A+ A- B+ B- AB+ AB- O+ O-
estado_ultima_ubicacion  estado venezolano (ej: "la_guaira" o "La Guaira")
detalle_ultima_ubicacion texto libre
fecha_ultimo_contacto  YYYY-MM-DD (default: hoy)
hospital               código del hospital (ej: "HV") o null
estado_actual          ver choices abajo
hospital_origen        texto libre
caso_sensible          true/false
notas_internas         texto libre
```

**`estado_actual` — valores válidos:**
```
sin_informacion · reportado · en_traslado · en_centro_acopio · en_centro_atencion
hospitalizado · hospitalizado_critico · dado_de_alta · localizado_con_vida
no_confirmado · fallecido
```

> Al cambiar `estado_actual` via PATCH se registra automáticamente en el historial.
> Si `estado_actual = fallecido`, `caso_sensible` se activa automáticamente.

**Búsqueda por texto (endpoint legado):**
```
GET /api/v1/buscar/?q=<texto>&page=<n>
```
Busca en nombre, alias, cédula, id_caso y hospital. Mínimo 2 caracteres.

---

### Hospitales (`/api/v1/hospitales/`)

Lookup por `codigo` (ej: `HV`).

| Método | URL | Descripción |
|---|---|---|
| `GET` | `/api/v1/hospitales/` | Listar hospitales (filtro: `?q=texto`) |
| `GET` | `/api/v1/hospitales/{codigo}/` | Obtener un hospital |
| `POST` | `/api/v1/hospitales/` | Crear hospital o centro de ayuda |
| `PATCH` | `/api/v1/hospitales/{codigo}/` | Actualizar datos |
| `DELETE` | `/api/v1/hospitales/{codigo}/` | Eliminar (falla con 409 si tiene pacientes) |

**Campos POST/PATCH:**
```
nombre               requerido
codigo               requerido, único (ej: HV)
tipo                 requerido — hospital_publico · hospital_privado · clinica
                     centro_acopio · refugio · proteccion_civil · cruz_roja · otro
estado               requerido — estado venezolano
ciudad               requerido
direccion
telefono_principal
capacidad_aproximada número entero
activo               true/false (default: true)
```

---

### Edificios (`/api/v1/edificios/`)

Lookup por `id` numérico.

| Método | URL | Descripción |
|---|---|---|
| `GET` | `/api/v1/edificios/` | Listar edificios (filtros: `?q=texto&estado_estructural=derrumbado`) |
| `GET` | `/api/v1/edificios/{id}/` | Obtener un edificio |
| `POST` | `/api/v1/edificios/` | Registrar edificio afectado |
| `PATCH` | `/api/v1/edificios/{id}/` | Actualizar datos |
| `DELETE` | `/api/v1/edificios/{id}/` | Eliminar |

**Campos POST/PATCH:**
```
nombre               requerido
estado               requerido — estado venezolano
ciudad               requerido
direccion            requerido
estado_estructural   requerido — derrumbado · parcialmente_danado
                     integridad_delicada · evacuado · en_evaluacion
notas
```

---

### Ejemplo rápido — cómo usarlo desde Claude

```bash
KEY="88g1KftM3tYSK2690eGif11KNPZFdioIZg5"
BASE="http://54.196.236.28:8000/api/v1"

# Crear paciente
curl -s -X POST "$BASE/personas/" \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"nombre_completo": "Juan Pérez", "cedula": "12345678", "nacionalidad_cedula": "V"}'

# Actualizar estado
curl -s -X PATCH "$BASE/personas/DC-00001/" \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"estado_actual": "hospitalizado", "hospital_origen": "Hospital Vargas"}'

# Buscar paciente
curl -s -H "Authorization: Bearer $KEY" "$BASE/buscar/?q=juan"

# Crear hospital
curl -s -X POST "$BASE/hospitales/" \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"nombre": "Hospital Vargas", "codigo": "HV", "tipo": "hospital_publico", "estado": "distrito_capital", "ciudad": "Caracas"}'

# Registrar edificio colapsado
curl -s -X POST "$BASE/edificios/" \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"nombre": "Torre A", "estado": "la_guaira", "ciudad": "La Guaira", "direccion": "Av. Principal", "estado_estructural": "derrumbado"}'
```

---

## Importación Excel

Desde el Admin se puede importar hospitales y personas reportadas desde archivos `.xlsx`.

El importer detecta automáticamente la fila de encabezados (busca en las primeras 5 filas) y maneja columnas con sufijo ` *` (campos requeridos en las plantillas formateadas).

Las plantillas descargables están en `docs/`.

---

## Arquitectura de settings

```
config/settings/
├── base.py    # Configuración común
├── dev.py     # DEBUG=True, sin restricciones de host
└── prod.py    # DEBUG=False, ALLOWED_HOSTS, STATIC_ROOT
```

La variable `DJANGO_SETTINGS_MODULE` selecciona cuál cargar (ver `docker-compose.yml`).
