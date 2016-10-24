
#
# Useful fixtures
#

import logging
logging.basicConfig(level=logging.DEBUG)

import pytest

from networktables import NetworkTables

@pytest.fixture(scope='function')
def nt():
    NetworkTables.setTestMode()
    NetworkTables.initialize()
    
    yield NetworkTables
    
    NetworkTables.shutdown()

