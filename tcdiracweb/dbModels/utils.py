def item_to_dict( item ):
    our_dict = {}
    for k,v in a.iteritems():
        if type(v) is set:
            our_dict[k] = list(type(v))
        else:
            our_dict[k] = v
    return our_dict
