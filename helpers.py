import csv
import pytz
import requests
import subprocess
import urllib
import uuid
import datetime
import re
from psycopg2 import connect, DatabaseError
from dbconfig import dbconfig
from flask import redirect, render_template, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    # Prepare API request
    symbol = symbol.upper()
    end = datetime.datetime.now(pytz.timezone("US/Eastern"))
    start = end - datetime.timedelta(days=7)

    # Yahoo Finance API
    url = (
        f"https://query1.finance.yahoo.com/v7/finance/download/{urllib.parse.quote_plus(symbol)}"
        f"?period1={int(start.timestamp())}"
        f"&period2={int(end.timestamp())}"
        f"&interval=1d&events=history&includeAdjustedClose=true"
    )

    # Query API
    try:
        response = requests.get(url, cookies={"session": str(uuid.uuid4())}, headers={
                                "User-Agent": "python-requests", "Accept": "*/*"})
        response.raise_for_status()

        # CSV header: Date,Open,High,Low,Close,Adj Close,Volume
        quotes = list(csv.DictReader(response.content.decode("utf-8").splitlines()))
        quotes.reverse()
        price = round(float(quotes[0]["Adj Close"]), 2)
        return {
            "name": symbol,
            "price": price,
            "symbol": symbol
        }
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"


def get_date_time():

    # datetime object containing current date and time
    now = datetime.datetime.now()

    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    return dt_string


def contains_number(input_string):
    return bool(re.search(r'\d', input_string))


def fetch_row(query, arguments):
    connection = None
    try:
        params = dbconfig()
        connection = connect(**params)

        with connection:
            with connection.cursor() as crsr:
                crsr.execute(query, arguments)
                row = crsr.fetchone()
                return row
    except(Exception, DatabaseError) as error:
        print(error)

def fetch_rows(query, arguments=None):
    connection = None
    try:
        params = dbconfig()
        connection = connect(**params)

        with connection:
            with connection.cursor() as crsr:
                crsr.execute(query, arguments)
                rows = crsr.fetchall()
                return rows
    except(Exception, DatabaseError) as error:
        print(error)

def modify_rows(query, arguments):
    connection = None
    try:
        params = dbconfig()
 
        connection = connect(**params)

        with connection:
            with connection.cursor() as crsr:
                crsr.execute(query, arguments)
                connection.commit()
    except(Exception, DatabaseError) as error:
        print(error)

def fetch_users(query):
    connection = None
    try:
        params = dbconfig()
        connection = connect(**params)

        with connection:
            with connection.cursor() as crsr:
                crsr.execute(query)
                rows = crsr.fetchall()
                return rows
    except(Exception, DatabaseError) as error:
        print(error)

def reformat_rows(rows: tuple) -> list:
    """
    Converts a list of tuples to a list of lists.

    Args:
        tuples_list (list): List of tuples.

    Returns:
        list: List of lists.
    """
    return [list(item) for item in rows]