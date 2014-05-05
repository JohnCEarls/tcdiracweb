def json_prep( dct ):
    """
    Prepares a dictionary to be jsonized
    """
    for k,v in dct.iteritems():
        try:
            #convert datetime to string
            dct[k] = v.isoformat()
        except AttributeError as ae:
            pass
            if type(v) == set:
                dct[k] = list(v)
    return dct
