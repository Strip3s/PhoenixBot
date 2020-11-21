# Phoenix Bot
[Support Discord](https://discord.gg/Ag6wnAf4Qu)<br/><br/>
Phoenix Bot is inspired by Natewong1313's Bird Bot project yet due to lack of activity by their team. We have decided to revive this project to achieve a common goal. Due to the recent insurgence of botters/scalpers taking advantage, our goal is to enable everyone the ability to combat these botters/scalpers by implementing their own botting system. Currently, this auto-checkout bot will support Walmart and Best Buy. There are more plans for future implementations later on. 

* Easy to use interface built on PyQt5
* Waits for items to restock if they are out of stock
* Optional price checker
* Lighting fast auto-checkout

<p align="center">
  <img src="https://i.imgur.com/E105F74.png" alt="Bird Bot UI" width="738">
</p>

## Phoenix Bot Repository Link
[View The Repo Here](https://github.com/Strip3s/PhoenixBot.git/)

## Quick Install for Windows
1. Make sure your Chrome browser is updated to the latest
2. Open Powershell as Administrator within your desired directory for the application to live.
3. Run the following commands: 
      ```
      git clone https://github.com/Strip3s/PhoenixBot/
      ```
      ```
      cd PhoenixBot
      ```
      ```
      python -m venv ./env
      ```
      ```
      ./env/Scripts/activate
      ```
      ```
      pip install -r requirements.txt
      ```
4. If you encounter any errors during installation, please consider the following:
    * If you get a red text error remove and you previously installed pyqt5 or lxml on your python,  remove the versions from the **requirements.txt** for both lxml and pyqt5.
    * If you get an error with red text run the following: 
     ```
     pip install pycryptodomex
     ```
5. Run the following command:
   ```
   python app.py
   ```

## Quick Install for Mac
**It is highly recommended you install brew and update python3 to latest version**

1. Make sure your Chrome browser is updated to the latest
2. Run the following commands: 
      ```
      git clone https://github.com/Strip3s/PhoenixBot/
      ```
      ```
      cd PhoenixBot
      ```
      ```
      python3 -m venv ./env
      ```
      ```
      source env/bin/activate
      ```
      ```
      pip3 install -r requirements.txt
      ```
3. If you encounter any errors during installation, please consider the following:
    * If you get a red text error remove and you previously installed pyqt5 or lxml on your python,  remove the versions from the **requirements.txt** for both lxml and pyqt5.
    * If you get an error with red text run the following: 
     ```
     pip3 install pycryptodomex
     ```
4. Run the following command:

   ```
   python3 app.py
   ```


## Windows FAQs
To resume working on the bot for testing after closing powershell, navigate again to the folder and run the following commands:
  ```
  ./env/Scripts/activate
  python app.py
  ```