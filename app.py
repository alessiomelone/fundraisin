# import module
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

import raccolte_dao, utenti_dao
from models import User


# Crea l'applicazione
app = Flask(__name__)
app.config['SECRET_KEY'] = 'RaisinIsGood' # Chiave segreta per la sessione, da cambiare in produzione

login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/')
def home():
    raccolte_db = raccolte_dao.get_raccolte_aperte_by_user(None)
    return render_template('home.html', raccolte = raccolte_db)


@app.route('/closed')
def raccolte_chiuse():
    raccolte_db = raccolte_dao.get_raccolte_chiuse_by_user(None)
    return render_template('raccolte_chiuse.html', raccolte = raccolte_db)


@app.route('/raccolte/<int:id>')
def raccolta(id):
    raccolta_db = raccolte_dao.get_raccolta_by_id(id)
    donazioni_db = raccolte_dao.get_donazioni(id)
    nome_creatore = utenti_dao.get_user_by_id(raccolta_db['id_utente'])['nome']
    return render_template('raccolta.html', raccolta = raccolta_db, donazioni = donazioni_db, nome_creatore = nome_creatore)


@app.route('/donate/<int:id_raccolta>', methods=['POST'])
def donate(id_raccolta):
  raccolta = raccolte_dao.get_raccolta_by_id(id_raccolta)
  if raccolta['timestamp_chiusura'] < datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'):
      flash('Raccolta chiusa', 'danger')
      return redirect(url_for('raccolta', id=id_raccolta))
  donazione = request.form.to_dict()

  if donazione['importo'] == '':
    flash('Il campo importo non può essere vuoto', 'danger')
    return redirect(url_for('raccolta', id=id_raccolta))

  if not donazione['importo'].isdigit() or donazione['importo'] == '0':
    flash('Il campo importo deve essere un intero positivo', 'danger')
    return redirect(url_for('raccolta', id=id_raccolta))

  if int(donazione['importo']) < raccolta['mindon'] or int(donazione['importo']) > raccolta['maxdon']:
    stri = 'Il campo importo deve essere compreso tra donazine minima e massima'
    flash(stri, 'danger')
    return redirect(url_for('raccolta', id=id_raccolta))

  donazione['timestamp'] = str(datetime.now())
  donazione['id_raccolta'] = id_raccolta
  donazione['anonima'] = '1' if 'anonima' in donazione else '0'
  donazione['carta'] = donazione['carta'].replace(' ', '')

  if not raccolte_dao.valid_card(donazione['carta']):
      flash('Carta non valida', 'danger')
      return redirect(url_for('raccolta', id=id_raccolta))

  success = raccolte_dao.donate(donazione)

  if success:
      flash('Donazione completata con successo!', 'success')
  else:
      flash('Errore durante la donazione', 'danger')
  return redirect(url_for('raccolta', id=id_raccolta))

@login_required
@app.route('/create_page')
def create_page():
    return render_template('create_edit.html', edit=False)

@login_required
@app.route('/create', methods=['POST'])
def crea_raccolta():
    raccolta = request.form.to_dict()
    raccolta['id_utente'] = current_user.id
    raccolta['totale_raccolto'] = '0'
    raccolta['timestamp_creazione'] = datetime.now()
    if raccolta['lampo']=='1':
      raccolta['timestamp_chiusura'] = str(raccolta['timestamp_creazione'] + timedelta(minutes=5))
    else:
      # se è inserita la data di scadenza, la converto in datetime, altrimenti la scadenza è 14 giorni dopo la creazione
      if raccolta['scadenza'] == '':
        raccolta['timestamp_chiusura'] = str(raccolta['timestamp_creazione'] + timedelta(days=14))
      else:
        raccolta['timestamp_chiusura'] = raccolta['scadenza'] + ' ' + raccolta['ora_scadenza'] + ':00.000000'

    raccolta['timestamp_creazione']=str(raccolta['timestamp_creazione'])

    messagge = raccolte_dao.validate(raccolta)

    if messagge!='ok':
      flash(messagge, 'danger')
      return redirect(url_for('create_page'))

    if 'img' in request.files and request.files['img'].filename != '':
      raccolta['img'] = '1'
    else:
      raccolta['img'] = '0'

    #restituisce l'id della raccolta appena creata, altrimenti False
    success = raccolte_dao.create_raccolta(raccolta)

    if success:
        if raccolta['img'] == '1':
            file = request.files['img']
            file.save('static/' + str(success) + '.jpg')
        flash('Raccolta creata con successo!', 'success')
        return redirect(url_for('profile', id=current_user.id))
    else:
        flash('Errore durante la creazione della raccolta', 'danger')
    return redirect(url_for('profile', id=current_user.id))


@login_required
@app.route('/edit/<int:id_raccolta>')
def edit_page(id_raccolta):
    raccolta = raccolte_dao.get_raccolta_by_id(id_raccolta)
    if raccolta['id_utente'] != current_user.id:
        flash('Non puoi modificare una raccolta di un altro utente', 'danger')
        return redirect(url_for('home'))
    data_scadenza = datetime.strptime(raccolta['timestamp_chiusura'], '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d')
    ora_scadenza= datetime.strptime(raccolta['timestamp_chiusura'], '%Y-%m-%d %H:%M:%S.%f').strftime('%H:%M')

    return render_template('create_edit.html', edit=True, raccolta=raccolta, data_scadenza=data_scadenza, ora_scadenza=ora_scadenza)

@login_required
@app.route('/edit_raccolta/<int:id_raccolta>', methods=['POST'])
def edit_raccolta(id_raccolta):

    raccolta_old = raccolte_dao.get_raccolta_by_id(id_raccolta)
    if raccolta_old['id_utente'] != current_user.id:
        flash('Non puoi modificare una raccolta di un altro utente', 'danger')
        return redirect(url_for('home'))

    raccolta = request.form.to_dict()
    raccolta['id'] = id_raccolta
    raccolta['timestamp_creazione'] = datetime.strptime(raccolta_old['timestamp_creazione'], '%Y-%m-%d %H:%M:%S.%f')

    if raccolta['lampo']=='1':
      raccolta['timestamp_chiusura'] = str(raccolta['timestamp_creazione'] + timedelta(minutes=5))
    else:
      # se è inserita la data di scadenza, la converto in datetime, altrimenti la scadenza è 14 giorni dopo la creazione
      if raccolta['scadenza'] == '':
        raccolta['timestamp_chiusura'] = str(raccolta['timestamp_creazione'] + timedelta(days=14))
      else:
        raccolta['timestamp_chiusura'] = raccolta['scadenza'] + ' ' + raccolta['ora_scadenza'] + ':00.000000'
    raccolta['timestamp_creazione']=str(raccolta['timestamp_creazione'])

    messagge = raccolte_dao.validate(raccolta)

    if messagge!='ok':
      flash(messagge, 'danger')
      return redirect(url_for('edit_page', id_raccolta=raccolta['id']))

    success = raccolte_dao.update_raccolta(raccolta)

    if success:
        flash('Raccolta modificata con successo!', 'success')
        return redirect(url_for('profile', id=current_user.id))
    else:
        flash('Errore durante la modifica della raccolta', 'danger')
    return redirect(url_for('profile', id=current_user.id))



@login_required
@app.route('/delete_raccolta/<int:id_raccolta>', methods=['POST'])
def delete_raccolta(id_raccolta):
    raccolte_dao.delete_donazioni_associate(id_raccolta)
    raccolte_dao.delete_raccolta_db(id_raccolta)
    flash('Raccolta e donazioni associate eliminate con successo.', 'success')
    return redirect(url_for('profile', id=current_user.id))





@login_required
@app.route('/profile/<int:id>')
def profile(id):
    if current_user.id != id:
        flash('Non puoi accedere al profilo di un altro utente', 'danger')
        return redirect(url_for('home'))
    user = utenti_dao.get_user_by_id(id)
    ra = raccolte_dao.get_raccolte_aperte_by_user(id)
    rc = raccolte_dao.get_raccolte_chiuse_by_user(id)
    credito_utente=0
    for raccolta in rc:
       if raccolta['totale_raccolto'] >= raccolta['obiettivo']:
          credito_utente += raccolta['totale_raccolto']
    return render_template('profile.html', user=user, raccolte_aperte=ra, raccolte_chiuse=rc, credito_utente=credito_utente)


@app.route('/signup_page')
def signup_page():
    return render_template('signup.html')


@app.route('/signup', methods=['POST'])
def signup():

  new_user_from_form = request.form.to_dict()

  if utenti_dao.get_user_by_email(new_user_from_form['email']):
    flash('Email già utilizzata, accedi', 'danger')
    return redirect(url_for('signup_page'))

  if new_user_from_form['nome'] == '':
    flash('Il campo nome non può essere vuoto', 'danger')
    return redirect(url_for('signup_page'))

  if new_user_from_form['cognome'] == '':
    flash('Il campo cognome non può essere vuoto', 'danger')
    return redirect(url_for('signup_page'))

  if new_user_from_form['email'] == '':
    flash('Il campo email non può essere vuoto', 'danger')
    return redirect(url_for('signup_page'))

  if not utenti_dao.check_secure(new_user_from_form['password']):
    flash('La tua password deve contenere almeno 8 caratteri, un numero, una lettera maiuscola e una minuscola.', 'danger')
    return redirect(url_for('signup_page'))

  new_user_from_form['password'] = generate_password_hash(new_user_from_form['password'])

  success = utenti_dao.creare_utente(new_user_from_form)

  if success:
    flash('Registrazione completata con successo!', 'success')
    return redirect(url_for('home'))

  flash('Errore durante la creazione dell\'utente', 'danger')
  return redirect(url_for('signup_page'))



@app.route('/login', methods=['POST'])
def login():

  utente_form = request.form.to_dict()

  utente_db = utenti_dao.get_user_by_email(utente_form['email'])

  if not utente_db or not check_password_hash(utente_db['password'], utente_form['password']):
    flash("Credenziali non valide", 'danger')
    return redirect(url_for('signup_page'))
  else:
    new = User(id=utente_db['id'], nome=utente_db['nome'], cognome=utente_db['cognome'], email=utente_db['email'], password=utente_db['password'] )
    login_user(new, True)

    return redirect(url_for('home'))


@login_manager.user_loader
def load_user(user_id):
    db_user = utenti_dao.get_user_by_id(user_id)
    if db_user is None:
        return None
    user = User(id=db_user['id'], nome=db_user['nome'], cognome=db_user['cognome'], email=db_user['email'], password=db_user['password'])
    return user


@login_required
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))
