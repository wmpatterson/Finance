from helpers import fetch_rows, fetch_row, modify_rows, fetch_users, reformat_rows
stock = 'TSLA'

user_id_records = fetch_rows(
                    "SELECT user_portfolio_id FROM portfolio WHERE stock = %s", ('TSLA',))

print(user_id_records)
user_id_list = [t[0] for t in user_id_records]
print(user_id_list)