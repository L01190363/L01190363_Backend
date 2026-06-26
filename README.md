# L01190363_Backend

# Backend — Directorio de Materias y Docentes

API REST que gestiona un directorio de **materias** y sus **docentes**.
Proyecto Integrador del curso *CloudCoder: Codespaces, GitHub y Copilot en la nube*.

Este README es una guía paso a paso para reproducir el backend desde cero en
GitHub Codespaces, explicando **qué hace y por qué** cada paso.

---

## ¿Cómo funciona? (la idea en una línea)

```
Navegador / curl  ->  Flask (puerto 5000)  ->  MySQL (Docker, puerto 3306)
```

El cliente hace una petición HTTP, **Flask** la traduce a una consulta SQL,
**MySQL** responde con los datos y Flask los devuelve como JSON.

---

## Los archivos del proyecto

Antes de los pasos, conoce las piezas. El repositorio tiene esta estructura:

```
backend-directorio/
├── .devcontainer/
│   └── devcontainer.json   -> Configura el entorno y lo automatiza
├── directorio.sql          -> Crea la base de datos y carga datos
├── ws_directorio.py        -> El servidor con los endpoints
└── README.md
```

### 1. `directorio.sql` — la base de datos

Define **dos tablas**: `materias` y `docentes`. La llave foránea conecta cada
docente con su materia. Usa `RESTRICT` (por defecto en MySQL): **no deja borrar
una materia si tiene docentes asignados** — así se protege la integridad de los datos.

```sql
-- ============================================================
--  directorio.sql  ·  Proyecto Integrador (Sesión 5)
--  Base de datos: Directorio de Materias y Docentes
-- ============================================================

CREATE DATABASE IF NOT EXISTS directorio;
USE directorio;

-- ------------------------------------------------------------
--  Tabla: materias
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS materias (
  id       INT AUTO_INCREMENT PRIMARY KEY,
  clave    VARCHAR(20)  UNIQUE NOT NULL,
  nombre   VARCHAR(100) NOT NULL,
  creditos INT
);

-- ------------------------------------------------------------
--  Tabla: docentes
--  La FK NO declara ON DELETE -> MySQL usa RESTRICT por defecto:
--  no se podrá borrar una materia que tenga docentes asignados.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS docentes (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  nombre     VARCHAR(100) NOT NULL,
  email      VARCHAR(100) UNIQUE NOT NULL,
  materia_id INT,
  FOREIGN KEY (materia_id) REFERENCES materias(id)
);

-- ------------------------------------------------------------
--  Datos iniciales
-- ------------------------------------------------------------
INSERT INTO materias (clave, nombre, creditos) VALUES
  ('TC1028',  'Programación en Python',    5),
  ('TC1004B', 'Implementación de IoT',     4),
  ('TC2005B', 'Construcción de Software',  5);

INSERT INTO docentes (nombre, email, materia_id) VALUES
  ('Ana Torres',  'ana.torres@tec.mx',   1),
  ('Luis Méndez', 'luis.mendez@tec.mx',  3);
```

### 2. `ws_directorio.py` — el servidor Flask

Expone los **8 endpoints** de la API. Cada función recibe una petición, consulta
MySQL y responde en JSON. Incluye validaciones (campos obligatorios, materia
existente) para devolver errores claros en vez de fallas crudas.

```python
"""
ws_directorio.py  ·  Proyecto Integrador (Sesión 5)
Backend REST: Directorio de Materias y Docentes
Flask + mysql-connector-python + flask-cors
"""

import os
import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Permite que el frontend (otro puerto/origen) consuma la API

# ------------------------------------------------------------
#  Configuración de conexión
#  Usa variables de entorno con valores por defecto que coinciden
#  con el contenedor MySQL de la guía de arranque rápido.
# ------------------------------------------------------------
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "contrasena"),
    "database": os.getenv("DB_NAME", "directorio"),
}


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


# ============================================================
#  MATERIAS
# ============================================================

@app.get("/materias")
def listar_materias():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM materias ORDER BY id")
    filas = cur.fetchall()
    cur.close(); db.close()
    return jsonify(filas)


@app.get("/materias/<int:id>")
def obtener_materia(id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM materias WHERE id = %s", (id,))
    fila = cur.fetchone()
    cur.close(); db.close()
    if fila is None:
        return jsonify({"error": "Materia no encontrada"}), 404
    return jsonify(fila)


@app.post("/materias")
def crear_materia():
    data = request.get_json(silent=True) or {}
    clave    = data.get("clave")
    nombre   = data.get("nombre")
    creditos = data.get("creditos")

    if not clave or not nombre:
        return jsonify({"error": "clave y nombre son obligatorios"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute(
            "INSERT INTO materias (clave, nombre, creditos) VALUES (%s, %s, %s)",
            (clave, nombre, creditos),
        )
        db.commit()
        cur.execute("SELECT * FROM materias WHERE id = %s", (cur.lastrowid,))
        return jsonify(cur.fetchone()), 201
    except mysql.connector.IntegrityError:
        return jsonify({"error": f"La clave '{clave}' ya existe"}), 409
    finally:
        cur.close(); db.close()


@app.put("/materias/<int:id>")
def actualizar_materia(id):
    data = request.get_json(silent=True) or {}
    clave    = data.get("clave")
    nombre   = data.get("nombre")
    creditos = data.get("creditos")

    if not clave or not nombre:
        return jsonify({"error": "clave y nombre son obligatorios"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT id FROM materias WHERE id = %s", (id,))
        if cur.fetchone() is None:
            return jsonify({"error": "Materia no encontrada"}), 404

        cur.execute(
            "UPDATE materias SET clave = %s, nombre = %s, creditos = %s WHERE id = %s",
            (clave, nombre, creditos, id),
        )
        db.commit()
        cur.execute("SELECT * FROM materias WHERE id = %s", (id,))
        return jsonify(cur.fetchone())
    except mysql.connector.IntegrityError:
        return jsonify({"error": f"La clave '{clave}' ya existe"}), 409
    finally:
        cur.close(); db.close()


@app.delete("/materias/<int:id>")
def eliminar_materia(id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT id FROM materias WHERE id = %s", (id,))
        if cur.fetchone() is None:
            return jsonify({"error": "Materia no encontrada"}), 404

        cur.execute("DELETE FROM materias WHERE id = %s", (id,))
        db.commit()
        return "", 204  # No Content
    except mysql.connector.IntegrityError:
        # La FK con RESTRICT bloquea el borrado si hay docentes asignados
        return jsonify({
            "error": "No se puede eliminar: hay docentes asignados a esta materia"
        }), 409
    finally:
        cur.close(); db.close()


# ============================================================
#  DOCENTES
# ============================================================

@app.get("/docentes")
def listar_docentes():
    db = get_db()
    cur = db.cursor(dictionary=True)
    # LEFT JOIN para traer también el nombre de la materia asignada
    cur.execute("""
        SELECT d.id, d.nombre, d.email, d.materia_id,
               m.nombre AS materia_nombre
        FROM docentes d
        LEFT JOIN materias m ON d.materia_id = m.id
        ORDER BY d.id
    """)
    filas = cur.fetchall()
    cur.close(); db.close()
    return jsonify(filas)


@app.post("/docentes")
def crear_docente():
    data = request.get_json(silent=True) or {}
    nombre     = data.get("nombre")
    email      = data.get("email")
    materia_id = data.get("materia_id")

    if not nombre or not email:
        return jsonify({"error": "nombre y email son obligatorios"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        # Validación de integridad referencial manual:
        # si mandan materia_id, comprobamos que exista antes de insertar.
        if materia_id is not None:
            cur.execute("SELECT id FROM materias WHERE id = %s", (materia_id,))
            if cur.fetchone() is None:
                return jsonify({"error": f"La materia_id {materia_id} no existe"}), 400

        cur.execute(
            "INSERT INTO docentes (nombre, email, materia_id) VALUES (%s, %s, %s)",
            (nombre, email, materia_id),
        )
        db.commit()
        cur.execute("SELECT * FROM docentes WHERE id = %s", (cur.lastrowid,))
        return jsonify(cur.fetchone()), 201
    except mysql.connector.IntegrityError:
        return jsonify({"error": f"El email '{email}' ya está registrado"}), 409
    finally:
        cur.close(); db.close()


@app.delete("/docentes/<int:id>")
def eliminar_docente(id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id FROM docentes WHERE id = %s", (id,))
    if cur.fetchone() is None:
        cur.close(); db.close()
        return jsonify({"error": "Docente no encontrado"}), 404

    cur.execute("DELETE FROM docentes WHERE id = %s", (id,))
    db.commit()
    cur.close(); db.close()
    return "", 204  # No Content


# ============================================================
#  Arranque
# ============================================================
if __name__ == "__main__":
    # host 0.0.0.0 para que el puerto sea accesible desde el Codespace
    app.run(host="0.0.0.0", port=5000, debug=True)
```

### 3. `.devcontainer/devcontainer.json` — la automatización

Es la clave de la reproducibilidad. Su `postCreateCommand` se ejecuta **solo** al
crear el Codespace y hace por ti: levantar MySQL, esperar a que esté listo, cargar
el `.sql` e instalar las dependencias. El alumno no instala nada manualmente.

```jsonc
{
  // Configuración del Codespace para el backend Flask + MySQL.
  "name": "Backend Flask + MySQL",
  "image": "mcr.microsoft.com/devcontainers/base:ubuntu",

  // Features: Docker (para correr MySQL) y Python 3.12.
  "features": {
    "ghcr.io/devcontainers/features/docker-outside-of-docker:1": {},
    "ghcr.io/devcontainers/features/python:1": { "version": "3.12" }
  },

  // Se ejecuta UNA vez al crear el Codespace. Automatiza:
  //   1. Limpia un contenedor previo con el mismo nombre (idempotente).
  //   2. Levanta MySQL en Docker.
  //   3. Espera a que MySQL acepte conexiones (en vez de un sleep fijo).
  //   4. Carga el esquema y los datos desde directorio.sql.
  //   5. Instala las dependencias de Python.
  "postCreateCommand": "docker rm -f mysql-directorio 2>/dev/null; docker run --name mysql-directorio -e MYSQL_ROOT_PASSWORD=contrasena -e MYSQL_DATABASE=directorio -p 3306:3306 -d mysql:latest && echo 'Esperando a que MySQL este listo...' && until docker exec mysql-directorio mysql -u root -pcontrasena -e 'SELECT 1' directorio >/dev/null 2>&1; do sleep 2; done && docker exec -i mysql-directorio mysql -u root -pcontrasena directorio < directorio.sql && pip install mysql-connector-python flask flask-cors && echo 'Backend listo: ejecuta  python ws_directorio.py'",

  // Reenvía el puerto del servidor Flask.
  "forwardPorts": [5000],
  "portsAttributes": {
    "5000": { "label": "Backend Flask" }
  },

  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.pylint",
        "humao.rest-client"
      ]
    }
  },

  "remoteUser": "vscode"
}
```

---

## Puesta en marcha — paso a paso

### Paso 1 · Sube los 4 archivos al repositorio

Sube `directorio.sql`, `ws_directorio.py`, `README.md` y
`.devcontainer/devcontainer.json` a tu repo en GitHub.

> **Por qué primero:** el Codespace ejecuta una automatización al construirse que
> *lee* estos archivos. Si no están presentes antes, esa automatización falla.

### Paso 2 · Crea el Codespace

En el repositorio: **Code -> Codespaces -> Create codespace on main**.

> **Qué pasa aquí:** al abrirlo, el `devcontainer.json` arma el entorno y dispara
> el `postCreateCommand`, que monta MySQL, carga los datos e instala las
> dependencias **automáticamente**.

### Paso 3 · Espera a que termine la construcción

Observa el log de la terminal mientras se construye.

> **Qué observar:** verás repetirse `Esperando a que MySQL este listo...` y, al
> final, el mensaje `Backend listo: ejecuta python ws_directorio.py`. Eso confirma
> que la base de datos quedó montada y cargada.

### Paso 4 · Arranca el servidor

```bash
python ws_directorio.py
```

> **Qué hace:** pone a Flask a escuchar peticiones HTTP en el **puerto 5000**.
> La terminal queda ocupada con el servidor corriendo (es normal).

### Paso 5 · Haz público el puerto 5000

En la pestaña **Ports**: clic derecho sobre el puerto 5000 ->
**Port Visibility -> Public**.

> **Por qué:** los puertos del Codespace son privados por defecto. Al hacerlo
> público, el frontend (y curl desde fuera) pueden alcanzar la API.
> **Copia esa URL** — la usará el frontend.

### Paso 6 · Comprueba que responde

En **otra** terminal (la primera está ocupada con el servidor):

```bash
curl http://localhost:5000/materias
```

> **Qué confirma:** si devuelve las tres materias en JSON, las tres capas
> (Flask + MySQL + datos) están conectadas y funcionando.

---

## Pruebas completas de la API

Estas pruebas cubren los 8 endpoints. Útiles para verificar todo el CRUD.

### Materias

```bash
# Listar todas
curl http://localhost:5000/materias

# Obtener una
curl http://localhost:5000/materias/1

# Crear
curl -X POST http://localhost:5000/materias \
  -H "Content-Type: application/json" \
  -d '{"clave":"TC3001","nombre":"Bases de Datos","creditos":6}'

# Actualizar
curl -X PUT http://localhost:5000/materias/1 \
  -H "Content-Type: application/json" \
  -d '{"clave":"TC1028","nombre":"Programación en Python","creditos":6}'

# Eliminar
curl -X DELETE http://localhost:5000/materias/1
```

### Docentes

```bash
# Listar (incluye el nombre de su materia por el JOIN)
curl http://localhost:5000/docentes

# Crear ligado a una materia
curl -X POST http://localhost:5000/docentes \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Carla Ruiz","email":"carla.ruiz@tec.mx","materia_id":2}'

# Eliminar
curl -X DELETE http://localhost:5000/docentes/1
```

### Probar la integridad referencial

Borrar una materia que tiene docentes debe devolver `409` (no se permite):

```bash
curl -i -X DELETE http://localhost:5000/materias/1
# -> HTTP/1.1 409 CONFLICT
# -> {"error": "No se puede eliminar: hay docentes asignados a esta materia"}
```

---

## Referencia rápida de endpoints

| Recurso  | Método   | Ruta              | Descripción                |
|----------|----------|-------------------|----------------------------|
| Materias | `GET`    | `/materias`       | Listar todas               |
| Materias | `GET`    | `/materias/<id>`  | Obtener una                |
| Materias | `POST`   | `/materias`       | Crear                      |
| Materias | `PUT`    | `/materias/<id>`  | Actualizar                 |
| Materias | `DELETE` | `/materias/<id>`  | Eliminar                   |
| Docentes | `GET`    | `/docentes`       | Listar todos (con materia) |
| Docentes | `POST`   | `/docentes`       | Crear                      |
| Docentes | `DELETE` | `/docentes/<id>`  | Eliminar                   |

> **Nota:** el `postCreateCommand` corre solo al *crear* el Codespace. Si lo
> detienes y reanudas, reinicia MySQL con `docker start mysql-directorio`.
