
#
# These tests are leftover from the original pynetworktables tests
#

import pytest
import threading


try:
    from unittest.mock import call, Mock
except ImportError:
    from mock import call, Mock

@pytest.fixture(scope='function')
def table1(nt):
    return nt.getTable('/test1')
    
@pytest.fixture(scope='function')
def table2(nt):
    return nt.getTable('/test2')

@pytest.fixture(scope='function')
def table3(nt):
    return nt.getTable('/test3')

@pytest.fixture(scope='function')
def subtable1(nt):
    return nt.getTable('/test2/sub1')
    
@pytest.fixture(scope='function')
def subtable2(nt):
    return nt.getTable('/test2/sub2')

@pytest.fixture(scope='function')
def subtable3(nt):
    return nt.getTable('/test3/suba')
    
@pytest.fixture(scope='function')
def subtable4(nt):
    return nt.getTable('/test3/suba/subb')

@pytest.fixture(scope='function')
def notifier(nt):
    return nt._api.notifier

@pytest.fixture(scope='function')
def nt_flush(notifier):
    # this reaches deep into the API to flush the notifier
    
    # replace the queue function
    tcond = threading.Condition()
    qcond = threading.Condition()
    
    q = notifier.m_notifications
    _get = q.get
    
    def get():
        # notify the waiter
        while True:
            print("get?")
            if not q.empty():
                print("get")
                ret = _get()
                print ("->", ret)
                return ret
            
            with qcond:
                print("qnotify")
                qcond.notify()
        
            with tcond:
                print("twait")
                tcond.wait()
    
    q.get = get
    
    def flush():
        with qcond:
            with tcond:
                print("tnotify")
                tcond.notify()
            print("qwait")
            if not qcond.wait(1):
                raise Exception("flush failed")
    
    yield flush
    
    # free the queue function
    q.get = _get
    
    

def test_key_listener_immediate_notify(table1, notifier, nt_flush):
    
    listener1 = Mock()
    
    table1.putBoolean("MyKey1", True)
    table1.putBoolean("MyKey1", False)
    table1.putBoolean("MyKey2", True)
    table1.putBoolean("MyKey4", False)
    
    assert not notifier.m_active
    
    table1.addTableListener(listener1.valueChanged, True, localNotify=True)
    
    nt_flush()
    listener1.valueChanged.assert_has_calls([
        call(table1, "MyKey1", False, True),
        call(table1, "MyKey2", True, True),
        call(table1, "MyKey4", False, True),
    ], True)
    assert len(listener1.mock_calls) == 3
    listener1.reset_mock()
    
    table1.putBoolean("MyKey", False)
    nt_flush()
    listener1.valueChanged.assert_called_once_with(table1, "MyKey", False, True)
    assert len(listener1.mock_calls) == 1
    listener1.reset_mock()
    
    table1.putBoolean("MyKey1", True)
    nt_flush()
    listener1.valueChanged.assert_called_once_with(table1, "MyKey1", True, False)
    assert len(listener1.mock_calls) == 1
    listener1.reset_mock()
    
    table1.putBoolean("MyKey1", False)
    nt_flush()
    listener1.valueChanged.assert_called_once_with(table1, "MyKey1", False, False)
    assert len(listener1.mock_calls) == 1
    listener1.reset_mock()
    
    table1.putBoolean("MyKey4", True)
    nt_flush()
    listener1.valueChanged.assert_called_once_with(table1, "MyKey4", True, False)
    assert len(listener1.mock_calls) == 1
    listener1.reset_mock()
    
def test_key_listener_not_immediate_notify(table1, nt_flush):
    
    listener1 = Mock()
    
    table1.putBoolean("MyKey1", True)
    table1.putBoolean("MyKey1", False)
    table1.putBoolean("MyKey2", True)
    table1.putBoolean("MyKey4", False)
    
    table1.addTableListener(listener1.valueChanged, False, localNotify=True)
    assert len(listener1.mock_calls) == 0
    listener1.reset_mock()
    
    table1.putBoolean("MyKey", False)
    nt_flush()
    listener1.valueChanged.assert_called_once_with(table1, "MyKey", False, True)
    assert len(listener1.mock_calls) == 1
    listener1.reset_mock()
    
    table1.putBoolean("MyKey1", True)
    nt_flush()
    listener1.valueChanged.assert_called_once_with(table1, "MyKey1", True, False)
    assert len(listener1.mock_calls) == 1
    listener1.reset_mock()
    
    table1.putBoolean("MyKey1", False)
    nt_flush()
    listener1.valueChanged.assert_called_once_with(table1, "MyKey1", False, False)
    assert len(listener1.mock_calls) == 1
    listener1.reset_mock()
    
    table1.putBoolean("MyKey4", True)
    nt_flush()
    listener1.valueChanged.assert_called_once_with(table1, "MyKey4", True, False)
    assert len(listener1.mock_calls) == 1
    listener1.reset_mock()
    
def test_specific_key_listener(table1, nt_flush):
    
    listener1 = Mock()
    
    table1.addTableListener(listener1.valueChanged, False, key='MyKey1', localNotify=True)
    
    table1.putBoolean('MyKey1', True)
    nt_flush()
    listener1.valueChanged.assert_called_once_with(table1, "MyKey1", True, True)
    assert len(listener1.mock_calls) == 1
    listener1.reset_mock()
    
    table1.putBoolean('MyKey2', True)
    nt_flush()
    assert len(listener1.mock_calls) == 0
    
    
    
def test_subtable_listener(table2, subtable1, subtable2, nt_flush):
    
    listener1 = Mock()
    
    table2.putBoolean("MyKey1", True)
    table2.putBoolean("MyKey1", False)
    table2.addSubTableListener(listener1.valueChanged, localNotify=True)
    table2.putBoolean("MyKey2", True)
    table2.putBoolean("MyKey4", False)

    subtable1.putBoolean("MyKey1", False)
    
    nt_flush()
    listener1.valueChanged.assert_called_once_with(table2, "sub1", subtable1, True)
    assert len(listener1.mock_calls) == 1
    listener1.reset_mock()
    
    subtable1.putBoolean("MyKey2", True)
    subtable1.putBoolean("MyKey1", True)
    subtable2.putBoolean('MyKey1', False)
    
    nt_flush()
    listener1.valueChanged.assert_called_once_with(table2, "sub2", subtable2, True)
    assert len(listener1.mock_calls) == 1
    listener1.reset_mock()
    
    
def test_subsubtable_listener(table3, subtable3, subtable4, nt_flush):
    listener1 = Mock()
    
    table3.addSubTableListener(listener1.valueChanged, localNotify=True)
    subtable3.addSubTableListener(listener1.valueChanged, localNotify=True)
    subtable4.addTableListener(listener1.valueChanged, True, localNotify=True)
    
    subtable4.putBoolean('MyKey1', False)
    
    nt_flush()
    listener1.valueChanged.assert_has_calls([
        call(table3, 'suba', subtable3, True),
        call(subtable3, 'subb', subtable4, True),
        call(subtable4, 'MyKey1', False, True)
    ], True)
    assert len(listener1.mock_calls) == 3
    listener1.reset_mock()
    
    subtable4.putBoolean('MyKey1', True)
    
    nt_flush()
    listener1.valueChanged.assert_called_once_with(subtable4, 'MyKey1', True, False)
    assert len(listener1.mock_calls) == 1
    listener1.reset_mock()
    
    listener2 = Mock()
    
    table3.addSubTableListener(listener2.valueChanged, localNotify=True)
    subtable3.addSubTableListener(listener2.valueChanged, localNotify=True)
    subtable4.addTableListener(listener2.valueChanged, True, localNotify=True)
    
    nt_flush()
    listener2.valueChanged.assert_has_calls([
        call(table3, 'suba', subtable3, True),
        call(subtable3, 'subb', subtable4, True),
        call(subtable4, 'MyKey1', True, True)
    ], True)
    assert len(listener1.mock_calls) == 0
    assert len(listener2.mock_calls) == 3
    listener2.reset_mock()
    