from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from pwinput import pwinput
import sqlite3
import sys
import os
import appdirs
import shutil
import datetime



class UserSetup:
    def __init__(self, database, possibleDomains):
        self.possibleDomains = possibleDomains
        self.database = database
        self.defaultTimeInterval = 30

    def saveData(self):
        print('Creating new account')
        login = self._getLogin()
        password = self._getPassword()
        domain = self._getDomain()
        timeInterval = self._getTimeInterval()
        
        self.database.newUser(login, password, domain, timeInterval)
        print('Account saved.\n')
        
        userAnswear = ''
        while userAnswear not in ['y', 'n']:
            userAnswear = input('Add new account? (y/n): ')
        print()
        if userAnswear == 'y':
            self.saveData()
        else:
            print('Setup done. You can close this window.')
            print('You can add shortcut to this file to autostarted programs')
            # print('Program is running in background now') # maybe sometime in the future
            input() # just not to close window immediately
                    
    def _getLogin(self):
        userName = input('Enter login: ')
        return userName
    
    def _getPassword(self):
        password = pwinput('Enter password: ')
        return password
    
    def _getDomain(self):
        print(f'Currently available domains: {", ".join(self.possibleDomains)}')
        domain = input(f'Select domain: ')
        domain = domain.lower()
        return domain if domain in self.possibleDomains else self._getDomain()
    
    def _getTimeInterval(self):
        while True:
            try:
                timeInterval = input(f'Enter time interval (leave empty to set {self.defaultTimeInterval} [minutes]): ')
                if not timeInterval:
                    return self.defaultTimeInterval
                if int(timeInterval) > 0:
                    return int(timeInterval)
                print('Enter positive number\n')
                
            except ValueError:
                print('Enter only number\n')
                
                
class DatabaseSetup:
    def __init__(self, databaseName):
        self._name = databaseName
        
        
    def update(self):
        '''
        Replaces data in `domainAddress` and `domainElements` tables in database in user data directory
        by data from database in pyinstaller temporary location (PTL).\n
        Does any diffrence only when data in PTL was updated
        '''
        if self._runningAsExe():
            fromPath = self._getDatabasePathFromPyinstallerTempLocation()
        else:
            fromPath = self._getDatabasePathFromSourceCodeLoaction()
        fromDb = sqlite3.connect(fromPath)
        with fromDb:
            domainAddress = fromDb.execute('SELECT * FROM domainAddress;')
            domainElements = fromDb.execute('SELECT * FROM domainElements;')    
        
        uddPath = self._getDatabasePathFromUserDataDir()
        uddDb = sqlite3.connect(uddPath)
        with uddDb:
            uddDb.execute('DELETE FROM domainAddress;')
            uddDb.execute('DELETE FROM domainElements;')
            uddDb.executemany('INSERT INTO domainAddress(domain, pageAddress) VALUES (?,?);',  domainAddress)
            uddDb.executemany('INSERT INTO domainElements VALUES (?,?,?,?);',  domainElements)
        fromDb.close()
        uddDb.close()


    def _anyUsers(self):
        '''
        returns True if there are users in database located in user app data directory\n
        returns False if users table does not exists or users table is empty
        '''
        dbPath = self._getDatabasePathFromUserDataDir()
        tempDbConnection = sqlite3.connect(dbPath)
        with tempDbConnection:
            try:
                query = tempDbConnection.execute('SELECT * FROM users')
            except sqlite3.OperationalError:
                # table does not exist
                return False
            
        return True if query.fetchall() else False # query is list so `return query` would not return bool value
        
    def getDatabasePath(self):
        '''
        Returns database path in user app data directory.\n
        When used during first program run also copies preinited database:\n
        - from PyInstaller temporary location (running as .exe)\n
        - source file location (running as .py)\n
        to the user app data directory and creates all necessary files.
        '''
        if not self._anyUsers():
            self._copyDatabase()
            
        return self._getDatabasePathFromUserDataDir()
    
    def _runningAsExe(self):
        '''
        Based on checking whether `sys._MEIPASS` variable is inited
        '''
        try:
            sys._MEIPASS
        except AttributeError:
            return False
        return True
    
    def _getDatabasePathFromPyinstallerTempLocation(self):
        return os.path.join(sys._MEIPASS, self._name)
    
    def _getDatabasePathFromSourceCodeLoaction(self):
        return os.getcwd() + f'\{self._name}'
    
    def _getDatabasePathFromUserDataDir(self):
        thisFileName = os.path.basename(sys.modules['__main__'].__file__).split('.')[0]
        retPath = appdirs.user_data_dir() + f'\{thisFileName}\{self._name}'
        self._createPathIfNotExists(retPath)
        return retPath
    
    def _copyDatabase(self):
        if self._runningAsExe():
            srcPath = self._getDatabasePathFromPyinstallerTempLocation()
        else:
            srcPath = self._getDatabasePathFromSourceCodeLoaction()
        dstPath = self._getDatabasePathFromUserDataDir()
        self._createPathIfNotExists(dstPath)
        shutil.copyfile(srcPath, dstPath)
        
        # is there a need to delete db from srcPath ??
        
    def _createPathIfNotExists(self, filePath):
        dstDir = os.path.dirname(filePath)
        if not os.path.exists(dstDir):
            os.mkdir(dstDir)


class DriverSetup:
    def __init__(self):
        self._osName = sys.platform
    
    def getDriver(self):
        '''
        Returns chromedriver for Windows or Linux system\n
        Returns safaridriver for MacOS system
        '''
        if self._osName == 'win32' or self._osName.startswith('linux'):
            return self._getDriverForChrome()
        return self._getDriverForSafari()
    
    def _getDriverOptions(self):
        if self._osName == 'win32' or self._osName.startswith('linux'):
            options = ChromeOptions()
        else:
            options = SafariOptions()
        options.headless = True
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        return options
        
    def _getDriverForChrome(self):
        options = self._getDriverOptions()
        return webdriver.Chrome('chromedriver', options=options)
        
    def _getDriverForSafari(self):
        self._enableSafariDriver()
        options = self._getDriverOptions()
        return webdriver.Safari(options=options)
        
    def _enableSafaridriver(self):
        os.system('safaridriver --enable')
    
    
class Database:
    def __init__(self, databaseName = 'database.sqlite'):
        self.name = databaseName
        self._config = DatabaseSetup(self.name)
        self._config.update()
        self.fullPath = self._config.getDatabasePath()
        self.db = sqlite3.connect(self.fullPath)
    
    def getUsers(self):
        with self.db:
            query = self.db.execute('SELECT * FROM users;')
        return query.fetchall()
            
    def newUser(self, userName, password, domain, timeInterval):
        dbRecord = (userName, password, domain, timeInterval)
        with self.db:
            self.db.execute('INSERT INTO users(userName, password, domain, timeInterval) VALUES(?,?,?,?);', dbRecord)
            
    def writeLog(self, userLogin, loopIndex, nDeletedMessages = None, info = None):
        if info is None:
            info = 'Done'
        error = info != 'Done'
        currentTime = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        with self.db:
            if error:
                dbRecord = (userLogin, loopIndex, error, info, currentTime)
                self.db.execute('INSERT INTO logs(userName, loop_id, error, info, date) VALUES(?,?,?,?,?);', dbRecord)
            else:
                dbRecord = (userLogin, loopIndex, error, info, nDeletedMessages, currentTime)
                self.db.execute('INSERT INTO logs(userName, loop_id, error, info, deleted, date) VALUES(?,?,?,?,?,?);', dbRecord)
                        
    def getPageAddress(self, domain):
        with self.db:
            query = self.db.execute('SELECT pageAddress FROM domainAddress WHERE domain == ?', [domain])
        return query.fetchall()[0][0]
    
    def getElements(self, domain):
        with self.db:
            query = self.db.execute('SELECT elementName, by, value FROM domainElements WHERE domain = ?', [domain])
        return {item[0] : {'by' : item[1], 'value': item[2]} for item in query.fetchall()}


class NoSuccessInNTrials(Exception):
    '''
    Cast in `Common._errorHandler` when no success in `nTrials`.
    Catch in derived class to go to sleep for `sleepTime`
    '''