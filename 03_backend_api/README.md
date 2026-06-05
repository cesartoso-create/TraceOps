# TraceOps Backend

Backend FastAPI para el MVP TraceOps.

## Modulos iniciales

- `meta`: informacion de version y ambiente.
- `projects`: catalogos de estados y tipos de proyecto.
- `evidences`: catalogo de categorias de evidencia.
- `workers`: Celery base para tareas asincronas.
- `db`: conexion SQLAlchemy.

## Endpoints iniciales

```text
GET /health
GET /api/v1/meta
POST /api/v1/auth/bootstrap
POST /api/v1/auth/login
GET /api/v1/auth/me
POST /api/v1/auth/devices/register
GET /api/v1/mobile/my-projects
GET /api/v1/mobile/projects/{project_id}/field-package
POST /api/v1/files/presign-upload
POST /api/v1/files/complete-upload
GET /api/v1/users/roles
GET /api/v1/users
POST /api/v1/users
GET /api/v1/users/{user_id}
PATCH /api/v1/users/{user_id}
POST /api/v1/users/{user_id}/deactivate
POST /api/v1/users/{user_id}/reset-password
GET /api/v1/contractors
POST /api/v1/contractors
GET /api/v1/contractors/{contractor_id}
PATCH /api/v1/contractors/{contractor_id}
GET /api/v1/crews
POST /api/v1/crews
GET /api/v1/crews/{crew_id}
PATCH /api/v1/crews/{crew_id}
GET /api/v1/crews/{crew_id}/members
POST /api/v1/crews/{crew_id}/members
DELETE /api/v1/crews/{crew_id}/members/{member_id}
GET /api/v1/properties
POST /api/v1/properties
GET /api/v1/properties/{property_id}
PATCH /api/v1/properties/{property_id}
GET /api/v1/projects/statuses
GET /api/v1/projects/types
GET /api/v1/projects
POST /api/v1/projects
GET /api/v1/projects/{project_id}
PATCH /api/v1/projects/{project_id}
POST /api/v1/projects/{project_id}/assign
POST /api/v1/projects/{project_id}/transition
GET /api/v1/pext/projects/{project_id}/prefeasibility
PUT /api/v1/pext/projects/{project_id}/prefeasibility
GET /api/v1/pext/projects/{project_id}/field-output
GET /api/v1/pext/projects/{project_id}/field-output/validation
GET /api/v1/pext/projects/{project_id}/splice-charts
POST /api/v1/pext/projects/{project_id}/splice-charts
GET /api/v1/pext/splice-charts/{chart_id}
PATCH /api/v1/pext/splice-charts/{chart_id}
POST /api/v1/pext/splice-charts/{chart_id}/entries
GET /api/v1/evidences/categories
POST /api/v1/evidences
GET /api/v1/evidences/project/{project_id}/items
GET /api/v1/evidences/{evidence_id}
```

## Prueba rapida de autenticacion

Crear primer admin, solo si no existe ningun usuario:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/bootstrap \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Admin TraceOps","email":"admin@traceops.local","password":"TraceOps2026!"}'
```

Login:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@traceops.local","password":"TraceOps2026!"}'
```

Consultar usuario autenticado:

```bash
TOKEN="pega_aqui_el_access_token"
curl http://127.0.0.1:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

## CRUD de usuarios

Listar roles:

```bash
curl http://127.0.0.1:8000/api/v1/users/roles \
  -H "Authorization: Bearer $TOKEN"
```

Crear tecnico:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Tecnico Demo","email":"tecnico.demo@traceops.local","password":"Tecnico2026!","role_code":"TECNICO","phone":"999999999"}'
```

Listar usuarios:

```bash
curl http://127.0.0.1:8000/api/v1/users \
  -H "Authorization: Bearer $TOKEN"
```

Filtrar por rol:

```bash
curl "http://127.0.0.1:8000/api/v1/users?role_code=TECNICO&is_active=true" \
  -H "Authorization: Bearer $TOKEN"
```

## Contratas y cuadrillas

Crear contrata:

```bash
CONTRACTOR_ID=$(curl -s -X POST http://127.0.0.1:8000/api/v1/contractors \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Contrata Demo","tax_id":"20123456789","type":"CONTRATA"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
```

Crear supervisor:

```bash
SUPERVISOR_ID=$(curl -s -X POST http://127.0.0.1:8000/api/v1/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Supervisor Demo","email":"supervisor.demo@traceops.local","password":"Supervisor2026!","role_code":"SUPERVISOR"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
```

Crear tecnico:

```bash
TECHNICIAN_ID=$(curl -s -X POST http://127.0.0.1:8000/api/v1/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Tecnico Campo Demo","email":"tecnico.campo@traceops.local","password":"Tecnico2026!","role_code":"TECNICO"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
```

Crear cuadrilla:

```bash
CREW_ID=$(curl -s -X POST http://127.0.0.1:8000/api/v1/crews \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"contractor_id\":\"$CONTRACTOR_ID\",\"code\":\"CQ-DEMO-01\",\"name\":\"Cuadrilla Demo 01\",\"supervisor_id\":\"$SUPERVISOR_ID\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
```

Agregar tecnico a cuadrilla:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/crews/$CREW_ID/members \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$TECHNICIAN_ID\",\"position\":\"TECNICO_LIDER\"}"
```

Asignar proyecto:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/projects/$PROJECT_ID/assign \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"supervisor_id\":\"$SUPERVISOR_ID\",\"contractor_id\":\"$CONTRACTOR_ID\",\"crew_id\":\"$CREW_ID\",\"technician_id\":\"$TECHNICIAN_ID\"}"
```

## Predios y proyectos

Crear predio:

```bash
PROPERTY_ID=$(curl -s -X POST http://127.0.0.1:8000/api/v1/properties \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"external_property_id":"WIN-DEMO-001","source":"WIN","address":"Av. Demo 123","district":"Lima","node_code":"NODO-01","latitude":-12.0464,"longitude":-77.0428}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
```

Crear proyecto:

```bash
PROJECT_ID=$(curl -s -X POST http://127.0.0.1:8000/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"property_id\":\"$PROPERTY_ID\",\"project_code\":\"PEXT-DEMO-001\",\"project_type\":\"PEXT\",\"name\":\"Demo PEXT 001\",\"priority\":\"MEDIA\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
```

Listar proyectos:

```bash
curl http://127.0.0.1:8000/api/v1/projects \
  -H "Authorization: Bearer $TOKEN"
```

Cambiar estado:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/projects/$PROJECT_ID/transition \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to_status":"FACTIBILIDAD_EN_REVISION","reason":"Inicio de factibilidad"}'
```

## PEXT: prefactibilidad y cuadro de empalme

Registrar prefactibilidad del predio desde campo:

El endpoint acepta los campos operativos de la ficha real PEXT: nombre de edificio, condominio, tipo/subtipo de proyecto, origen, clasificacion, construccion, acceso autorizado, responsables, visita tecnica, direccion normalizada, coordenadas, totales de torres/hogares, datos GCA, `towers` y `tower_contacts`.

```bash
curl -X PUT http://127.0.0.1:8000/api/v1/pext/projects/$PROJECT_ID/prefeasibility \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "visit_date":"2026-06-01",
    "contact_name":"Contacto Demo",
    "contact_phone":"999888777",
    "address_confirmed":true,
    "building_type":"EDIFICIO",
    "access_type":"CONSERJERIA",
    "tower_count":1,
    "floor_count":12,
    "riser_count":2,
    "hp_count":48,
    "existing_fo":false,
    "nearest_node_code":"NODO-01",
    "distance_to_node_m":180,
    "feeder_mufa_code":"MF-DEMO-001",
    "requires_oc":true,
    "oc_distance_m":35,
    "canalization_type":"VEREDA",
    "poles_required":0,
    "nap_required_count":4,
    "splitter_required":"1:8",
    "estimated_power_dbm":-19.5,
    "latitude":-12.0464,
    "longitude":-77.0428,
    "gps_accuracy_m":8,
    "feasibility_result":"PREFACTIBLE",
    "risks":"Acceso sujeto a autorizacion de administracion",
    "restrictions":"Coordinar ingreso a cuarto tecnico",
    "observations":"Predio apto para PEXT",
    "metadata":{"captured_from":"mobile_app"}
  }'
```

Crear cuadro de empalme:

```bash
SPLICE_CHART_ID=$(curl -s -X POST http://127.0.0.1:8000/api/v1/pext/projects/$PROJECT_ID/splice-charts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mufa_code":"MF-DEMO-001","mufa_type":"NUEVA","node_code":"NODO-01","cable_in":"Cable alimentador 48H","cable_out":"Cable distribucion 12H","fiber_capacity":"48H"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)[\"id\"])")
```

Agregar fila al cuadro de empalme:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/pext/splice-charts/$SPLICE_CHART_ID/entries \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sequence_number":1,"tray":"Bandeja 1","tube_color":"Azul","fiber_in_number":1,"fiber_in_color":"Azul","fiber_out_number":1,"fiber_out_color":"Azul","service_type":"NAP","nap_code":"NAP-DEMO-01","destination":"Torre 1 / Montante 1","signal_dbm":-20.1}'
```

Consultar salida consolidada de campo:

```bash
curl http://127.0.0.1:8000/api/v1/pext/projects/$PROJECT_ID/field-output \
  -H "Authorization: Bearer $TOKEN"
```

Incluye proyecto, predio, ficha PEXT, torres/responsables, cuadros de empalme, evidencias con GPS y archivos asociados.

Validar completitud antes de revision/liquidacion:

```bash
curl http://127.0.0.1:8000/api/v1/pext/projects/$PROJECT_ID/field-output/validation \
  -H "Authorization: Bearer $TOKEN"
```

Devuelve `is_complete`, errores bloqueantes, advertencias y conteo esperado/real de evidencias.

## App movil: bandeja tecnica

Login como tecnico:

```bash
TECH_TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"tecnico.campo@traceops.local","password":"Tecnico2026!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)[\"access_token\"])")
```

Ver proyectos asignados al tecnico:

```bash
curl http://127.0.0.1:8000/api/v1/mobile/my-projects \
  -H "Authorization: Bearer $TECH_TOKEN"
```

Descargar paquete de campo para la app:

```bash
curl http://127.0.0.1:8000/api/v1/mobile/projects/$PROJECT_ID/field-package \
  -H "Authorization: Bearer $TECH_TOKEN"
```

El paquete de campo incluye:

```text
forms.prefeasibility  -> secciones y campos de la ficha PEXT real
forms.splice_chart    -> cabecera del cuadro de empalme por MUFA
forms.splice_entry    -> filas repetibles del cuadro de empalme
requirements          -> evidencias minimas con GPS que la app debe capturar
```

## Evidencias PEXT con GPS

Crear metadata de evidencia desde app movil:

```bash
EVIDENCE_ID=$(curl -s -X POST http://127.0.0.1:8000/api/v1/evidences \
  -H "Authorization: Bearer $TECH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id":"'"$PROJECT_ID"'",
    "category":"MUFA",
    "subcategory":"MUFA_NUEVA",
    "associated_code":"MF-DEMO-001",
    "element_type":"MUFA",
    "splice_chart_id":"'"$SPLICE_CHART_ID"'",
    "local_client_uuid":"11111111-1111-4111-8111-111111111111",
    "captured_at":"2026-06-01T10:30:00-05:00",
    "latitude":-12.0464,
    "longitude":-77.0428,
    "gps_accuracy_m":8,
    "gps_provider":"gps",
    "checksum_sha256":"demo-checksum-mufa-001",
    "metadata":{"capture_source":"mobile_app","pending_file_upload":true}
  }' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)[\"id\"])")
```

Listar evidencias del proyecto:

```bash
curl http://127.0.0.1:8000/api/v1/evidences/project/$PROJECT_ID/items \
  -H "Authorization: Bearer $TOKEN"
```

## Archivos de evidencia en MinIO

Flujo recomendado para app movil:

```text
1. Crear metadata de evidencia.
2. Solicitar URL prefirmada.
3. Subir foto comprimida directo a MinIO con PUT.
4. Confirmar upload para registrar `files` y asociar `file_id` a la evidencia.
```

Solicitar URL de carga:

```bash
PRESIGN_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/v1/files/presign-upload \
  -H "Authorization: Bearer $TECH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id":"'"$PROJECT_ID"'",
    "evidence_id":"'"$EVIDENCE_ID"'",
    "filename":"mufa-demo.jpg",
    "mime_type":"image/jpeg",
    "file_kind":"IMAGE",
    "checksum_sha256":"demo-checksum-mufa-001"
  }')
```

Subir archivo:

```bash
UPLOAD_URL=$(echo "$PRESIGN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)[\"upload_url\"])")
OBJECT_KEY=$(echo "$PRESIGN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)[\"object_key\"])")
printf "demo image bytes for TraceOps evidence" > /tmp/mufa-demo.jpg
curl -X PUT "$UPLOAD_URL" -H "Content-Type: image/jpeg" --data-binary @/tmp/mufa-demo.jpg
```

Completar upload:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/files/complete-upload \
  -H "Authorization: Bearer $TECH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bucket":"traceops-local",
    "object_key":"'"$OBJECT_KEY"'",
    "original_filename":"mufa-demo.jpg",
    "mime_type":"image/jpeg",
    "size_bytes":35,
    "checksum_sha256":"demo-checksum-mufa-001",
    "file_kind":"IMAGE",
    "evidence_id":"'"$EVIDENCE_ID"'"
  }'
```

## Siguiente desarrollo

1. Endpoint de sincronizacion offline-first.
2. Validaciones de cierre por evidencias minimas.
3. Web Console MVP para gestor/supervisor/admin.
4. App Flutter: bandeja, paquete de campo, captura offline y subida de fotos.
5. Generacion KMZ con evidencias georreferenciadas.
