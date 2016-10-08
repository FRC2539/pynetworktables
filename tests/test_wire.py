
from io import BytesIO

import pytest

#from ntcore.message import Message
from ntcore.value import Value
from ntcore.tcpsockets.tcp_stream import ReadStream, StreamEOF
from ntcore.wire import WireCodec


@pytest.fixture(params=[
    0x0200, 0x0300
])
def round_trip(request):
    
    codec = WireCodec(request.param)
    
    def _fn(v, minver=0x0200, is_array=False):
        if codec.proto_rev < minver:
            return
        
        out = []
        fp = BytesIO()
        rstream = ReadStream(fp)
        
        codec.write_value(v, out)
        fp.write(b''.join(out))
        fp.seek(0)
        
        vtype = rstream.read(1)
        assert vtype == v.type
        
        vv = codec.read_value(vtype, rstream)
        
        with pytest.raises(StreamEOF):
            rstream.read(1)
            
        assert v == vv
    
    return _fn
    

# for each value type, test roundtrip

def test_wire_boolean(round_trip):
    round_trip(Value.makeBoolean(True))

def test_wire_double(round_trip):
    round_trip(Value.makeDouble(0.5))
    
def test_wire_string1(round_trip):
    round_trip(Value.makeString(''))
    
def test_wire_string2(round_trip):
    round_trip(Value.makeString('Hi there'))
    
def test_wire_raw1(round_trip):
    round_trip(Value.makeRaw(b''), minver=0x0300)

def test_wire_raw2(round_trip):
    round_trip(Value.makeRaw(b'\x00\xff\x78'), minver=0x0300)

def test_wire_boolArray1(round_trip):
    round_trip(Value.makeBooleanArray([]))
    
def test_wire_boolArray2(round_trip):
    round_trip(Value.makeBooleanArray([True, False]))

def test_wire_doubleArray1(round_trip):
    round_trip(Value.makeDoubleArray([]))
    
def test_wire_doubleArray2(round_trip):
    round_trip(Value.makeDoubleArray([0, 1]))
    
def test_wire_stringArray1(round_trip):
    round_trip(Value.makeStringArray([]))
    
def test_wire_stringArray2(round_trip):
    round_trip(Value.makeStringArray(["hi", "there"]))

def test_wire_rpc1(round_trip):
    round_trip(Value.makeRpc(''), minver=0x0300)
    
def test_wire_rpc2(round_trip):
    round_trip(Value.makeRpc('Hi there'), minver=0x0300)

# Try out the various message types
