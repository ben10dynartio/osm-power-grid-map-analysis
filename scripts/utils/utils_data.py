import ast
import math

def convert_int(value, default=0, error=-1):
    if type(value) is int:
        return value
    if type(value) is float:
        if math.isnan(value):
            return default
        return int(value)
    if value is None:
        return default
    if value == "":
        return default
    if value.isdigit():
        return int(value)
    return error

def convert_dict(value):
    if value is None :
        return {}
    elif type(value) is str:
        return ast.literal_eval(value)
    elif type(value) is dict:
        return value
    else:
        raise ValueError(f"Unknown value type : {value}")