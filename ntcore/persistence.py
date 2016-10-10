'''
    This tries to stay compatible with ntcore's persistence mechanism,
    but if you go outside the realm of normal operations it may differ.
'''

import ast
import binascii
import base64
import re

try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser

from .constants import *
from .value import Value

import logging
logger = logging.getLogger('nt')


PERSISTENT_SECTION = '[NetworkTables Storage 3.0]'

_key_bool = re.compile('boolean "(.+)"')
_key_double = re.compile('double "(.+)"')
_key_string = re.compile('string "(.+)"')
_key_raw = re.compile('raw "(.+)"')
_key_bool_array = re.compile('array boolean "(.+)"')
_key_double_array = re.compile('array double "(.+)"')
_key_string_array = re.compile('array string "(.+)"')

_value_string = re.compile(r'"((?:\\.|[^"\\])*)",?')

# TODO: these escape functions almost certainly don't deal with unicode
#       correctly

# TODO: strictly speaking, this isn't 100% compatible with ntcore... but

def _unescape_string(s):
    # shortcut if no escapes present
    if '\\' not in s:
        return s
    
    # let python do the hard work
    return ast.literal_eval('"%s"' % s)

# This is mostly what we want... unicode strings won't work properly though
_table = {i: chr(i) if i >= 32 and i < 127 else '\\x%02x' % i for i in range(256)}
_table[ord('"')] = '\\"'
_table[ord('\\')] = '\\\\'
_table[ord('\n')] = '\\n'
_table[ord('\t')] = '\\t'
_table[ord('\r')] = '\\r'

def _escape_string(s):
    return s.translate(_table)

def load_entries(fp):
    
    entries = []
    
    parser = RawConfigParser()
    
    try:
        parser.read(fp)
    except Exception as e:
        return 'Error reading persistent file: %s' % e
    
    try:
        cfg = parser[PERSISTENT_SECTION]
    except KeyError:
        return "Persistent section not found"

    value = None
    m = None

    for k, v in cfg.items():
        
        # Reduces code duplication
        if value:
            entries.append((_unescape_string(m.group(1)), value))
            
        value = None
        
        m = _key_bool.match(k)
        if m:
            if v == 'true':
                value = Value.makeBoolean(True)
            elif v == 'false':
                value = Value.makeBoolean(False)
            else:
                logger.warn("Unrecognized boolean value for %s", m.group(1))
            continue
        
        m = _key_double.match(k)
        if m:
            try:
                value = Value.makeDouble(float(v))
            except ValueError as e:
                logger.warn("Unrecognized double value for %s", m.group(1))
                
            continue
        
        m = _key_string.match(k)
        if m:
            value = Value.makeString(_unescape_string(v))
            continue
        
        m = _key_raw.match(k)
        if m:
            try:
                value = Value.makeRaw(base64.b64decode(v, validate=True))
            except binascii.Error:
                logger.warn("Unrecognized raw value for %s", m.group(1))
            continue
        
        m = _key_bool_array.match(k)
        if m:
            bools = []
            for vv in v.split(','):
                vv = vv.strip()
                if vv == 'true':
                    bools.append(True)
                elif vv == 'false':
                    bools.append(False)
                else:
                    logger.warn("Unrecognized bool '%s' in bool array %s'", vv, m.group(1))
                    bools = None
                    break
                
            if bools is not None:
                value = Value.makeBooleanArray(bools)    
            continue
        
        m = _key_double_array.match(k)
        if m:
            doubles = []
            for vv in v.split(','):
                try:
                    doubles.append(float(vv))
                except ValueError:
                    logger.warn("Unrecognized double '%s' in double array %s", vv, m.group(1))
                    doubles = None
                    break
                
            value = Value.makeDoubleArray(doubles)    
            continue
        
        m = _key_string_array.match(k)
        if m:
            # Technically, this will let invalid inputs in... but,
            # I don't really care. Feel free to fix it if you do.
            strings = [_unescape_string(vv) for vv in _value_string.findall(v)]
            value = Value.makeStringArray(strings)
            continue


def save_entries(fp, entries):
    
    parser = RawConfigParser()
    parser.add_section(PERSISTENT_SECTION)

    cfg = parser[PERSISTENT_SECTION]
    
    for name, value in entries:
        if not value:
            continue
        
        t = value.type()
        
        if t == NT_BOOLEAN:
            name = 'boolean "%s"' % _escape_string(name)
            vrepr = 'true' if value.getboolean() else 'false'
        elif t == NT_DOUBLE:
            name = 'double "%s"' % _escape_string(name)
            vrepr = str(value.getDouble())
        elif t == NT_STRING:
            name = 'string "%s"' % _escape_string(name)
            vrepr = '"%s"' % _escape_string(value.getString())
        elif t == NT_RAW:
            name = 'raw "%s"' % _escape_string(name)
            vrepr = base64.b64encode(value.getRaw())
        elif t == NT_BOOLEAN_ARRAY:
            name = 'array boolean "%s"' % _escape_string(name)
            vrepr = ','.join(['true' if v else 'false' for v in value.getBooleanArray()])
        elif t == NT_DOUBLE_ARRAY:
            name = 'double "%s"' % _escape_string(name)
            vrepr = ','.join([str(v) for v in value.getDoubleArray()])
        elif t == NT_STRING_ARRAY:
            name = 'string "%s"' % _escape_string(name)
            vrepr = '","'.join([_escape_string(v) for v in value.getStringArray()])
            if vrepr:
                vrepr = '"%s"' % vrepr
        else:
            continue
        
        cfg[name] = vrepr
    
    parser.write(fp, space_around_delimiters=False)    
