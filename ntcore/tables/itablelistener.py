#include "tables/ITableListener.h"

#include "ntcore_c.h"

void ITableListener.valueChangedEx(ITable* source, key,
                                    std.shared_ptr<nt.Value> value,
                                    unsigned int flags)
    valueChanged(source, key, value, (flags & NT_NOTIFY_NEW) != 0)

