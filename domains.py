from setups import DriverSetup, Database, NoSuccessInNTrials

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
import time
import traceback
import inspect
import functools
import datetime



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
    def selectAdMessagesByEndString(self, messages, endsWithString, refreshOnError = True, **kwargs):
        nSelectedMessages = 0
        discriminativeInfo = self.info['messageDiscriminative']
        selectInfo = self.info['messageSelect']
        for message in messages:
            messageTopic = message.find_element(discriminativeInfo['by'], discriminativeInfo['value']).text
            selectButton = message.find_element(selectInfo['by'], selectInfo['value'])
            if messageTopic.endswith(endsWithString):
                self.clickOnElement(selectButton)
                nSelectedMessages += 1
        self.nSelectedMessages += nSelectedMessages
                
    @_errorHandler
    def deleteSelectedMessages(self, **kwargs):
        deleteButtonInfo = self.info['deleteButton']
        deleteButton = self.waitForElement(deleteButtonInfo['by'], deleteButtonInfo['value'])
        if deleteButton is not None:
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
                    self.selectAdMessagesByEndString(messages, self.adMessageEndsWith)
                    self.deleteSelectedMessages()
                self.switchTab(tabName)
            
            self.writeLog()
            self.goToSleep()
            
            
# SO FAR TEST ONLY
class Interia(Common):
    def __init__(self, userLogin, userPassword, timeInterval):
        Common.__init__(self, userLogin, userPassword, timeInterval, 'interia')
        self.adMessageEndsWith = 'dostarczone przez Interię'
        
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
                    self.selectAdMessagesByEndString(messages, self.adMessageEndsWith)
                    self.deleteSelectedMessages()
                self.switchTab(tabName)
                    
            self.writeLog()
            self.goToSleep()
            