import os
from psycopg2 import connect, DatabaseError
from flask import Flask, flash, redirect, render_template, request, session, g
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from helpers import *
from datetime import datetime

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)




@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    cash_balance_rows = fetch_rows("SELECT cash FROM users WHERE id = %s;", (session["user_id"],))
    cash_balance = int(cash_balance_rows[0]['cash'])

    # Query db for the stocks owned and shares
    stocks_owned = fetch_rows("SELECT DISTINCT(stock), quantity FROM portfolio WHERE user_portfolio_id = %s;", (session["user_id"],))
    
    print(f'STOCKS OWNED ARE: {stocks_owned}')

    # If stocks owned is zero, remove from db
    for stock in stocks_owned:
        stock_quantity = stock['quantity']
        print(f'stock quantity is {stock_quantity}')
        if stock_quantity == 0:
            modify_rows("DELETE FROM portfolio WHERE stock = %s;", stock['stock'])
    # Query Yahoo Finance API to fetch current price and then calc holding value, add both values to respective dicts for stocks
        # Send stock name to lookup func
        fetched_data = lookup(stock['stock'])
 
        # Create current price key in stock dict based on the price fetched using
        stock['current_price'] = fetched_data['price']
        stock['holding_value'] = stock['current_price'] * float(stock['quantity'])
        print(stock)

    total_stock_valuation = 0
    for stock in stocks_owned:
        total_stock_valuation += float(stock["holding_value"])
    print(total_stock_valuation)
    # Calculate total portfolio valuation
 
    print(f'TOTAL STOCK VALUATION IS OF TYPE {type(total_stock_valuation)}')
    portfolio_valuation = cash_balance + total_stock_valuation
    formatted_portfolio_valuation = format(portfolio_valuation, ".2f")
    formatted_cash_balance = format(cash_balance, ".2f")

    return render_template("index.html", cash_balance=formatted_cash_balance, portfolio_valuation=formatted_portfolio_valuation, stocks_owned=stocks_owned)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        return render_template("buy.html")

    elif request.method == "POST":
        # apology if symbol input is blank
        if not request.form.get("symbol"):
            return apology("You must enter a stock!")
        if not request.form.get("shares"):
            return apology("You must enter a quantity!")
        # apology if symbol doesn't exist
        if lookup(request.form.get("symbol")) == None:
            return apology("This stock doesn't exist")
        # If the POST submission is all good
        else:
            # get shares and symbols and pass to variables
            try:
                shares = int(request.form.get("shares"))
            except ValueError:
                return apology("Needs to be an int", 400)
            stock = request.form.get("symbol").upper()
            if shares < 0:
                return apology("Enter a positive integer quantity!")

            # Check stock price
            stock_price = float(lookup(stock)["price"])
            # Check user's cash balance
            user_balance = (fetch_row("SELECT cash from USERS WHERE id = %s;",(session["user_id"],)))['cash']
            print(f'USER BALANCE IS: {user_balance}')
            # render apology if user cannot afford purchase
            order_total = stock_price * shares
            user_balance = float(user_balance)
            if user_balance < order_total:
                return apology("You don't have sufficient funds for this order!")
            else:
                # Add purchase to transactions table
                transaction_dt  = datetime.strptime(get_date_time(), '%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                print(f'TRANSACTION DT IS {transaction_dt}')

                modify_rows("INSERT INTO transactions (type, user_id, stock, price, quantity, order_total, purchase_date) VALUES (%s, %s, %s, %s, %s, %s, %s);",
                        ("buy", session["user_id"], stock, stock_price, shares, order_total, transaction_dt))
                # Update user's cash balance
                modify_rows("UPDATE users SET cash = cash - %s WHERE id = %s;", (order_total, session["user_id"]))
                print('SUCCESSFULLY UPDATED USERS BALANCE')
                # Update user's portfolio holdings of this stock
                # Check if user holds any of this stock already
                user_id_records = fetch_rows(
                    "SELECT user_portfolio_id FROM portfolio WHERE stock = %s", (stock,))
                print(f'USER ID RECORDS IS: {user_id_records}')
                user_id_list = [t['user_portfolio_id'] for t in user_id_records]
                # Creates list of users who own the stock being bought
                print(f'USER WHO OWN {stock} ARE: { user_id_list}')
                """This query will insert a new record for stock purchase if they haven't bought this stock before"""
                if session["user_id"] not in user_id_list:
                    print('USER HAS NOT BOUGHT THIS STOCK BEFORE')
                    modify_rows("INSERT INTO portfolio (user_portfolio_id, stock, quantity) VALUES (%s, %s, %s);",
                            (session["user_id"], stock, shares))
                else:
                    print('THIS USER OWNS SOME OF THIS STOCK ALREADY')
                    modify_rows("UPDATE portfolio SET quantity = (quantity + %s) WHERE stock = %s AND user_portfolio_id = %s",
                            (shares, stock, session["user_id"]))

            return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    if request.method == "GET":
        transactions = fetch_rows(
            "SELECT stock, type, price, quantity, purchase_date FROM transactions WHERE user_id = %s;", (session["user_id"],))
        print(f'here are the transactions" \n {transactions}')
        transactions = transactions[::-1]
        for trans in transactions:
            trans['price'] = format(float(trans['price']), ".2f")
            trans['quantity'] = format(float(trans['quantity']), ".2f")
        return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
       return render_template("login.html")
    # User reached route via POST (as by submitting a form via POST)
    else:
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)
        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        
        username = request.form.get("username")
        # Query database for username
        rows = fetch_row("SELECT * FROM users WHERE username = %s", (username,))

        print(f'ROWS RETURNS {rows}')
        # Ensure username exists and password is correct
        if not rows or not check_password_hash(rows['hash'], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows['id']
        print(session["user_id"])

        # Redirect user to home page
        return redirect("/")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")

    elif request.method == "POST":
        symbol = request.form.get("symbol")
        if lookup(symbol) == None:
            return apology("This stock doesn't exist", 400)
        else:
            symbol_dict = lookup(symbol)

            symbol_dict["price"] = "{:.2f}".format(symbol_dict["price"])
            print(symbol_dict["price"])

            return render_template("quoted.html", symbol_dict=symbol_dict)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    render_template("register.html")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        existing_users = fetch_users("SELECT username FROM users;")
        list_users = [item[0] for item in existing_users]
        # check if any fields are empty
        if len(username) == 0 or len(password) == 0 or len(confirmation) == 0:
            return apology("One or more fields are empty!")
       # check passwords match
        elif password != confirmation:
            return apology("The password confirmation does not match!")
        # Check special characters for password
        if contains_number(password) != True:
            return apology("The password does not contain a number!")

        # check username isn't already in db
        elif username in list_users:
            return apology("This username is already taken!")
        else:
            modify_rows("INSERT INTO users (username, hash, cash) VALUES (%s, %s, %s);",
                      (username, generate_password_hash(password), 10000.00))
            registrants = fetch_row("""SELECT * FROM users WHERE username = %s;""", (username,))
            print(f'REGISTRANTS IS {registrants}')
            print(f'CURRENT USER IS: {registrants["username"]}')
            session["user_id"] = registrants['id']
            print(f' CURRENT SESSION ID IS: {session["user_id"]}')
            return render_template("login.html")

    # User reached route via GET (as by clicking a link or via redirect)
    elif request.method == "GET":
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":

        stock = request.form.get("symbol")
        stock_info = lookup(stock)
        current_stock_price = stock_info['price']
        shares = float(request.form.get("shares"))
        users_stocks = fetch_rows("SELECT DISTINCT(stock) FROM portfolio WHERE user_portfolio_id = %s", (session["user_id"],))
        users_shares = fetch_rows(
            "SELECT quantity FROM portfolio WHERE user_portfolio_id = %s AND stock = %s", (session["user_id"], stock))
        
        stock_list = [dict["stock"] for dict in users_stocks]

        if not stock:
            return apology("You didn't select a stock!")
        elif stock not in stock_list:
            return apology(f"You don't own any {stock}!")
        elif shares < 1:
            return apology("You need to enter a positive number!")
        elif shares > int(users_shares[0]["quantity"]):
            return apology("You don't have that many shares to sell!")
        else:
            # Update transactions table with a sell order and also update their shares
            order_total = current_stock_price * shares
            transaction_dt = get_date_time()
            print(f'TRANSACTION DT IS {transaction_dt}')
            """ THIS QUERY IS EXECUTING"""
            modify_rows("INSERT INTO transactions (type, user_id, stock, price, quantity, order_total, purchase_date) VALUES (%s, %s, %s, %s, %s, %s, %s);",
                    ("sell", session["user_id"], stock, current_stock_price, shares, order_total, transaction_dt))
            # Update user's portfolio holdings of this stock
            modify_rows("UPDATE portfolio SET quantity = (quantity - %s) WHERE stock = %s AND user_portfolio_id = %s",
                    (shares, stock, session["user_id"]))
            print(f'Decreased shares of {stock} by {shares}')
        # if stocks owned is zero, remove from db
            stocks_owned = fetch_rows(
                "SELECT DISTINCT(stock), quantity FROM portfolio WHERE user_portfolio_id = %s", (session["user_id"],))

            for stock in stocks_owned:
                if stock['quantity'] == 0.0:
                    modify_rows("DELETE FROM portfolio WHERE stock = %s", (stock['stock']))
            # Update user's cash balance
            modify_rows("UPDATE users SET cash = (cash + %s) WHERE id = %s", (order_total, session["user_id"]))
            print('updated stock holdings')
            return redirect("/")

    elif request.method == "GET":
        # Query db for the stocks owned and shares
        stocks_owned = fetch_rows(
            "SELECT DISTINCT(stock), SUM(quantity) as quantity FROM portfolio WHERE user_portfolio_id = %s GROUP BY stock;", (session["user_id"],))
        print('stocks owned to sell are:')
        print(stocks_owned)
        return render_template("sell.html", stocks_owned=stocks_owned)


if __name__ == '__main__':
    app.run(debug=True)