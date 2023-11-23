# Finance
A web app designed to get quotes for stocks and then subsequently buy and sell stocks as well as view transaction history for users.
Please note that although this app is full-stack, front-end was not prioritised during development.

## Technologies
Front-End: HTML5, CSS, Bootstrap, JavaScript.

Back-end: Python, Flask, Jinja2, Postgresql, Psycopg2.

## Features

## Communal

### Login, Register and Logout
- The login page contains all paths for registering and logging in to the Finance app. When registering, users provide their personal details, before their password is hashed for security and their created account is stored in the postgresql database.
- All acounts follow the same route when logging out, and will be redirected to the login page.

## User-Specific

### Home page
- Displays user cash balance (starts at 10k), current portfolio valuation as well as current stock holdings.

### Quotes
- Users can get a quote for a stock by inputting its ticker symbol which will then interact with the Yahoo Finance API to fetch the current price of the stock. Users are then redirecting to a page that presents the current value of a single share of the stock.

### Buying stocks
- The buy page enables users to enter a ticker symbol for a stock as well as a desired quantity for purchase. Provided the stock exists and the user has sufficient cash in their balance, a purchase order is made and both balance and holding are updated as well as a transaction receipt entered into their history.

### Selling stocks
- The sell page enables users to select any of the stocks they currently hold from a drop down as well as the quantity they would like to sell. Provided they own at least the quantity selected for sale, a sales order is executed and the user's balance and holding are updated accordingly. A sell transaction is added to their history.

# Version 2 Plans
I plan to update the front-end of this app once I am more comfortable using CSS and JS. I also plan to use the structure of this Flask app to create a more complex app.
