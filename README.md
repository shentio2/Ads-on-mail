# About
- Program to delete ads recived on e-mail accounts. 
- Runs on system startup and then accordingly to time interval specified during setup (default 30 minutes, for example: 10:17, 10:30, 11:00 and so on)
- Enables multiple accounts connected and processed at once
- Uses database in user app data directory to store information about user data*, logs and domain specific page elements (*see Known issues section)
- Make implementing functionality for new domains easier by providing class ```Common``` with basic configuration, functions, error handling, database access, logs handling and data gathering<br>

Implemented domains: wp.pl, interia.pl

# Setup to use as .exe:
0. Intall all necessary libraries
1. On Windows or Linux download chromedriver.exe and put in source file location. Make sure your Google Chrome version is compatibile with chromedriver version. As far as I know no need to download anything on MacOS as it provides safaridriver by default.
2. Run ```initDatabase.py``` to create database and initialize it with page elements info
3. Make executable
    - on Windows run ```pyinstaller --onefile --add-data "database.sqlite;." adsOnMail.py```
    - on Linux/MacOS run ```pyinstaller --onefile --add-data "database.sqlite:." adsOnMail.py```
4. On Windows or Linux move chromedriver.exe to dist folder
5. Run adsOnMail.exe and setup users
6. \<No name for this step yet\>
    - on Windows move ```backgroundAdsOnMail.cmd``` to dist folder
    - on Linux/MacOS move ```backgroundAdsOnMail.sh``` to dist folder
7. Optionally create shortcut to moved file in startup folder so that script runs automatically when computer is on<br>

# Run as .py:
To run as .py only three first steps from above section are required


# Known issues:
- passwords are stored as plain text in database that needs no authentication. Passwords can be stored in decrypted form, but they have to be encrypted at the certain point in program anyway (when filling login input) and that would require storing keys as well.
- when computer is put out of sleep mode, script does not run immediately but sleeps as it has never been in a sleep mode (but it's not the case when computer is turned off/on)
- tested only on Windows so there is a chance it doesn't work on other operational systems even though there is os-dependent functionality implemented (like user app data path, browser used by webdriver)