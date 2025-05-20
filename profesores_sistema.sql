CREATE DATABASE IF NOT EXISTS profesores;

USE profesores;

CREATE TABLE `usuarios` (
    `id_usuarios` INT(11) NOT NULL AUTO_INCREMENT,
    `nombre_usuario` VARCHAR(50) NOT NULL,
    `contrasena` VARCHAR(50) NOT NULL,
    `tipo_usuario` TINYINT(1) NOT NULL,
    PRIMARY KEY (`id_usuarios`)
)  ENGINE=INNODB;

CREATE TABLE `categoria_profesor` (
    `id_categoria_profesor` INT(11) NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(50) NOT NULL,
    PRIMARY KEY (`id_categoria_profesor`)
)  ENGINE=INNODB;

CREATE TABLE `grado_academico` (
    `id_grado_academico` INT(11) NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(50) NOT NULL,
    PRIMARY KEY (`id_grado_academico`)
)  ENGINE=INNODB;

CREATE TABLE `genero` (
    `id_genero` INT(11) NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(50) NOT NULL,
    PRIMARY KEY (`id_genero`)
)  ENGINE=INNODB;

CREATE TABLE `profesores` (
    `id_profesor` INT(11) NOT NULL AUTO_INCREMENT,
    `numero_trabajador` VARCHAR(45) NOT NULL,
    `nombre_completo` VARCHAR(100) NOT NULL,
    `fk_id_genero` INT(11) NOT NULL,
    `rfc` VARCHAR(45) NOT NULL,
    `curp` VARCHAR(45) NOT NULL,
	`fk_id_categoria_profesor` INT(11) NOT NULL,
	`fk_id_grado_academico` INT(11) NOT NULL,
	`antiguedad_unam` VARCHAR(45) NOT NULL,
    `antiguedad_carrera` VARCHAR(45) NOT NULL,
    `correo` VARCHAR(45) NOT NULL,
    `numero_casa` VARCHAR(45) NOT NULL,
    `numero_celular` VARCHAR(45) NOT NULL,
    `direccion` VARCHAR(100) NOT NULL,
    PRIMARY KEY (`id_profesor`),
    KEY `fk_id_genero` (`fk_id_genero`),
    KEY `fk_id_categoria_profesor` (`fk_id_categoria_profesor`),
    KEY `fk_id_grado_academico` (`fk_id_grado_academico`),
    CONSTRAINT `fk_id_genero` FOREIGN KEY (`fk_id_genero`)
        REFERENCES `genero` (`id_genero`),
    CONSTRAINT `fk_id_categoria_profesor` FOREIGN KEY (`fk_id_categoria_profesor`)
        REFERENCES `categoria_profesor` (`id_categoria_profesor`),
    CONSTRAINT `fk_id_grado_academico` FOREIGN KEY (`fk_id_grado_academico`)
        REFERENCES `grado_academico` (`id_grado_academico`)

)  ENGINE=INNODB;