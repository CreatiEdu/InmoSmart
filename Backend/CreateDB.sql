-- Active: 1790643696354@@q4os-desktop.tailec0f82.ts.net@3306@inmosmart
CREATE TABLE `usuario` (
    `id_usuario` integer PRIMARY KEY,
    `nombre` varchar(255),
    `email` varchar(255) UNIQUE,
    `password` varchar(255),
    `telefono` varchar(255),
    `dni` varchar(255) UNIQUE,
    `id_rol` integer
);

CREATE TABLE `contacto` (
    `id_contacto` integer AUTO_INCREMENT PRIMARY KEY,
    `nombre` varchar(255),
    `email` varchar(255),
    `telefono` varchar(255),
    `asunto` varchar(100),
    `mensaje` text,
    `fecha_envio` datetime
);

CREATE TABLE `roles` (
    `id_rol` integer AUTO_INCREMENT PRIMARY KEY,
    `nombre_rol` varchar(255)
);

CREATE TABLE `propiedad` (
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

CREATE TABLE `tipopropiedad` (
    `id_tipo` integer PRIMARY KEY,
    `nombre_tipo` varchar(255)
);

CREATE TABLE `propiedadestado` (
    `id_estado` integer PRIMARY KEY,
    `nombre_estado` varchar(255)
);

CREATE TABLE `contratos` (
    `id_contrato` integer AUTO_INCREMENT PRIMARY KEY,
    `id_inquilino_comprador` integer,
    `fecha_inicio` date,
    `fecha_fin` date,
    `monto` decimal,
    `url_documento_firmado` varchar(255),
    `id_propiedad` integer
);

CREATE TABLE `favoritos` (
    `id_favorito` integer PRIMARY KEY,
    `id_propiedad` integer,
    `id_usuario` integer
);
    
ALTER TABLE `usuario`
ADD CONSTRAINT `Tiene_Rol` FOREIGN KEY (`id_rol`) REFERENCES `roles` (`id_rol`);

ALTER TABLE `propiedad`
ADD CONSTRAINT `Gestiona` FOREIGN KEY (`id_gestor`) REFERENCES `usuario` (`id_usuario`);

ALTER TABLE `propiedad`
ADD CONSTRAINT `Es_Tipo` FOREIGN KEY (`id_tipo`) REFERENCES `tipopropiedad` (`id_tipo`);

ALTER TABLE `propiedad`
ADD CONSTRAINT `Tiene_Estado` FOREIGN KEY (`id_estado`) REFERENCES `propiedadestado` (`id_estado`);

ALTER TABLE `contratos`
ADD CONSTRAINT `Tiene_Propiedad` FOREIGN KEY (`id_propiedad`) REFERENCES `propiedad` (`id_propiedad`);

ALTER TABLE `contratos`
ADD CONSTRAINT `Puede_ver` FOREIGN KEY (`id_inquilino_comprador`) REFERENCES `usuario` (`id_usuario`);

ALTER TABLE `favoritos`
ADD CONSTRAINT `Marca` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id_usuario`);

ALTER TABLE `favoritos`
ADD CONSTRAINT `Es_marcada` FOREIGN KEY (`id_propiedad`) REFERENCES `propiedad` (`id_propiedad`);