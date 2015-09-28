import sys
sys.path.insert(0, 'src')

import docProcessor as dp
import utils as util
import settings as ENV
import datetime

startTime = datetime.datetime.now()

dp.extractDocuments()


endTime = datetime.datetime.now()
timeSpent = endTime - startTime
print "PROGRAM COMPLETED IN " + str(timeSpent.seconds) + " SECONDS\n\n\n--------------------------\n\n\n"