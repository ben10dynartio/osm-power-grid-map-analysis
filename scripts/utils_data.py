def convert_int(value, default=0, error=-1):
    if type(value) is int:
        return value
    if value is None:
        return default
    if value == "":
        return default
    if value.isdigit():
        return int(value)
    return error