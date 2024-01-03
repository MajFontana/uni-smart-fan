AUTH_MODIFY_STATUS = 0
AUTH_MODIFY_CONFIG = 1
AUTH_READ_STATUS = 2
AUTH_READ_CONFIG = 3

def getAuthorization(key):
    if key == "abcd":
        return set([AUTH_MODIFY_STATUS, AUTH_READ_CONFIG])
    elif key == "efgh":
        return set([AUTH_READ_STATUS, AUTH_READ_CONFIG, AUTH_MODIFY_CONFIG])
    else:
        return set([])
