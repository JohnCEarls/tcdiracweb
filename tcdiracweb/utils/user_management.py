import boto.dynamodb
from boto.dynamodb2.table import Table
import boto.dynamodb2.exceptions
import hashlib

def hash_id( id ):
    m = hashlib.md5()
    m.update( id )
    m.update("The rain in spain falls mainly in the plain")
    return m.hexdigest()

def get_user_table():
    return Table('adversary_user')

def get_user( user_id ):
    table = get_user_table()
    user = table.get_item( user_id = user_id )
    if user.keys():
        return user
    else:
        return None

def user_registered( user_id ):
    user = get_user( user_id )
    if user:
        return True
    else:
        return False

def user_active( user_id):
    user = get_user( user_id )
    if user and user['active'] == 1:
        return True
    else:
        return False

def add_user( user_id, user_name, user_email):
    table = get_user_table( )
    data = { 'user_id': user_id, 'user_name': user_name, 'user_email': user_email, 'active': 0 }
    try:
        res = table.put_item( data )
    except boto.dynamodb2.exceptions.ConditionalCheckFailedException as e:
        #already exists
        res = False
    return res

def active_users():
    users = get_user_table()
    return users.scan( active__eq = 1 )

def inactive_users():
    users = get_user_table()
    return users.scan( active__eq = 0 )

def all_users():
    users = get_user_table()
    return users.scan( )

def activate_user( user_id ):
    if user_registered( user_id ):
        user = get_user( user_id )
        user['active'] = 1
        user.save()
        return True
    else:
        return False


if __name__ == "__main__":
    import random
    new_user_id = 'test%i' % random.randint(100000,999999)
    assert get_user( new_user_id ) is None, "%s is in db and shouldn't be" % new_user_id
    assert user_registered( new_user_id ) == False, "%s is in registered and shouldn't be" % new_user_id
    assert user_active( new_user_id ) == False, "%s is in active and shouldn't be" % new_user_id
    assert add_user( new_user_id, 'test_uname', 'test@test.com') == True, "%s was not added"  % new_user_id

    assert get_user( new_user_id ) is not None, "%s is not in db and should be" % new_user_id
    assert user_registered( new_user_id ), "%s is not  registered and should be" % new_user_id
    assert user_active( new_user_id ) == False, "%s is in active and shouldn't be" % new_user_id
    assert activate_user( new_user_id ),  "%s was not activated"  % new_user_id
    
    assert user_active( new_user_id ),  "%s was not activated"  % new_user_id
    assert add_user( new_user_id, "Test", "Test" ) == False, "%s inserted twice" %  new_user_id
    print "Active Users"
    print "============"
    for user in active_users():
        for k,b in user.items():
            print '\t', k, " : ", b
    print "Inactive Users"
    print "============"
    for user in inactive_users():
        for k,b in user.items():
            print '\t', k, " : ", b

    print "All Users"
    print "============"
    for user in all_users():
        for k,b in user.items():
            print '\t', k, " : ", b


