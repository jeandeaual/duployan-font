# MIT License
#
# Copyright (c) 2017 Just van Rossum
# Copyright (c) 2020 Google LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import fontTools.ttLib.tables.otTables

def fixLookupOverFlows(ttf, overflowRecord):
    ok = 0
    lookup_index = overflowRecord.LookupListIndex
    if overflowRecord.SubTableIndex is None:
        lookup_index = lookup_index - 1
    if lookup_index < 0:
        return ok
    if overflowRecord.tableType == 'GSUB':
        ext_type = 7
    elif overflowRecord.tableType == 'GPOS':
        ext_type = 9
    lookups = ttf[overflowRecord.tableType].table.LookupList.Lookup
    for lookup_index in range(lookup_index, -1, -1):
        lookup = lookups[lookup_index]
        if lookup.SubTable[0].__class__.LookupType != ext_type:
            lookup.LookupType = ext_type
            for si in range(len(lookup.SubTable)):
                subtable = lookup.SubTable[si]
                ext_subtable_class = fontTools.ttLib.tables.otTables.lookupTypes[overflowRecord.tableType][ext_type]
                ext_subtable = ext_subtable_class()
                ext_subtable.Format = 1
                ext_subtable.ExtSubTable = subtable
                lookup.SubTable[si] = ext_subtable
            ok = 1
    return ok

def getDataLength(self):
    return sum(map(len, self.items))

def CountReference_len(self):
    return self.size

def OTTableWriter_len(self):
    return 4 if self.longOffset else 2

