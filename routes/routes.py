from flask import Blueprint, jsonify, request
import psycopg2
from datetime import datetime


# Crear un Blueprint
routes = Blueprint('routes', __name__)

# Establece la conexión a la base de datos
try:
    connection = psycopg2.connect(
        host='localhost',
        database='proyecto1_cifrados',
        user='cifrados',
        password='ketchup123'
    )
except Exception as error:
    print(f"No se pudo conectar a la base de datos debido a: {error}")
    connection = None

@routes.route('/users', methods=['GET'])
def get_users():
    if connection:
        cursor = connection.cursor()
        # Ejecuta la consulta para obtener todos los usuarios
        cursor.execute("SELECT id, username FROM usuarios;")  # Cambiado para seleccionar solo las columnas necesarias
        # Fetchall devuelve una lista de tuplas, convertimos cada tupla a un dict
        users = [{'id': row[0], 'username': row[1]} for row in cursor.fetchall()]
        cursor.close()
        return jsonify(users)
    else:
        return jsonify({'error': 'Error al conectar con la base de datos'}), 500


@routes.route('/users', methods=['POST'])
def create_user():
    if not connection:
        return jsonify({'error': 'Error al conectar con la base de datos'}), 500

    # Obtener datos del usuario desde el cuerpo de la solicitud
    user_data = request.get_json()
    user = user_data.get('username')
    public_key = user_data.get('public_key')
    fecha_creacion = datetime.now()

    # Validar los datos recibidos
    if not user or not public_key:
        return jsonify({'error': 'Falta información del usuario'}), 400

    try:
        cursor = connection.cursor()
        query_string = "INSERT INTO usuarios (username, public_key, fecha_creacion) VALUES (%s, %s, %s);"
        cursor.execute(query_string, (user, public_key, fecha_creacion))
        connection.commit()  # Realizar la transacción
        cursor.close()
        return jsonify({'message': 'Usuario creado exitosamente'}), 201
    except (Exception, psycopg2.DatabaseError) as error:
        connection.rollback()  # Revertir la transacción en caso de error
        return jsonify({'error': str(error)}), 500

@routes.route('/users/<string:username>/key', methods=['GET'])
def get_user_public_key(username):
    if connection:
        cursor = connection.cursor()
        try:
            # Consultar la llave pública del usuario basándose en el username
            cursor.execute("SELECT public_key FROM usuarios WHERE username = %s;", (username,))
            result = cursor.fetchall()
            if result:
                return jsonify({'username': username, 'public_key': result[0][0]})
            else:
                return jsonify({'error': 'Usuario no encontrado'}), 404
        except psycopg2.Error as e:
            return jsonify({'error': f"Error al obtener la llave pública: {e}"}), 500
        finally:
            cursor.close()
    else:
        return jsonify({'error': 'Error al conectar con la base de datos'}), 500

@routes.route('/groups', methods=['GET'])
def get_groups():
    if connection:
        cursor = connection.cursor()
        # Recuperar la información de los grupos y realizar un JOIN con usuarios_grupos y usuarios
        cursor.execute("""
            SELECT g.id, g.nombre, g.clave_simetrica, u.username
            FROM grupos g
            LEFT JOIN usuarios_grupos ug ON g.id = ug.id_grupo
            LEFT JOIN usuarios u ON ug.id_usuario = u.id;
        """)
        rows = cursor.fetchall()
        
        groups = {}
        # Organizar la información de los grupos y usuarios
        for row in rows:
            group_id, nombre, clave_simetrica, username = row
            if group_id not in groups:
                groups[group_id] = {
                    'id': group_id,
                    'nombre': nombre,
                    'clave_simetrica': clave_simetrica,
                    'usuarios': []
                }
            # Agregar el nombre de usuario a la lista de usuarios si existe (puede ser None si el grupo no tiene usuarios)
            if username:
                groups[group_id]['usuarios'].append(username)
        
        # Convertir el diccionario de grupos a una lista para la salida JSON
        groups_list = list(groups.values())

        cursor.close()
        return jsonify(groups_list)
    else:
        return jsonify({'error': 'Error al conectar con la base de datos'}), 500

@routes.route('/messages/<string:user_destino>', methods=['POST'])
def create_message(user_destino):
    if not connection:
        return jsonify({'error': 'Error al conectar con la base de datos'}), 500

    # Obtener datos del mensaje desde el cuerpo de la solicitud
    message_data = request.get_json()
    message_text = message_data.get('message')
    sender_username = message_data.get('username')

    # Validar los datos recibidos
    if not message_text or not sender_username: # Asegurarse de tener todos los campos necesarios
        return jsonify({'error': 'Falta información del mensaje'}), 400

    try:
        cursor = connection.cursor()

        # Obtener el ID del remitente
        query_sender_id = "SELECT id FROM usuarios WHERE username = %s"
        cursor.execute(query_sender_id, (sender_username,))
        sender_id = cursor.fetchone()[0]

        # Obtener el ID del destinatario
        query_destino_id = "SELECT id FROM usuarios WHERE username = %s"
        cursor.execute(query_destino_id, (user_destino,))
        destino_id = cursor.fetchone()[0]

        # Insertar el mensaje en la base de datos
        query_string = "INSERT INTO mensajes (mensaje_cifrado, id_username_destino, id_username_origen) VALUES (%s, %s, %s);"
        cursor.execute(query_string, (message_text, destino_id, sender_id))
        connection.commit()  # Realizar la transacción
        cursor.close()
        return jsonify({'message': 'Mensaje enviado exitosamente'}), 201
    except (Exception, psycopg2.DatabaseError) as error:
        connection.rollback()  # Revertir la transacción en caso de error
        return jsonify({'error': str(error)}), 500


@routes.route('/messages/groups/<string:group_destino>', methods=['POST'])
def create_group_message(group_destino):
    if not connection:
        return jsonify({'error': 'Error al conectar con la base de datos'}), 500

    # Obtener datos del mensaje desde el cuerpo de la solicitud
    message_data = request.get_json()
    message_text = message_data.get('message')
    sender_username = message_data.get('username')

    # Validar los datos recibidos
    if not message_text or not sender_username: # Asegurarse de tener todos los campos necesarios
        return jsonify({'error': 'Falta información del mensaje'}), 400

    try:
        cursor = connection.cursor()

        # Obtener el ID del remitente
        query_sender_id = "SELECT id FROM usuarios WHERE username = %s"
        cursor.execute(query_sender_id, (sender_username,))
        sender_id = cursor.fetchone()[0]

        # Obtener el ID del destinatario
        query_destino_id = "SELECT id FROM grupos WHERE nombre = %s"
        cursor.execute(query_destino_id, (group_destino,))
        destino_id = cursor.fetchone()[0]

        # Insertar el mensaje en la base de datos
        query_string = "INSERT INTO mensajes_grupos (id_grupo, author, mensaje_cifrado) VALUES (%s, %s, %s);"
        cursor.execute(query_string, (destino_id, sender_id, message_text))
        connection.commit()  # Realizar la transacción
        cursor.close()
        return jsonify({'message': 'Mensaje enviado exitosamente'}), 201
    except (Exception, psycopg2.DatabaseError) as error:
        connection.rollback()  # Revertir la transacción en caso de error
        return jsonify({'error': str(error)}), 500

@routes.route('/groups', methods=['POST'])
def create_group():
    if not connection:
        return jsonify({'error': 'Error al conectar con la base de datos'}), 500

    # Obtener datos del grupo desde el cuerpo de la solicitud
    group_data = request.get_json()
    group_name = group_data.get('nombre')
    symmetric_key = group_data.get('clave_simetrica')
    group_password = group_data.get('contrasena')
    users = group_data.get('usuarios')

    # Validar los datos recibidos
    if not group_name or not symmetric_key or not group_password or not users:
        return jsonify({'error': 'Falta información del grupo'}), 400

    try:
        cursor = connection.cursor()
        
        # Insertar el grupo en la tabla de grupos
        query_group_insert = "INSERT INTO grupos (nombre, contrasena, clave_simetrica) VALUES (%s, %s, %s) RETURNING id;"
        cursor.execute(query_group_insert, (group_name, group_password, symmetric_key))
        group_id = cursor.fetchone()[0]  # Obtener el ID del grupo recién creado

        # Insertar cada usuario en la tabla de usuarios_grupos
        for user in users:
            # Obtener el ID del usuario
            query_user_id = "SELECT id FROM usuarios WHERE username = %s;"
            cursor.execute(query_user_id, (user,))
            user_id = cursor.fetchone()[0]

            # Insertar el usuario en la tabla de usuarios_grupos
            query_user_group_insert = "INSERT INTO usuarios_grupos (id_usuario, id_grupo) VALUES (%s, %s);"
            cursor.execute(query_user_group_insert, (user_id, group_id))

        connection.commit()  # Realizar la transacción
        cursor.close()
        return jsonify({'message': 'Grupo creado exitosamente'}), 201
    except (Exception, psycopg2.DatabaseError) as error:
        connection.rollback()  # Revertir la transacción en caso de error
        return jsonify({'error': str(error)}), 500


@routes.route('/users/<string:username>', methods=['PUT'])
def update_user(username):
    if not connection:
        return jsonify({'error': 'Error al conectar con la base de datos'}), 500

    # Obtener datos del usuario desde el cuerpo de la solicitud
    user_data = request.get_json()
    new_public_key = user_data.get('public_key')

    # Validar los datos recibidos
    if not username or not new_public_key:
        return jsonify({'error': 'Falta información del usuario'}), 400

    try:
        cursor = connection.cursor()

        # Actualizar la clave pública del usuario
        query_update_user = "UPDATE usuarios SET public_key = %s WHERE username = %s;"
        cursor.execute(query_update_user, (new_public_key, username))
        connection.commit()  # Realizar la transacción
        cursor.close()
        return jsonify({'message': 'Usuario actualizado exitosamente'}), 200
    except (Exception, psycopg2.DatabaseError) as error:
        connection.rollback()  # Revertir la transacción en caso de error
        return jsonify({'error': str(error)}), 500
    
from flask import jsonify

@routes.route('/messages/users/<string:username_origen>/<string:username_destino>', methods=['GET'])
def get_messages_between_users(username_origen, username_destino):
    if not connection:
        return jsonify({'error': 'Error al conectar con la base de datos'}), 500

    try:
        cursor = connection.cursor()

        # Obtener el ID del usuario de origen
        cursor.execute("SELECT id FROM usuarios WHERE username = %s;", (username_origen,))
        user_origen_id = cursor.fetchone()
        if user_origen_id is None:
            return jsonify({'error': f'Usuario de origen {username_origen} no encontrado'}), 404

        # Obtener el ID del usuario de destino
        cursor.execute("SELECT id FROM usuarios WHERE username = %s;", (username_destino,))
        user_destino_id = cursor.fetchone()
        if user_destino_id is None:
            return jsonify({'error': f'Usuario de destino {username_destino} no encontrado'}), 404

        # Obtener mensajes entre los usuarios
        cursor.execute("""
            SELECT m.id, m.mensaje_cifrado, uo.username AS username_origen, ud.username AS username_destino 
            FROM mensajes m
            JOIN usuarios uo ON m.id_username_origen = uo.id
            JOIN usuarios ud ON m.id_username_destino = ud.id
            WHERE (m.id_username_origen = %s AND m.id_username_destino = %s)
            OR (m.id_username_origen = %s AND m.id_username_destino = %s)
            ORDER BY m.id;
            """, (user_origen_id[0], user_destino_id[0], user_destino_id[0], user_origen_id[0]))

        messages = cursor.fetchall()
        results = [{
            'id': msg[0],
            'message': msg[1],
            'username_origen': msg[2],
            'username_destino': msg[3]
        } for msg in messages]

        cursor.close()
        return jsonify(results)
    except (Exception, psycopg2.DatabaseError) as error:
        return jsonify({'error': str(error)}), 500


@routes.route('/users/key/<string:username>', methods=['DELETE'])
def delete_user_public_key(username):
    if not connection:
        return jsonify({'error': 'Error al conectar con la base de datos'}), 500

    try:
        cursor = connection.cursor()

        # Verificar si el usuario existe
        query_check_user = "SELECT id FROM usuarios WHERE username = %s;"
        cursor.execute(query_check_user, (username,))
        user_id = cursor.fetchone()

        if user_id:
            # Eliminar la clave pública del usuario
            query_delete_public_key = "UPDATE usuarios SET public_key = NULL WHERE username = %s;"
            cursor.execute(query_delete_public_key, (username,))
            connection.commit()  # Realizar la transacción
            cursor.close()
            return jsonify({'message': f'Clave pública del usuario {username} eliminada exitosamente'}), 200
        else:
            return jsonify({'error': 'Usuario no encontrado'}), 404

    except (Exception, psycopg2.DatabaseError) as error:
        connection.rollback()  # Revertir la transacción en caso de error
        return jsonify({'error': str(error)}), 500


@routes.route('/groups/<string:group>', methods=['DELETE'])
def delete_group(group):
    if not connection:
        return jsonify({'error': 'Error al conectar con la base de datos'}), 500

    try:
        cursor = connection.cursor()

        # Verificar si el grupo existe
        query_check_group = "SELECT id FROM grupos WHERE nombre = %s;"
        cursor.execute(query_check_group, (group,))
        group_id = cursor.fetchone()

        if group_id:
            # Eliminar todos los registros relacionados en la tabla usuarios_grupos
            query_delete_user_group = "DELETE FROM usuarios_grupos WHERE id_grupo = %s;"
            cursor.execute(query_delete_user_group, (group_id,))
            
            # Eliminar el grupo
            query_delete_group = "DELETE FROM grupos WHERE nombre = %s;"
            cursor.execute(query_delete_group, (group,))
            
            connection.commit()  # Realizar la transacción
            cursor.close()
            return jsonify({'message': f'Grupo {group} y sus registros relacionados eliminados exitosamente'}), 200
        else:
            return jsonify({'error': 'Grupo no encontrado'}), 404

    except (Exception, psycopg2.DatabaseError) as error:
        connection.rollback()  # Revertir la transacción en caso de error
        return jsonify({'error': str(error)}), 500


@routes.route('/users/<string:username>', methods=['DELETE'])
def delete_user(username):
    if not connection:
        return jsonify({'error': 'Error al conectar con la base de datos'}), 500

    try:
        cursor = connection.cursor()

        # Obtener el ID del usuario
        query_get_user_id = "SELECT id FROM usuarios WHERE username = %s;"
        cursor.execute(query_get_user_id, (username,))
        user_id = cursor.fetchone()

        if user_id:
            user_id = user_id[0]  # Obtener el ID del usuario

            # Eliminar registros relacionados en la tabla usuarios_grupos
            query_delete_user_groups = "DELETE FROM usuarios_grupos WHERE id_usuario = %s;"
            cursor.execute(query_delete_user_groups, (user_id,))

            # Eliminar registros relacionados en la tabla mensajes
            query_delete_user_messages = "DELETE FROM mensajes WHERE id_username_destino = %s OR id_username_origen = %s;"
            cursor.execute(query_delete_user_messages, (user_id, user_id))

            # Eliminar registros relacionados en la tabla mensajes_grupos
            query_delete_user_group_messages = "DELETE FROM mensajes_grupos WHERE author = %s;"
            cursor.execute(query_delete_user_group_messages, (user_id,))

            # Eliminar el usuario
            query_delete_user = "DELETE FROM usuarios WHERE username = %s;"
            cursor.execute(query_delete_user, (username,))
            
            connection.commit()  # Realizar la transacción
            cursor.close()
            return jsonify({'message': f'Usuario {username} y sus registros relacionados eliminados exitosamente'}), 200
        else:
            return jsonify({'error': 'Usuario no encontrado'}), 404

    except (Exception, psycopg2.DatabaseError) as error:
        connection.rollback()  # Revertir la transacción en caso de error
        return jsonify({'error': str(error)}), 500


@routes.route('/messages/groups/<int:id_group>', methods=['GET'])
def get_group_messages(id_group):
    if not connection:
        return jsonify({'error': 'Error al conectar con la base de datos'}), 500

    try:
        cursor = connection.cursor()

        # Asegúrate de que las referencias a la tabla y columnas son correctas
        cursor.execute("""
            SELECT mg.id_grupo, u.username, mg.mensaje_cifrado
            FROM mensajes_grupos mg
            JOIN usuarios u ON mg.author = u.id
            WHERE mg.id_grupo = %s;
        """, (id_group,))

        messages = cursor.fetchall()
        results = [{
            'id_group': msg[0],
            'author': msg[1],
            'mensaje': msg[2]
        } for msg in messages]  # Asegúrate de que esto coincida con la selección de tu consulta

        cursor.close()
        return jsonify(results)
    except (Exception, psycopg2.DatabaseError) as error:
        return jsonify({'error': str(error)}), 500

