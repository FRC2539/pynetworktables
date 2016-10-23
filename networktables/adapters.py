


class NetworkTableGlobalListenerAdapter:

    def __init__(self, listener):
        self.listener = listener
        assert callable(self.listener)

    def valueChanged(self, source, key, value, isNew):
        self.listener(key, value, isNew)

class NetworkTableKeyListenerAdapter:
    """An adapter that is used to filter value change notifications for a
    specific key
    """

    def __init__(self, relativeKey, fullKey, targetSource, targetListener):
        """Create a new adapter
        
        :param relativeKey: the name of the key relative to the table (this
                            is what the listener will receiver as the key)
        :param fullKey: the full name of the key in the NetworkTableNode
        :param targetSource: the source that events passed to the target
                             listener will appear to come from
        :param targetListener: the callable where events are forwarded to
        """
        assert callable(targetListener)
        self.relativeKey = relativeKey
        self.fullKey = fullKey
        self.targetSource = targetSource
        self.targetListener = targetListener

    def valueChanged(self, source, key, value, isNew):
        if key == self.fullKey:
            self.targetListener(self.targetSource,
                                self.relativeKey, value, isNew)

class NetworkTableListenerAdapter:
    """An adapter that is used to filter value change notifications and make
    the path relative to the NetworkTable
    """

    def __init__(self, prefix, targetSource, targetListener):
        """Create a new adapter
        
        :param prefix: the prefix that will be filtered/removed from the
                       beginning of the key
        :param targetSource: the source that events passed to the target
                             listener will appear to come from
        :param targetListener: the callable where events are forwarded to
        """
        assert callable(targetListener)
        self.prefix = prefix
        self.targetSource = targetSource
        self.targetListener = targetListener

    def valueChanged(self, source, key, value, isNew):
        #TODO use string cache
        if key.startswith(self.prefix):
            relativeKey = key[len(self.prefix):]
            if NetworkTable.PATH_SEPARATOR in relativeKey:
                return
            self.targetListener(self.targetSource, relativeKey,
                                value, isNew)

class NetworkTableSubListenerAdapter:
    """An adapter that is used to filter sub table change notifications and
    make the path relative to the NetworkTable
    """

    def __init__(self, prefix, targetSource, targetListener):
        """Create a new adapter
        
        :param prefix: the prefix of the current table
        :param targetSource: the source that events passed to the target
                             listener will appear to come from
        :param targetListener: the callable where events are forwarded to
        """
        assert callable(targetListener)
        self.prefix = prefix
        self.targetSource = targetSource
        self.targetListener = targetListener
        self.notifiedTables = set()

    def valueChanged(self, source, key, value, isNew):
        #TODO use string cache
        if not key.startswith(self.prefix):
            return

        key = key[len(self.prefix):]

        if key.startswith(NetworkTable.PATH_SEPARATOR):
            key = key[len(NetworkTable.PATH_SEPARATOR):]

        #TODO implement sub table listening better
        keysplit = key.split(NetworkTable.PATH_SEPARATOR)
        if len(keysplit) < 2:
            return

        subTableKey = keysplit[0]

        if subTableKey in self.notifiedTables:
            return

        self.notifiedTables.add(subTableKey)
        self.targetListener(self.targetSource, subTableKey,
                self.targetSource.getSubTable(subTableKey), True)