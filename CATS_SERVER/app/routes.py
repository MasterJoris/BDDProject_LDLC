from app import app
from app import sql_select, sql_insert, sql_delete, sql_update
from flask import request
from flask import jsonify


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    # requête pour récupérer les joueurs
    request_sql = f'''SELECT players_id, players_pseudo 
    FROM players'''

    # on exécute la requete
    data = sql_select(request_sql)

    # on print le résultat de la requête
    print(data)

    # on parcourt le résultat
    for player in data:
        # on récupère l'id du joueur
        player_id = player["players_id"]

        # requête pour récupérer les chats d'un joueur
        request_sql = f'''SELECT * FROM cats 
        JOIN rooms ON rooms.rooms_id = cats.rooms_id 
        WHERE rooms.players_id = {player_id}'''

        cats = sql_select(request_sql)
        print(f'''CHATS DU JOUEUR {player_id} : \n''')
        print(len(cats))

        # on ajoute le nombre de chats (le nombre d'objets dans la liste renvoyée par le serveur) au player actuel
        player["cats_count"] = len(cats)

    # on renvoie le résultat jsonifié
    return jsonify(data), 200


@app.route('/login', methods=['POST'])
def login():
    # on récupére le json envoyé par le client
    formulaire_login = (request.get_json())

    # on récupére 'e-mail et le mdp du joueur

    email = formulaire_login["email"]
    password = formulaire_login["password"]

    # on vérifie que l'email existe puis que le mot de passe est correct
    sql_request = f'''SELECT players_id, players_email, players_password FROM players WHERE players_email = "{email}"'''

    player_avec_cette_adresse_email = sql_select(sql_request)
    print(player_avec_cette_adresse_email)
    if len(player_avec_cette_adresse_email) == 0:
        return "Adresse email non reconnue ou inexsitante", 400
    elif password == player_avec_cette_adresse_email[0]["players_password"]:
        player_id = player_avec_cette_adresse_email[0]["players_id"]
        dico_player_id = {"id": player_id}
        return jsonify(dico_player_id), 200
    else:
        return "Mot de passe incorrect", 403


@app.route('/signup', methods=['POST'])
def sign_up():
    # on récupère le json envoyé par le client
    formulaire_inscription = (request.get_json())

    # on récupère l'email
    email = formulaire_inscription["email"]

    # on check si l'email existe, si oui on envoie une erreur
    sql_request = f'''SELECT * FROM players WHERE players_email = "{email}"'''

    players_avec_cette_email = sql_select(sql_request)

    if len(players_avec_cette_email) > 0:
        return "Email déjà existant", 503

    # on ajoute le joueur
    sql_request = f'''INSERT INTO players(players_pseudo, players_email, players_password)
    VALUES("{formulaire_inscription["pseudo"]}", 
    "{formulaire_inscription["email"]}", 
    "{formulaire_inscription["password"]}")'''

    players_id = sql_insert(sql_request)

    add_room(players_id, 0, 0, formulaire_inscription["seed"])

    return "OK", 200


@app.route('/users/<int:players_id>/rooms', methods=['GET', 'POST'])
def rooms_handling(players_id):
    if request.method == 'GET':
        return get_rooms_request(players_id)
    elif request.method == 'POST':
        return add_room_request(players_id, request.get_json())


def get_rooms_request(players_id):
    # Requête SQL pour obtenir les infos sur les rooms
    sql_request = f'''
    SELECT * FROM `rooms` 
    WHERE players_id = {players_id}'''

    # On stock le résultat de la requête SQL
    players_rooms = sql_select(sql_request)
    print(players_rooms)
    # On parcourt les salles pour y ajouter les chats présents dans chaque salle
    for rooms in players_rooms:
        room_id = rooms["rooms_id"]
        sql_request2 = f'''SELECT * FROM `cats`
        WHERE rooms_id = {room_id}'''
        cats = sql_select(sql_request2)
        rooms["cats"] = cats

    return jsonify(players_rooms), 200


def add_room_request(players_id, request_json):
    print(request_json)
    return add_room(players_id, request_json["position_x"], request_json["position_y"], request_json["seed"])


def add_room(players_id, pos_x, pos_y, seed):
    # Requête pour créer une nouvelle ligne dans la table rooms
    sql_request = f'''INSERT INTO `rooms` 
    (`rooms_id`, `rooms_position_x`, `rooms_position_y`, `rooms_seed`, `players_id`) 
    VALUES (NULL, '{pos_x}', '{pos_y}', '{seed}', '{players_id}');'''
    # On check s'il existe déjà une salle à l'endroit désiré
    sql_request2 = f'''SELECT rooms_position_x,rooms_position_y FROM `rooms` WHERE players_id = {players_id}'''
    rooms_positions = sql_select(sql_request2)
    for rooms in rooms_positions:
        if pos_x == rooms["rooms_position_x"] and pos_y == rooms["rooms_position_y"]:
            return "Il y a déjà une salle à cette position", 403
    # On insert la nouvelle salle dans la BDD et on renvoit l"id de la salle.
    new_room = sql_insert(sql_request)
    new_room_dico = {"id": new_room}
    return jsonify(new_room_dico), 200


@app.route('/users/<int:players_id>/rooms/<int:rooms_id>', methods=['DELETE'])
def delete_room(players_id, rooms_id):
    # Requête pour vérifier que le rooms_id est bien lié au players_id
    sql_request2 = f'''SELECT * FROM `rooms`
    WHERE `rooms_id` = {rooms_id} AND `players_id` = {players_id}'''
    room_player = sql_select(sql_request2)
    if len(room_player) == 0:
        return "Le joueur n'a pas cette salle", 403
    else:
        # Requête pour vérifier qu'il n y a pas de chat dans la salle
        sql_request3 = f'''SELECT * FROM `cats`
        WHERE `rooms_id` = {rooms_id} '''
        cats = sql_select(sql_request3)
        # Requête pour supprimer une ligne dans la table rooms
        sql_request = f'''DELETE FROM `rooms` WHERE `rooms`.`rooms_id` = {rooms_id}'''
        if len(cats) == 0:
            sql_delete(sql_request)
            return "OK", 200
        else:
            return "Suppression impossible, des chats sont présents dans la salle !", 403


@app.route('/cats', methods=['GET'])
def get_free_cats():
    return "Not implemented", 501


@app.route('/cats/<int:cats_id>', methods=['PATCH', 'DELETE'])
def update_cat(cats_id):
    return "Not implemented", 501
