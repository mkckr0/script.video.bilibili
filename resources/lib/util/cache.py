import glob
import os
import pickle
import typing
from .const import ADDON_PROFILE

CACHE_PATH = os.path.join(ADDON_PROFILE, "cache")

def set_state(name: str, value: typing.Any):
    path = os.path.join(CACHE_PATH, name + ".pickle")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as ofile:
        pickle.dump(value, ofile, protocol=pickle.HIGHEST_PROTOCOL)


T = typing.TypeVar("T")


def get_state(name: str, cls: typing.Type[T]) -> T:
    path = os.path.join(CACHE_PATH, name + ".pickle")
    if not os.path.exists(path):
        return cls()
    with open(path, "rb") as ifile:
        return pickle.load(ifile)

def clear_cache(wildcard: str):
    for file in glob.glob(os.path.join(CACHE_PATH, wildcard)):
        os.remove(file)