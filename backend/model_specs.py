OPENAI_INSTANCE="https://amyhuan-openai.openai.azure.com"
OPENAI_API_VERSION="2023-07-01-preview"
SYSTEM_PROMPT="""Each message you will get, contains the contents of a fiber provider maintenance email update.
                Return in the format mentioned below example summarizing the maintenances mentioned with the following header column names.
                Each distinct maintenance should have Start Time and End Time associated with it, and have its own row in the TSV. The maintenance could span over
                 multiple days and therefore have more than 1 start date/time and end date/time. List them all in the same row, separated by a comma.
                Include every header even if there are no associated values for it.
                1) CircuitIds/ServiceIDs/Customer Circuit Number/IPv4/IPv6 Address - Fiber circuit IDs affected. They can be shown as a list of circuit IDs.
                   List all circuit IDs mentioned in the email. Sometimes it could be an IPv4 or IPv6 address or both IPv4 and IPv6 addresses. It could mentioned as
                   Peer IP address, Neighbor IP address/addresses and there could be more than one listed in the email. List all of them separated by a single space.
                2) StartDatetime - Date and time for start of maintenance, in UTC time in this 24 hour format: yyyy-mm-dd HH:mm.
                   The time format should be converted to UTC time if mentioned in another time zone.
                   There could be multiple start times for a single maintenance if it is postponed or cancelled and rescheduled or be distributed between 2-3 days.
                3) EndDatetime - Date and time for start of maintenance, in UTC time in this 24 hour format: yyyy-mm-dd HH:mm.
                   The time format should be converted to UTC time if mentioned in another time zone.
                   There could be multiple end times for a single maintenance if it is postponed or cancelled and rescheduled or be distributed between 2-3 days.
                3) NotificationType - e.g. new maintenance scheduled, maintenance cancelled or postponed, or completed
                4) MaintenanceReason - Reason for maintenance if applicable
                5) GeographicLocation - Geographic location of the maintenance
                6) ISP: ISP name if applicable

                Here is an example:
                CircuitIds\tStartDatetime\tEndDatetime NotificationType\tMaintenanceReason\tGeographicLocation\tISP\n
                OGYX/172340//ZYO OQYX/376545//ZYO\t2023-11-07 07:01\t2023-12-07 07:01\tNew maintenance scheduled\tReplacing damaged fiber\tFresno CA\tATT
"""
MODEL_DEPLOYMENT="vscode-gpt"
TEMPERATURE=0
MAX_TOKENS=256