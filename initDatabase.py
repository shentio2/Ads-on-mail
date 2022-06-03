import sqlite3


domainPage = ['wp', 'https://profil.wp.pl/login/login.html']

elements = [
    ['wp', 'acceptCookies', 'xpath', '//button[text()="AKCEPTUJĘ I PRZECHODZĘ DO SERWISU"]'],
    ['wp', 'loginInput', 'id', 'login'],
    ['wp', 'passwordInput', 'id', 'password'],
    ['wp', 'loginButton', 'class name', 'sc-bdvvtL.sc-gsDKAQ.styled__SubmitButton-sc-1bs2nwv-2.ekJwFE.hIxhWw.jyhBDA'],
    ['wp', 'message', 'class name', 'stream-item__info'],
    ['wp', 'messageTopic', 'class name', 'stream-item__senders.text-truncate'],
    ['wp', 'messageSelect', 'class name', 'stream-item__select'],
    ['wp', 'deleteButton', 'class name', 'Button.Button--secondary'],
    ['wp', 'offertsTab', 'class name', 'Tab-text.commerce'],
    ['wp', 'mainTab', 'class name', 'Tab-text.tooltip-theme-arrows.tooltip-target']
]



db = sqlite3.connect('./database.sqlite')

with db:
    db.execute('''
               CREATE TABLE IF NOT EXISTS domainAddress (
                   domain text NOT NULL,
                   pageAddress text NOT NULL,
                   PRIMARY KEY (domain, pageAddress)
               )
               ''')
    
    db.execute('''
               CREATE TABLE IF NOT EXISTS domainElements (
                   domain text NOT NULL, 
                   elementName text NOT NULL,
                   by text NOT NULL,
                   value text NOT NULL,
                   PRIMARY KEY (domain, elementName)
               )
               ''')
    
    db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    userName text NOT NULL,
                    password text NOT NULL,
                    domain text NOT NULL,
                    timeInterval INTEGER NOT NULL);
                ''')

    db.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    userName text NOT NULL,
                    loop_id INTEGER NOT NULL,
                    error INTEGER NOT NULL,
                    info text NOT NULL,
                    deleted INTEGER,
                    date text NOT NULL);
                ''')
    
    
  
with db:
    db.execute('INSERT INTO domainAddress(domain, pageAddress) VALUES (?,?);',  domainPage)
    
with db:
    db.executemany('INSERT INTO domainElements VALUES (?,?,?,?);',  elements)
    
    
    
    
    
    
    