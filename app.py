import os

from queue import Empty
from pyparsing import empty
import xml.etree.ElementTree as ET #knihovna pro XML

from sqlalchemy import create_engine #knihovna pro jazyk SQL
import hashlib #knihovna kvůli S256
import pyodbc #knihovna pro komunikaci se MS SQL

from requests_oauthlib import OAuth2Session #knihovna pro autoraizaci vúči serveru

from flask import Flask, request, redirect, session, url_for, abort,  make_response  #knihovna REST API
from flask.json import jsonify

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

dianiApi = Flask(__name__)

def connection():
    #s = '::1,1433' #server a port (MS SQL má více portů defaultní je 1433) nebo loclahost --> adres serveru je spousta
    s = 'host.docker.internal,1433' # Dokcer adresa
    d = 'test' #název DB
    u = 'test' #USER
    p = 'test' #Password
    #cstr = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+s+';DATABASE='+d+';trusted_connection=yes'   #String pro Windows (ověřuji se windows učtem)
    cstr = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+s+';DATABASE='+d+';UID='+u+';PWD='+ p # string pro jinýho usera např. SQL connetction
    conn = pyodbc.connect(cstr)
    return conn



# Infromace nutné k ověření vůči serveru
client_id_address = "B2EC84D0-2FE4-4AF9-99E5-670ABC926AF6"
response_type_address= 'code'
callback_address = 'http://localhost:5000/'
scope_address = 'openid+profile'
state_address = 'xcoiv98y2kd22vusuye3kch' # nebylo potřeba, generuje se samo díky knihovně
rand_string = 'xcoiv98y2kd22vusuye3kchxcoiv98y2kd22vusuye3kchxcoiv98y2kd22vusuye3kchxcoiv98y2kd22vusuye3kchxcoiv98y2kd22vusuye3kch'
code_challenge = hashlib.sha256(rand_string.encode('utf-8')).hexdigest() # ověřovací řetězec, který se kontroluje po odpovědi, zda zůstal stejný -> HASH
code_challenge_method = 'S256'
authorization_base_url = 'https://identity-dev.albertov.cz/connect/authorize'
token_url = 'https://identity-dev.albertov.cz/connect/token'

dianiApi.secret_key = "CodeSpecialist.com"
client_secret = "from flask import Flask"

indentityServer = OAuth2Session(client_id_address) #založení instance IDENTITY SERVERU pro ověřování
#authorization_url, state = indentityServer.authorization_url(authorization_base_url+
#                                                             '&redirect_uri='+callback_address+
#                                                            '&scope='+scope_address+
#                                                            '&code_challenge='+code_challenge+
#                                                            '&code_challenge_method='+code_challenge_method)
authorization_url, state = indentityServer.authorization_url(authorization_base_url) #základní autorizační url serveru

@dianiApi.route("/login") #ověřování
def login():
    session['oauth_state'] = state #uložení stavu přihlášení
    return redirect(authorization_url+   #adresa se všemi potřebnými údaji pro identity server
                    '&redirect_uri='+callback_address+
                    '&scope='+scope_address+
                    '&code_challenge='+code_challenge+
                    '&code_challenge_method='+code_challenge_method)



@dianiApi.route("/") #main -> pokud je přihlášený uživatel napíše se session is active jinak nothing to see here
def main():
    print(session)
    if bool(session):
        return f"Session is active"
    else:
        return f"nothing to see here"


@dianiApi.route("/callback") #/callback
def callback():
    return f"nothing to see here"

@dianiApi.route("/logout") #adresa, která mě odhlásí
def logout():
    session.clear()
    return redirect("/")


def login_is_required(function): # funkce, která ověřuje, zda jsem přihlášen
    def wrapper(*args, **kwargs):
        if bool(session):
            return function()
        else:
            return abort(401)  # Authorization required Vrací hlášku, která říká že nemám práva
    wrapper.__name__ = function.__name__
    return wrapper

#127.0.0.1:5000/select
#@login_is_required
@dianiApi.route("/select") #select dotaz do databáze 
def select():
    pacients = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dbo.uzivatel")
    for row in cursor.fetchall():
        pacients.append({"id": row[0], "name": row[1]})
    conn.close()
    return f"{pacients}"

#127.0.0.1:5000/insert
@login_is_required   # nejdříve se provede autorizace, zda jsem přihlášen a mám přístup k funkci pod tímto.
@dianiApi.route("/insert") # funkce vkládá natvrdo ID a jméno do DB
def insert():
        id = 5
        name = "Karel"
        conn = connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO dbo.uzivatel (id, name) VALUES (?, ?)", id, name)
        conn.commit()
        conn.close()
        return redirect('/select') # přesměrování na výběr, abych hned viděl změnu

# 127.0.0.1:5000/update/3/Klementajn
@login_is_required# nejdříve se provede autorizace, zda jsem přihlášen a mám přístup k funkci pod tímto.
@dianiApi.route('/update/<int:id>/<string:name>',methods = ['GET']) # funkce update, která funguje tak, že napíšu do adresy ID řádku co hcic změnit, a poté na co
def update(id, name):
    conn = connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE dbo.uzivatel SET name = ? WHERE id = ?", name, id)
    conn.commit()
    conn.close()
    return redirect('/select')



@dianiApi.route('/fhir') #dle zaslaného odkazu vypisuji FHIR ve formátu XML
def fhir():
    with open('fhir.xml', 'r') as f:
        bar = f.read()                                            
    response = make_response(bar)                                           
    response.headers['Content-Type'] = 'text/xml; charset=utf-8'            
    return response

@dianiApi.route('/fhirVlastní') # lze i vytvářet vlastní XML řetězce
def user_xml():
    #bar = '<body>foo</body>'  
    with open('fhir2.xml', 'r') as f:
        bar = f.read()                                                                   
    response = make_response(bar)                                           
    response.headers['Content-Type'] = 'text/xml; charset=utf-8'            
    return response
    


if __name__ == "__main__":   
    dianiApi.run(debug=True,host='0.0.0.0', port=5000) #řádek, který spouští server na adrese 0.0.0.0 -> je viditelný odkudkoli


    