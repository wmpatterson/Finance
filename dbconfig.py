from configparser import ConfigParser

def dbconfig(filename="database.ini", section="postgresql"):
    # create a parser
    parser = ConfigParser()
    # read the config file
    parser.read(filename)
    # create a dict
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} is not found in the {filename} file.')
    return db

dbconfig()