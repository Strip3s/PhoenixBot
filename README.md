# Phoenix Bot
[Discord](https://discord.gg/mTp4awX9wB)<br/><br/>
Phoenix Bot is inspired by Natewong1313's Bird Bot project yet due to lack of activity by their team. We have decided to revive this project to achieve a common goal. Due to the recent insurgence of botters/scalpers taking advantage, our goal is to enable everyone the ability to combat these botters/scalpers by implementing their own botting system. Currently, this auto-checkout bot will support Walmart, Best Buy, Gamestop, & Target. There are more plans for future implementations later on. 

* Easy to use interface built on PyQt5
* Waits for items to restock if they are out of stock
* Optional price checker
* Lighting fast auto-checkout

## Current Functionality

| **Website** | **Auto Checkout** | **Open Cart Link** | **Work In Progress** |
|:---:|:---:|:---:|:---:|
| amazon.com | | |`✔`|
| bestbuy.com | |`✔`| |
| gamestop.com |`✔`| | |
| target.com |`✔`| | |
| walmart.com |`✔`| | |

<p align="center">
  <img src="https://imgur.com/pILriDO.png" alt="Phoenix Bot UI" width="738">
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
      python -m pip install --upgrade pip 
      ```
      ```
      pip install -r requirements.txt
      ```
4. If you encounter any errors during installation, please consider the following:
    * If you get a red text error remove and you previously installed pyqt5 or lxml on your python, remove the versions from the **requirements.in** for both lxml and pyqt5, then run the following commands:
    ```
    pip install pip-tools==5.4.0
    ```
    ```
    pip-compile --generate-hashes --no-index --output-file=requirements.txt requirements.in
    ```
    ```
    pip install -r requirements.txt
    ```
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
      python3 -m pip3 install --upgrade pip 
      ```
      ```
      pip3 install -r requirements.txt
      ```
3. If you encounter any errors during installation, please consider the following:
    * If you get a red text error remove and you previously installed pyqt5 or lxml on your python,  remove the versions from the **requirements.in** for both lxml and pyqt5, then run the following commands:
    ```
    pip3 install pip-tools==5.4.0
    ```
    ```
    pip-compile --generate-hashes --no-index --output-file=requirements.txt requirements.in
    ```
    ```
    pip3 install -r requirements.txt
    ```
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


## Contributing
This project uses pip-compile with the --generate-hashes flag to validate dependencies via checksums. This helps prevent updates to existing package versions on PyPI from adding new code to our project. When changing requirements, make updates in the requirements.in file, then compile using the command below to update requirements.txt before committing.
```
pip-compile --generate-hashes --no-index --output-file=requirements.txt requirements.in
```
If you receive an error when running this command related to pinning a version of pip, make sure your system or virtualenv pip version is up to date by running the following command:
```
python -m pip install --upgrade pip
```