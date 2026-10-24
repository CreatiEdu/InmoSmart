-- Active: 1780184813602@@inmosmart.duckdns.org@3306@inmosmart
CREATE TABLE `Usuarios` (
    `id_usuario` integer PRIMARY KEY,
    `nombre` varchar(255),
    `email` varchar(255) UNIQUE,
    `password` varchar(255),
    `telefono` varchar(255),
    `dni` varchar(255) UNIQUE,
    `id_rol` integer,
    `activo` boolean
);

CREATE TABLE `Contacto` (
    `id_contacto` integer AUTO_INCREMENT PRIMARY KEY,
    `nombre` varchar(255),
    `email` varchar(255),
    `telefono` varchar(255),
    `asunto` varchar(100),
    `mensaje` text,
    `fecha_envio` datetime
);

CREATE TABLE `Roles` (
    `id_rol` integer PRIMARY KEY,
    `nombre_rol` varchar(255)
);

CREATE TABLE `Propiedad` (
    `id_propiedad` integer PRIMARY KEY AUTO_INCREMENT,
    `titulo` varchar(255),
    `descripcion` text,
    `precio` decimal,
    `habitaciones` integer,
    `baños` integer,
    `superficie` float,
    `acepta_mascotas` boolean,
    `id_tipo` integer,
    `id_estado` integer,
    `id_gestor` integer,
    `fecha_creacion` date,
    `imagen_1` MEDIUMBLOB,
    `imagen_2` MEDIUMBLOB,
    `imagen_3` MEDIUMBLOB
);

CREATE TABLE `TipoPropiedad` (
    `id_tipo` integer PRIMARY KEY,
    `nombre_tipo` varchar(255)
);

CREATE TABLE `PropiedadEstado` (
    `id_estado` integer PRIMARY KEY,
    `nombre_estado` varchar(255)
);

CREATE TABLE `Contractos` (
    `id_contrato` integer PRIMARY KEY,
    `id_inquilino_comprador` integer,
    `fecha_inicio` date,
    `fecha_fin` date,
    `monto` decimal,
    `url_documento_firmado` varchar(255),
    `id_propiedad` integer
);

CREATE TABLE `Favoritos` (
    `id_favorito` integer PRIMARY KEY,
    `id_propiedad` integer,
    `id_usuario` integer
);

ALTER TABLE `Usuarios`
ADD CONSTRAINT `Tiene_Rol` FOREIGN KEY (`id_rol`) REFERENCES `Roles` (`id_rol`);

ALTER TABLE `Propiedad`
ADD CONSTRAINT `Gestiona` FOREIGN KEY (`id_gestor`) REFERENCES `Usuarios` (`id_usuario`);

ALTER TABLE `Propiedad`
ADD CONSTRAINT `Es_Tipo` FOREIGN KEY (`id_tipo`) REFERENCES `TipoPropiedad` (`id_tipo`);

ALTER TABLE `Propiedad`
ADD CONSTRAINT `Tiene_Estado` FOREIGN KEY (`id_estado`) REFERENCES `PropiedadEstado` (`id_estado`);

ALTER TABLE `Contractos`
ADD CONSTRAINT `Tiene_Propiedad` FOREIGN KEY (`id_propiedad`) REFERENCES `Propiedad` (`id_propiedad`);

ALTER TABLE `Contractos`
ADD CONSTRAINT `Puede_ver` FOREIGN KEY (`id_inquilino_comprador`) REFERENCES `Usuarios` (`id_usuario`);

ALTER TABLE `Favoritos`
ADD CONSTRAINT `Marca` FOREIGN KEY (`id_usuario`) REFERENCES `Usuarios` (`id_usuario`);

ALTER TABLE `Favoritos`
ADD CONSTRAINT `Es_marcada` FOREIGN KEY (`id_propiedad`) REFERENCES `Propiedad` (`id_propiedad`);