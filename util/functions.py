# util.py
from enum import Enum
from copy import deepcopy


class SearchDict(dict):
    def search(self, key):
        """
        Recursively search for a key in the dictionary and its nested dictionaries.
        """
        if key in self:
            return self[key]
        for value in self.values():
            if isinstance(value, dict):
                result = SearchDict(value).search(key)
                if result is not None:
                    return result
        return None

    def reverse_search(self, value):
        """
        Recursively search for a value in the dictionary and its nested dictionaries.
        """
        for k, v in self.items():
            if v == value:
                return k
            if isinstance(v, dict):
                result = SearchDict(v).reverse_search(value)
                if result is not None:
                    return result
        return None


def copy_enum(enum: Enum, to_name: str):
    if to_name not in copy_enum._dict:
        copy_enum._dict[to_name] = 0
    else:
        copy_enum._dict[to_name] += 1
        to_name = f"{to_name}{copy_enum._dict[to_name]}"

    enum = Enum(to_name, {member.name: deepcopy(member.value) for member in enum})
    return enum


copy_enum._dict = {}
