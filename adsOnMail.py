from setups import UserSetup, Database
from domains import Common

import multiprocessing
import sys


noUserSetup = len(sys.argv) > 1 and sys.argv[1] == 'nosetup'
    
    
class Main:
    def __init__(self, noUserSetup):
        self.noUserSetup = noUserSetup
        self.database = Database()
        
        self.domainClassDict = {class_.__name__.lower() : class_ for class_ in Common.__subclasses__()}
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
        if not noUserSetup:
            self._initUsers()
            exit()
        users = self.database.getUsers()
        classObjects = [self._getClassObjects(user) for user in users]
        return classObjects
        
    def run(self):
        classObjects = self._setup()
        self.processes = [multiprocessing.Process(target=class_.run) for class_ in classObjects]
        [process.start() for process in self.processes]
        
       

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main = Main(noUserSetup)
    main.run()
    
    
