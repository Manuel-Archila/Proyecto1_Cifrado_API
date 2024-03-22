CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL NOT NULL,
    public_key TEXT NOT NULL,
    username VARCHAR(30) NOT NULL UNIQUE,
    fecha_creacion TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS mensajes (
    id SERIAL NOT NULL,
    mensaje_cifrado TEXT NOT NULL,
    id_username_destino INTEGER NOT NULL,
    id_username_origen INTEGER NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (id_username_destino) REFERENCES usuarios(id),
    FOREIGN KEY (id_username_origen) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS grupos (
    id SERIAL NOT NULL,
    nombre VARCHAR(30) NOT NULL,
    contrasena TEXT NOT NULL,
    clave_simetrica TEXT NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS usuarios_grupos (
    id_usuario INTEGER NOT NULL,
    id_grupo INTEGER NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
    FOREIGN KEY (id_grupo) REFERENCES grupos(id)
);

CREATE TABLE IF NOT EXISTS mensajes_grupos (
    id_grupo INTEGER NOT NULL,
    author INTEGER NOT NULL,
    mensaje_cifrado TEXT NOT NULL,
    FOREIGN KEY (id_grupo) REFERENCES grupos(id),
    FOREIGN KEY (author) REFERENCES usuarios(id)
);

ALTER TABLE usuarios ADD COLUMN fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
