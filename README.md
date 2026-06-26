# L01190363_Backend


Readme · MD
# Backend — Directorio de Materias y Docentes
 
API REST que gestiona un directorio de **materias** y los **docentes** asignados a cada una.
Forma parte del Proyecto Integrador del curso *CloudCoder: Codespaces, GitHub y Copilot en la nube*.
 
## Stack
 
- **Lenguaje:** Python 3.12
- **Framework:** Flask
- **Base de datos:** MySQL (en contenedor Docker)
- **Conector:** `mysql-connector-python`
- **CORS:** `flask-cors` (para que el frontend lo consuma desde otro puerto)
- **Entorno:** GitHub Codespaces + `devcontainer.json`
## Estructura del repositorio
 
```
backend-directorio/
├── .devcontainer/
│   └── devcontainer.json
├── directorio.sql       ← Esquema + datos iniciales
├── ws_directorio.py     ← Servidor Flask con los endpoints
└── README.md
```
 
## Modelo de datos
 
Dos tablas con una relación uno-a-muchos (una materia tiene varios docentes):
 
| Tabla      | Campos                                              |
|------------|-----------------------------------------------------|
| `materias` | `id`, `clave` (único), `nombre`, `creditos`         |
| `docentes` | `id`, `nombre`, `email` (único), `materia_id` (FK)  |
 
> La llave foránea `docentes.materia_id` usa `RESTRICT` (comportamiento por
> defecto de MySQL): **no se puede eliminar una materia que tenga docentes
> asignados**. El backend atrapa este caso y devuelve un `409` con mensaje claro.
 
## Cómo reproducir el proyecto
 
Todos los pasos se ejecutan dentro del Codespace del repositorio.
 
### 1. Levantar MySQL en Docker
 
```bash
docker run --name mysql-directorio \
  -e MYSQL_ROOT_PASSWORD=contrasena \
  -e MYSQL_DATABASE=directorio \
  -p 3306:3306 \
  -d mysql:latest
```
 
### 2. Crear las tablas y cargar datos iniciales
 
Espera ~15 segundos a que MySQL termine de arrancar y luego ejecuta:
 
```bash
docker exec -i mysql-directorio mysql -u root -pcontrasena directorio < directorio.sql
```
 
### 3. Instalar dependencias
 
```bash
pip install mysql-connector-python flask flask-cors
```
 
### 4. Arrancar el servidor
 
```bash
python ws_directorio.py
```
 
El servidor queda escuchando en el **puerto 5000**.
 
### 5. Exponer el puerto
 
En la pestaña **Ports** de VS Code, marca el **puerto 5000** como **Public**.
Copia esa URL: la necesitarás para conectar el frontend.
 
## Configuración (variables de entorno)
 
El servidor lee la conexión desde variables de entorno, con valores por defecto
que coinciden con el contenedor de arriba. Solo necesitas cambiarlas si modificas
el `docker run`.
 
| Variable      | Valor por defecto |
|---------------|-------------------|
| `DB_HOST`     | `localhost`       |
| `DB_USER`     | `root`            |
| `DB_PASSWORD` | `contrasena`      |
| `DB_NAME`     | `directorio`      |
 
## Endpoints
 
| Recurso  | Método   | Ruta              | Descripción            |
|----------|----------|-------------------|------------------------|
| Materias | `GET`    | `/materias`       | Listar todas           |
| Materias | `GET`    | `/materias/<id>`  | Obtener una            |
| Materias | `POST`   | `/materias`       | Crear                  |
| Materias | `PUT`    | `/materias/<id>`  | Actualizar             |
| Materias | `DELETE` | `/materias/<id>`  | Eliminar               |
| Docentes | `GET`    | `/docentes`       | Listar todos (con materia) |
| Docentes | `POST`   | `/docentes`       | Crear                  |
| Docentes | `DELETE` | `/docentes/<id>`  | Eliminar               |
 
### Códigos de respuesta
 
| Código | Cuándo                                                        |
|--------|--------------------------------------------------------------|
| `200`  | Operación exitosa con cuerpo (GET, PUT)                       |
| `201`  | Recurso creado (POST)                                         |
| `204`  | Eliminado correctamente, sin cuerpo (DELETE)                 |
| `400`  | Faltan campos obligatorios o `materia_id` inexistente        |
| `404`  | El recurso no existe                                          |
| `409`  | Conflicto: clave/email duplicado o materia con docentes      |
 
## Probar la API con `curl`
 
> Sustituye `localhost:5000` por tu URL pública del Codespace si pruebas desde fuera.
 
```bash
# Listar materias
curl http://localhost:5000/materias
 
# Obtener una materia
curl http://localhost:5000/materias/1
 
# Crear una materia
curl -X POST http://localhost:5000/materias \
  -H "Content-Type: application/json" \
  -d '{"clave":"TC3001","nombre":"Bases de Datos","creditos":6}'
 
# Actualizar una materia
curl -X PUT http://localhost:5000/materias/1 \
  -H "Content-Type: application/json" \
  -d '{"clave":"TC1028","nombre":"Programación en Python","creditos":6}'
 
# Eliminar una materia
curl -X DELETE http://localhost:5000/materias/1
 
# Listar docentes (incluye el nombre de su materia)
curl http://localhost:5000/docentes
 
# Crear un docente
curl -X POST http://localhost:5000/docentes \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Carla Ruiz","email":"carla.ruiz@tec.mx","materia_id":2}'
 
# Eliminar un docente
curl -X DELETE http://localhost:5000/docentes/1
```
 
## Notas de diseño
 
- **CORS habilitado:** el frontend se sirve en otro puerto (8080), así que se
  permite el acceso desde cualquier origen para que los `fetch` no se bloqueen.
- **Validación referencial manual:** al crear un docente con `materia_id`, se
  verifica que la materia exista antes de insertar, devolviendo un error legible
  en vez de una falla cruda de la llave foránea.
- **`204 No Content` en los DELETE:** el frontend debe manejar esta respuesta
  sin intentar parsear JSON de un cuerpo vacío.
