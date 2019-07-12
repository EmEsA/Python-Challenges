def scale(strng, k, n):
    return "".join([("".join([k * c for c in part]) + "\n") * n for part in strng.split("\n")])[:-1] if strng != "" else strng