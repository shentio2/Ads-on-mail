from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
import time
from pwinput import pwinput
import traceback
import datetime
import sqlite3
import inspect
import multiprocessing
import functools
import os
import appdirs
import sys
import shutil



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
                return int(timeInterval) if timeInterval else self.defaultTimeInterval
            except ValueError:
                print('Enter only number\n')
                
                
class DatabaseSetup:
    def __init__(self, databaseName):
        self._name = databaseName
        
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
        thisFileName = os.path.basename(__file__).split('.')[0]
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
            
            
class Database:
    def __init__(self, databaseName = 'database.sqlite'):
        self.name = databaseName
        self._config = DatabaseSetup(self.name)
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
    
    
class Main:
    def __init__(self):
        self.database = Database()
        self.possibleClasses = [Wp]
        self.domainClassDict = {class_.__name__.lower() : class_ for class_ in self.possibleClasses}
        # keys -> class name as string
        # values -> actual class object
        self.processes = []

    def _initUsers(self):
        possibleDomains = list(self.domainClassDict.keys())
        setupper = UserSetup(self.database, possibleDomains)
        setupper.saveData()
        
    def _minutesToSeconds(self, minutes):
        return minutes*60
        
    def _getClassObjects(self, user):
        login = user[1]
        password = user[2]
        domain = user[3]
        timeInterval = self._minutesToSeconds(user[4])
        
        domainClass = self.domainClassDict[domain]
        worker = domainClass(login, password, timeInterval)
        return worker
        
    def _setup(self):
        users = self.database.getUsers()
        if not users:
            self._initUsers()
            exit()
        classObjects = [self._getClassObjects(user) for user in users]
        return classObjects
        
    def run(self):
        classObjects = self._setup()
        self.processes = [multiprocessing.Process(target=class_.run) for class_ in classObjects]
        [process.start() for process in self.processes]
        
        
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
    
        
class Common:
    '''
    Base class for all domain specific classes\n
    Provide basic configuration, functions, error handling, database access, logs handling and data gathering
    '''
    def __init__(self, userLogin, userPassword, timeInterval, domain):
        self.database = None
        self.driver = None
        self.info = None
        self.domain = domain
        self.userLogin = userLogin
        self.userPassword = userPassword
        self.timeInterval = timeInterval
        self.loopIndex = 0
        self.nSelectedMessages = 0
        self._config = DriverSetup()
        self.defaultNTrialsBeforeError = 5
        self.defaultTimeIntervalBetweenTrials = 0.2
        self.defaultRefreshOnError = False
        
    def setup(self):
        self.database = Database()
        self.info = self.getElements(self.domain)
        self.closeDriver()
        self.driver = self._config.getDriver()
        
    def closeDriver(self):
        if self.driver is not None:
            self.driver.close()
            self.driver = None
    
    def getElements(self, domain):
        return self.database.getElements(domain)
    
    def waitForElement(self, by, value, timeout = 10):
        try:
            element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        except TimeoutException as e:
            return None
        return element

    def waitForPage(self, timeout = 10):
        WebDriverWait(self.driver, timeout).until(
            lambda x: x.execute_script("return document.readyState === 'complete'")
        )
        
    def refreshPage(self, additionalSleepTime = 0):
        self.driver.refresh()
        self.waitForPage()
        if additionalSleepTime:
            time.sleep(additionalSleepTime)
        
    def fillInput(self, inputElement, value, nTries=5):
        for index in range(nTries):
            try:
                inputElement.send_keys(value)
                return
            except ElementNotInteractableException as e:
                if index < nTries-1:
                    time.sleep(0.5)
                else:
                    self.writeLog(errorInfo = traceback.format_exc())
                    raise NoSuccessInNTrials
                
    def clickOnElement(self, element):
        '''
        This function is more reliable than running just `element.click()`.\n
        It does not require element to be on the top layer in contrast to
        `element.click()` (element can be for example covered by navbar)
        '''
        self.driver.execute_script("arguments[0].click();", element)
        
    
    def _getParameter(self, function, functionKwargs, paramName, defaultVal):
        '''
        Returns `paramName` value passed to `function` if `paramName` was passed to `function` or \n
        returns `paramName` default value if `function` has default value or \n
        returns `defaultVal`
        '''
        param = functionKwargs.get(paramName)
        if param is None:
            pom = inspect.signature(function).parameters.get(paramName)
            param = pom.default if pom is not None else defaultVal
        return param

    def _errorHandler(function):
        @functools.wraps(function)
        def modFun(*args, **kwargs):
            classSelf = args[0] # first arg passed to `function` is `self`
            nTries = classSelf._getParameter(function, kwargs, 'nTries', classSelf.defaultNTrialsBeforeError)
            tryAgainInterval = classSelf._getParameter(function, kwargs, 'tryAgainInterval', classSelf.defaultTimeIntervalBetweenTrials)
            refreshOnError = classSelf._getParameter(function, kwargs, 'refreshOnError', classSelf.defaultRefreshOnError)
            
            for index in range(nTries):
                try:
                    return function(*args, **kwargs)
                except:
                    if index < nTries-1:
                        time.sleep(tryAgainInterval)
                        if refreshOnError:
                            classSelf.refreshPage()
                    else:
                        classSelf.writeLog(errorInfo = traceback.format_exc())
                        raise NoSuccessInNTrials
        return modFun
                
    @_errorHandler
    def runPage(self, tryAgainInterval = 30, **kwargs):
        pageAddress = self.database.getPageAddress(self.domain)
        self.driver.get(pageAddress)
        
    @_errorHandler
    def acceptCookies(self, **kwargs):
        buttonInfo = self.info['acceptCookies']
        acceptCookiesButton = self.waitForElement(buttonInfo['by'], buttonInfo['value'])
        if acceptCookiesButton is not None:
            self.clickOnElement(acceptCookiesButton)
    
    @_errorHandler
    def login(self, refreshOnError = True, **kwargs):
        loginInfo = self.info['loginInput']
        passwordInfo = self.info['passwordInput']
        buttonInfo = self.info['loginButton']
        
        loginInput = self.waitForElement(loginInfo['by'], loginInfo['value'])
        passwordInput = self.waitForElement(passwordInfo['by'], passwordInfo['value'])
        loginButton = self.waitForElement(buttonInfo['by'], buttonInfo['value'])
        
        # it has to be in `fillInput` function
        # otherwise it could fill `loginInput` multiple times in case of error in `passwordInput`
        self.fillInput(loginInput, self.userLogin)
        self.fillInput(passwordInput, self.userPassword)
        self.clickOnElement(loginButton)
                
    @_errorHandler
    def afterLoginRoutine(self, **kwargs):
        time.sleep(5)
        self.refreshPage(additionalSleepTime = 5)
        
    @_errorHandler
    def getMessages(self, **kwargs):
        messageInfo = self.info['message']
        anyMessage = self.waitForElement(messageInfo['by'], messageInfo['value'])
        if anyMessage is not None:
            time.sleep(3)
            messages = self.driver.find_elements(messageInfo['by'], messageInfo['value'])
            return messages
        return []
        
    @_errorHandler
    def selectAdMessagesByTopic(self, messages, endsWithString, refreshOnError = True, **kwargs):
        nSelectedMessages = 0
        topicInfo = self.info['messageTopic']
        selectInfo = self.info['messageSelect']
        for message in messages:
            messageTopic = message.find_element(topicInfo['by'], topicInfo['value']).text
            selectButton = message.find_element(selectInfo['by'], selectInfo['value'])
            if messageTopic.endswith(endsWithString):
                self.clickOnElement(selectButton)
                nSelectedMessages += 1
        self.nSelectedMessages += nSelectedMessages
                
    @_errorHandler
    def deleteSelectedMessages(self, **kwargs):
        deleteButtonInfo = self.info['deleteButton']
        deleteButton = self.driver.find_element(deleteButtonInfo['by'], deleteButtonInfo['value'])
        self.clickOnElement(deleteButton)
        
    @_errorHandler
    def switchTab(self, tabName, **kwargs):
        tabInfo = self.info[tabName]
        time.sleep(1)
        tab = self.driver.find_element(tabInfo['by'], tabInfo['value'])
        self.clickOnElement(tab)
        self.waitForPage()
        time.sleep(3)
        
    def goToSleep(self):
        sleepTime = self.timeInterval - int((datetime.datetime.now()-datetime.datetime(1970,1,1)).total_seconds())%self.timeInterval
        time.sleep(sleepTime)
        self.nSelectedMessages = 0
        self.loopIndex += 1
        
    def writeLog(self, errorInfo = None):
        self.database.writeLog(self.userLogin, self.loopIndex, self.nSelectedMessages, errorInfo)
            
    @staticmethod
    def loop(function):
        @functools.wraps(function)
        def modFun(*args, **kwargs):
            classSelf = args[0] # first arg passed to `function` is `self`
            while True:
                try:
                    function(*args, **kwargs)
                except NoSuccessInNTrials:
                    classSelf.goToSleep()
                    
        return modFun
        
        
class Wp(Common):
    def __init__(self, userLogin, userPassword, timeInterval):
        Common.__init__(self, userLogin, userPassword, timeInterval, 'wp')
        self.adMessageEndsWith = '/WP'

    @Common.loop
    def run(self):
        self.setup()
        self.runPage()
        self.acceptCookies()
        self.login()
        
        for _ in range(5):
            self.afterLoginRoutine()
            
            for tabName in ['offertsTab', 'mainTab']:
                messages = self.getMessages()
                if messages:
                    self.selectAdMessagesByTopic(messages, self.adMessageEndsWith)
                    self.deleteSelectedMessages()
                self.switchTab(tabName)
            
            self.writeLog()
            self.goToSleep()
        

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main = Main()
    main.run()