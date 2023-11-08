lst = [1,2,3]

lst.append(4)

print(lst)

def fetch_rows(query, arguments=None):
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

print(fetch_rows(("SELECT cash from USERS WHERE id = %s;",(25,))))