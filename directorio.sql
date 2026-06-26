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
