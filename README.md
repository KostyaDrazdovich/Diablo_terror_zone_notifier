# Project Description
The project allows you to run and configure a backend for your Telegram bot, which would send notifications if the current terror zone selected by the user needs notification.
The bot is currently in version 0.8.0. 
The following is planned:

* Transition from data storage in json to your own SQL database.
* Transition from schedule to asyncio.
* Packaging code and database in Docker containers for easy startup.

### To use for personal purposes, you need:

* Have Python version 3.10 or higher.
* Select venv, run the command pip install -r requirements/packages.
* Get a token to call the API - https://d2runewizard.com/integration#authorization and insert it into auth_data.py.
* Get a token for the Telegram bot from Telegram.
* Run main.py.

The information about the current terror zones is provided by https://d2runewizard.com. 
If you have any questions or feedback, please feel free to contact the bot creator via 
Discord: https://discordapp.com/users/663745370177798186/ 
Email: konstantindrazdovich@gmail.com
LinkedIn: https://www.linkedin.com/in/kdrazdovich/