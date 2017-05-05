from actions import *

ZIPCODE_INTENT = 'zipcode'
TIMESLOT_INTENT = 'timeslot'
DETAIL_DONE_INTENT = 'detail_done'

intents = {
'Default Fallback Intent':fallback_action,
'Fallback':fallback_action,
'Hi':begin_action
}
