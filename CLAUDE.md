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
├── centros/     # Modelo Hospital + importación Excel desde Admin
├── personas/    # Modelo PersonaReportada + FuenteActualizacion + choices
├── usuarios/    # Modelo PerfilHospital (OneToOne→User, FK→Hospital)
└── api/         # API REST para el chatbot de Telegram
```

### `centros` — Hospitales
- **Hospital**: nombre, codigo (único), tipo, estado venezolano, ciudad, dirección, teléfono, capacidad, activo.
- Admin permite importar desde Excel y descargar plantilla.

### `personas` — Personas reportadas
- **PersonaReportada**: id_caso (auto DC-XXXXX), datos personales, estado clínico, ubicación, metadatos de reporte.
- **FuenteActualizacion**: auditoría de cambios de estado (quién, cuándo, de qué a qué).
- `caso_sensible` se activa automáticamente cuando `estado_actual = fallecido`.

### `usuarios` — Perfiles
- **PerfilHospital**: vincula un `User` de Django con un `Hospital`.
- Admins (superuser): acceso total a todos los registros.
- OperadorHospital: solo ve y crea registros de su hospital, sin campos sensibles.

### `api` — API REST
- Autenticación por API key en header `Authorization: Bearer <key>`.
- `GET /api/v1/buscar/?q=<texto>&page=<n>` — búsqueda de personas reportadas.

---

## Roles en el Admin

| Rol | Acceso |
|---|---|
| **Superuser (Admin)** | Todos los hospitales, todos los campos, importar/exportar, gestionar usuarios |
| **OperadorHospital** | Solo su hospital, sin campos de reportante, sin notas internas |

Para crear un OperadorHospital:
1. Crear el `User` desde Admin → Usuarios.
2. Asignarle un `PerfilHospital` con el hospital correspondiente.

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

### Documentación interactiva
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`
- **Schema OpenAPI (JSON)**: `http://localhost:8000/api/schema/`

### Endpoint de búsqueda

```
GET /api/v1/buscar/?q=<texto>&page=<n>
Authorization: Bearer <API_KEY_BOT>
```

**Campos de búsqueda:** nombre completo, alias, cédula, ID caso, nombre y código del hospital.

**Respuesta exitosa (200):**
```json
{
  "count": 25,
  "page": 1,
  "total_pages": 3,
  "next": "http://localhost:8000/api/v1/buscar/?q=juan&page=2",
  "previous": null,
  "results": [
    {
      "id_caso": "DC-00001",
      "nombre_completo": "Juan Pérez",
      "alias_o_apodos": "Juanito",
      "cedula": "V-12345678",
      "edad_aproximada": 35,
      "sexo": "Masculino",
      "tipo_sangre": "O+",
      "estado_actual": "Hospitalizado — Estable",
      "caso_sensible": false,
      "hospital": "Hospital Vargas (HV)",
      "hospital_origen": "",
      "estado_ultima_ubicacion": "Distrito Capital",
      "detalle_ultima_ubicacion": "El Valle",
      "fecha_ultimo_contacto": "2026-06-26",
      "fecha_actualizacion": "2026-06-26T14:30:00"
    }
  ]
}
```

**Errores:**
- `401` — API key ausente o inválida
- `400` — parámetro `q` con menos de 2 caracteres

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
