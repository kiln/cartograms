import os
import re

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.pardir))

def _normalise(country_name):
  s = country_name.upper()
  if s == "AND": return s
  return re.sub(r'[^A-Z]|\bAND\b|\bTHE\b', '', s)

# Read in the list of country codes
class CountryNameEncoder(object):
    def __init__(self):
        alpha_2_by_name = {}
        alpha_3_by_name = {}
        for line in open(os.path.join(BASE_DIR, "data/iso-country-codes.ssv"), 'r'):
            split_line = line.strip().split(";")
            alpha_2 = split_line[0]
            alpha_3 = split_line[1]
            names = split_line[1:]
            for name in names:
                norm = _normalise(name)
                if norm in alpha_2_by_name:
                    raise Exception("Normalised name '%s' already seen" % (norm))
                if norm:
                    alpha_2_by_name[norm] = alpha_2
                    alpha_3_by_name[norm] = alpha_3
        
        self.alpha_2_by_name = alpha_2_by_name
        self.alpha_3_by_name = alpha_3_by_name
    
    def alpha_2(self, country_name):
        return self.alpha_2_by_name.get(_normalise(country_name))
    
    def alpha_3(self, country_name):
        return self.alpha_3_by_name.get(_normalise(country_name))

_encoder = CountryNameEncoder()
alpha_2 = _encoder.alpha_2
alpha_3 = _encoder.alpha_3
