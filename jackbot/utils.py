def str_list_public(obj, padding: int = 8):
    var_name_fmt = "%%%is" % padding
    return "\n".join([
        "-%s: %s" % (var_name_fmt % n, v)
        for n, v in public_attributes(obj)
    ])


def public_attributes(obj):
    d = obj.__dict__
    return [(k, d[k]) for k in d if not str.startswith(k, "__")]
