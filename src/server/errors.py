def getError(err):
    e = {}
    e['error'] , e['message'] = err
    return e

server_error = ('SERVER_ERROR', 'Some error occurred. Please try again.')
user_exist_error = ('USER_EXISTS_ERROR', 'User already exists. Please Log in.')
credentials_error = ('CREDENTIALS_ERROR', 'Incorrect Username or Password')
invalid_token_error = ('TOKEN_ERROR', 'Provide a valid auth token.')