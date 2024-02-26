import sqlite3
from datetime import datetime, timedelta
from operator import itemgetter

def validate(raccolta):
    if (datetime.strptime(raccolta['timestamp_chiusura'], '%Y-%m-%d %H:%M:%S.%f') - datetime.strptime(raccolta['timestamp_creazione'], '%Y-%m-%d %H:%M:%S.%f')).days > 14:
      return 'La data di scadenza non può essere più di 14 giorni dopo la data di creazione'

    if str(raccolta['timestamp_chiusura']) < datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'):
      print('----' + raccolta['timestamp_creazione'])
      print('----' + raccolta['timestamp_chiusura'])
      print('----' + datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
      return 'La data di scadenza non può essere nel passato'

    if raccolta['titolo'] == '':
      return 'Il campo titolo non può essere vuoto'

    if raccolta['descrizione'] == '':
      return 'Il campo descrizione non può essere vuoto'

    if raccolta['obiettivo'] == '':
      return 'Il campo obiettivo non può essere vuoto'

    if not raccolta['obiettivo'].isdigit() or raccolta['obiettivo'] == '0':
      return 'Il campo obiettivo deve essere un intero positivo'

    if raccolta['mindon'] == '':
       return 'Il campo donazione minima non può essere vuoto'

    if raccolta['maxdon'] == '':
      return 'Il campo donazione massima non può essere vuoto'

    if not raccolta['mindon'].isdigit() or raccolta['mindon'] == '0':
      return 'Il campo donazione minima deve essere un intero positivo'

    if not raccolta['maxdon'].isdigit() or raccolta['maxdon'] == '0':
      return 'Il campo donazione massima deve essere un intero positivo'

    if raccolta['mindon']>raccolta['maxdon']:
      return 'Il campo donazione minima deve essere minore o uguale al campo donazione massima'

    return 'ok'

def valid_card(carta):
    if len(carta) != 16:
        return False
    if not carta.isdigit():
        return False
    return True

#Restituisce una stringa del tipo 'xg yh' oppure 'x ore y minuti' oppure 'x minuti' a seconda del tempo passato
#Se manca meno di un minuto, restituisce 'meno di un minuto'
def time_ago(timestamp_donazione):
    timestamp_donazione = datetime.strptime(timestamp_donazione, '%Y-%m-%d %H:%M:%S.%f')
    timestamp_attuale = datetime.now()
    print(timestamp_attuale)
    minuti_rimanenti = (timestamp_attuale - timestamp_donazione).total_seconds() / 60
    if minuti_rimanenti > 1440:
        giorni = int(minuti_rimanenti / 1440)
        ore = int((minuti_rimanenti % 1440) / 60)
        return str(giorni) + 'g ' + str(ore) + 'h'
    elif minuti_rimanenti > 60:
        ore = int(minuti_rimanenti / 60)
        minuti = int(minuti_rimanenti % 60)
        return str(ore) + 'h ' + str(minuti) + ' minuti'
    elif minuti_rimanenti > 1:
        return str(int(minuti_rimanenti)) + ' minuti'
    else:
        return 'meno di un minuto'

#Restituisce una stringa del tipo 'xg yh' oppure 'x ore y minuti' oppure 'x minuti' a seconda del tempo rimanente
#Se manca meno di un minuto, restituisce 'meno di un minuto'
def time_left(timestamp_chiusura):
    timestamp_chiusura = datetime.strptime(timestamp_chiusura, '%Y-%m-%d %H:%M:%S.%f')
    timestamp_attuale = datetime.now()
    minuti_rimanenti = (timestamp_chiusura - timestamp_attuale).total_seconds() / 60
    if minuti_rimanenti > 1440:
        giorni = int(minuti_rimanenti / 1440)
        ore = int((minuti_rimanenti % 1440) / 60)
        return str(giorni) + 'g ' + str(ore) + 'h'
    elif minuti_rimanenti > 60:
        ore = int(minuti_rimanenti / 60)
        minuti = int(minuti_rimanenti % 60)
        return str(ore) + 'h ' + str(minuti) + ' minuti'
    elif minuti_rimanenti > 1:
        return str(int(minuti_rimanenti)) + ' minuti'
    else:
        return 'meno di un minuto'


def open(raccolta):
    if raccolta['timestamp_chiusura'] > str(datetime.now()):
        return True
    return False

def show_date(timestamp):
    timestamp = timestamp.split(' ')
    data = timestamp[0].split('-')
    timestamp = data[2] + '/' + data[1] + '/' + data[0]
    return timestamp


def show_date_time(timestamp):
    timestamp = timestamp.split(' ')
    data = timestamp[0].split('-')
    ora = timestamp[1].split(':')
    timestamp = data[2] + '/' + data[1] + '/' + data[0] + ' ' + ora[0] + ':' + ora[1]
    print(timestamp)
    return timestamp

#Ritorna una lista di dizionari con tutte le raccolte aperte di un utente
#se id_utente è None ritorna tutte le raccolte aperte
#aggiunge dei campi utili per la visualizzazione
def get_raccolte_aperte_by_user(id_utente):
    result = []
    query = 'SELECT * FROM raccolte WHERE timestamp_chiusura > ?'
    if id_utente:
        query += ' AND id_utente = ?'
    connection = sqlite3.connect('db/fundraisin.db')
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()
    if id_utente:
        cursor.execute(query, (datetime.now(), id_utente))
    else:
        cursor.execute(query, (datetime.now(),))

    rows = cursor.fetchall()

    for row in rows:
        raccolta_dict = dict(row)
        raccolta_dict['tempo_rimanente'] = time_left(raccolta_dict['timestamp_chiusura'])
        raccolta_dict['creata_il'] = show_date_time(raccolta_dict['timestamp_creazione'])
        raccolta_dict['percentuale_completamento'] = round(raccolta_dict['totale_raccolto']/raccolta_dict['obiettivo']*100)
        result.append(raccolta_dict)

    result = sorted(result, key=itemgetter('timestamp_chiusura'))


    cursor.close()
    connection.close()

    return result

#Ritorna una lista di dizionari con tutte le raccolte chiuse di un utente
#se id_utente è None ritorna tutte le raccolte aperte
#aggiunge dei campi utili per la visualizzazione
def get_raccolte_chiuse_by_user(id_utente):
    result = []
    query = 'SELECT * FROM raccolte WHERE timestamp_chiusura < ?'
    if id_utente:
        query += ' AND id_utente = ?'
    connection = sqlite3.connect('db/fundraisin.db')
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    if id_utente:
        cursor.execute(query, (datetime.now(), id_utente))
    else:
        cursor.execute(query, (datetime.now(),))

    rows = cursor.fetchall()

    for row in rows:
        raccolta_dict = dict(row)
        raccolta_dict['chiusa_il'] = show_date(raccolta_dict['timestamp_chiusura'])
        raccolta_dict['obiettivo_raggiunto'] = raccolta_dict['totale_raccolto'] >= raccolta_dict['obiettivo']
        result.append(raccolta_dict)

    result = sorted(result, key=itemgetter('obiettivo_raggiunto'), reverse=True)


    cursor.close()
    connection.close()

    return result



def get_raccolta_by_id(id_raccolta):
    query = 'SELECT * FROM raccolte WHERE id = ?'

    connection = sqlite3.connect('db/fundraisin.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(query, (id_raccolta,))

    result = cursor.fetchone()
    result = dict(result)
    result['aperta'] = open(result)
    result['tempo_rimanente'] = time_left(result['timestamp_chiusura'])
    result['creata_il'] = show_date_time(result['timestamp_creazione'])
    result['percentuale_completamento'] = round(result['totale_raccolto']/result['obiettivo']*100)
    result['chiusa_il'] = show_date_time(result['timestamp_chiusura'])
    result['obiettivo_raggiunto'] = result['totale_raccolto'] >= result['obiettivo']


    cursor.close()
    connection.close()

    return result



def get_donazioni(id_raccolta):
    result = []
    query = 'SELECT * FROM donazioni WHERE id_raccolta = ?'

    connection = sqlite3.connect('db/fundraisin.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(query, (id_raccolta,))

    rows = cursor.fetchall()

    for row in rows:
        donazione_dict = dict(row)
        donazione_dict['tempo_passato'] = time_ago(donazione_dict['timestamp'])
        result.append(donazione_dict)


    cursor.close()
    connection.close()

    return result



def donate(donazione):
    query = 'INSERT INTO donazioni (id_raccolta, importo, timestamp, indirizzo, nome, cognome, anonima, messaggio) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
    connection = sqlite3.connect('db/fundraisin.db')
    cursor = connection.cursor()

    cursor.execute(query, (donazione['id_raccolta'], donazione['importo'], donazione['timestamp'], donazione['indirizzo'], donazione['nome'], donazione['cognome'], donazione['anonima'], donazione['messaggio']) )
    connection.commit()

    cursor.close()
    connection.close()
    query = 'UPDATE raccolte SET totale_raccolto = totale_raccolto + ? WHERE id = ?'
    connection = sqlite3.connect('db/fundraisin.db')
    cursor = connection.cursor()
    cursor.execute(query, (donazione['importo'], donazione['id_raccolta']))
    connection.commit()
    cursor.close()
    connection.close()

    return True


def create_raccolta(raccolta):
    query = 'INSERT INTO raccolte (id_utente, titolo, descrizione, obiettivo, timestamp_creazione, timestamp_chiusura, totale_raccolto, mindon, maxdon, lampo, img) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    connection = sqlite3.connect('db/fundraisin.db')
    cursor = connection.cursor()

    cursor.execute(query, (raccolta['id_utente'], raccolta['titolo'], raccolta['descrizione'], raccolta['obiettivo'], raccolta['timestamp_creazione'], raccolta['timestamp_chiusura'], raccolta['totale_raccolto'], raccolta['mindon'], raccolta['maxdon'], raccolta['lampo'], raccolta['img']))

    last_id = cursor.lastrowid

    connection.commit()
    cursor.close()
    connection.close()

    # Restituisco l'ID della nuova raccolta per gestire l'immagine
    return last_id


def update_raccolta(raccolta):
    query = 'UPDATE raccolte SET titolo = ?, descrizione = ?, obiettivo = ?, timestamp_chiusura = ?, mindon = ?, maxdon = ?, lampo = ? WHERE id = ?'
    connection = sqlite3.connect('db/fundraisin.db')
    cursor = connection.cursor()

    cursor.execute(query, (raccolta['titolo'], raccolta['descrizione'], raccolta['obiettivo'], raccolta['timestamp_chiusura'], raccolta['mindon'], raccolta['maxdon'], raccolta['lampo'], raccolta['id']))
    connection.commit()
    cursor.close()
    connection.close()

    return True


def delete_donazioni_associate(id_raccolta):
    query = 'DELETE FROM donazioni WHERE id_raccolta = ?'
    connection = sqlite3.connect('db/fundraisin.db')
    cursor = connection.cursor()

    cursor.execute(query, (id_raccolta,))
    connection.commit()
    cursor.close()
    connection.close()

    return True

def delete_raccolta_db(id_raccolta):
    query = 'DELETE FROM raccolte WHERE id = ?'
    connection = sqlite3.connect('db/fundraisin.db')
    cursor = connection.cursor()

    cursor.execute(query, (id_raccolta,))
    connection.commit()
    cursor.close()
    connection.close()

    return True
