import sqlite3


domainPages = [
    ['wp', 'https://profil.wp.pl/login/login.html'],
    ['interia', 'https://poczta.interia.pl/logowanie/']
]

elements = [
    ['wp', 'acceptCookies', 'xpath', '//button[text()="AKCEPTUJĘ I PRZECHODZĘ DO SERWISU"]'],
    ['wp', 'loginInput', 'id', 'login'],
    ['wp', 'passwordInput', 'id', 'password'],
    ['wp', 'loginButton', 'class name', 'sc-bdvvtL.sc-gsDKAQ.styled__SubmitButton-sc-1bs2nwv-2.ekJwFE.hIxhWw.jyhBDA'],
    ['wp', 'message', 'class name', 'stream-item__info'],
    ['wp', 'messageDiscriminative', 'class name', 'stream-item__senders.text-truncate'],
    ['wp', 'messageSelect', 'class name', 'stream-item__select'],
    ['wp', 'deleteButton', 'class name', 'Button.Button--secondary'],
    ['wp', 'offertsTab', 'class name', 'Tab-text.commerce'],
    ['wp', 'mainTab', 'class name', 'Tab-text.tooltip-theme-arrows.tooltip-target'],
    
    ['interia', 'acceptCookies', 'class name', 'rodo-popup-agree'],
    ['interia', 'loginInput', 'id', 'email'],
    ['interia', 'passwordInput', 'id', 'password'],
    ['interia', 'loginButton', 'class name', 'btn'],
    ['interia', 'message', 'xpath', '//li[@ng-repeat="message in messages"]'],
    ['interia', 'messageDiscriminative', 'xpath', './/span[@ng-bind="::message.fromString"]'],
    ['interia', 'messageSelect', 'class name', 'checkbox-label'],
    ['interia', 'deleteButton', 'xpath', '//div[@ng-click="moveCheckedToTrash();"]'],
    ['interia', 'offertsTab', 'class name', 'icon.icon-offer'],
    ['interia', 'mainTab', 'xpath', '//a[@href="#/folder/1"]']
]



db = sqlite3.connect('./database.sqlite')

with db:
    db.execute('''
               CREATE TABLE IF NOT EXISTS domainAddress (
                   domain text NOT NULL,
                   pageAddress text NOT NULL,
                   PRIMARY KEY (domain, pageAddress));
               ''')
    
    db.execute('''
               CREATE TABLE IF NOT EXISTS domainElements (
                   domain text NOT NULL, 
                   elementName text NOT NULL,
                   by text NOT NULL,
                   value text NOT NULL,
                   PRIMARY KEY (domain, elementName));
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
    db.executemany('INSERT OR IGNORE INTO domainAddress(domain, pageAddress) VALUES (?,?);',  domainPages)
    
with db:
    db.executemany('INSERT OR IGNORE INTO domainElements VALUES (?,?,?,?);',  elements)
    
    
    
    
    
    
    