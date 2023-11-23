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

    dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
    return dt_string


def contains_number(input_string):
    return bool(re.search(r'\d', input_string))


def fetch_row(query, arguments):
    """
    Executes a SELECT query on the database using the provided SQL query and arguments,
    fetching a single row and returning it as a  dictionary.

    This function is designed for SELECT queries that retrieve rows from the database.
    Each row is represented as a dictionary, where the keys are column names and
    the values are the corresponding values in the row.

    Parameters:
    - query (str): The SQL SELECT query to be executed.
    - arguments (tuple, optional): The arguments to be passed to the query placeholders.
      Defaults to None.
    """
    connection = None
    try:
        params = dbconfig()
        connection = connect(**params)

        with connection:
            with connection.cursor() as crsr:
                crsr.execute(query, arguments)
                row = crsr.fetchone()

                if row is not None:
                    # Get column names from cursor description
                    column_names = [desc[0] for desc in crsr.description]

                    # Create a dictionary with column names as keys
                    row_dict = {column_names[i]: row[i] for i in range(len(column_names))}
                    return row_dict
                else:
                    return None
    except(Exception, DatabaseError) as error:
        print(error)


def fetch_rows(query, arguments=None):
    """
    Executes a SELECT query on the database using the provided SQL query and arguments,
    fetching all resulting rows and returning them as a list of dictionaries.

    This function is designed for SELECT queries that retrieve rows from the database.
    Each row is represented as a dictionary, where the keys are column names and
    the values are the corresponding values in the row.

    Parameters:
    - query (str): The SQL SELECT query to be executed.
    - arguments (tuple, optional): The arguments to be passed to the query placeholders.
      Defaults to None.
    """
    connection = None
    result = []
    
    try:
        params = dbconfig()
        connection = connect(**params)

        with connection:
            with connection.cursor() as crsr:
                crsr.execute(query, arguments)
                columns = [desc[0] for desc in crsr.description]
                rows = crsr.fetchall()
                
                for row in rows:
                    row_dict = {columns[i]: row[i] for i in range(len(columns))}
                    result.append(row_dict)

        return result
    except (Exception, DatabaseError) as error:
        print(error)
        return result

def modify_rows(query, arguments):
    """
    Executes a modification query on the database using the provided SQL query and arguments.

    This function is designed for executing queries that modify the rows in the database,
    such as INSERT, UPDATE, or DELETE statements.

    Parameters:
    - query (str): The SQL query to be executed.
    - arguments (tuple): The arguments to be passed to the query placeholders.
    """
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