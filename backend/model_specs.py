OPENAI_INSTANCE="https://auto-vso-0.openai.azure.com/"
OPENAI_API_VERSION="2023-07-01-preview"
SYSTEM_PROMPT="""Each message you will get, contains the contents of a fiber provider maintenance email update.
                Return in the format mentioned below example summarizing the maintenances mentioned with the following header column names.
                Each distinct maintenance should have Start Time and End Time associated with it, and have its own row in the TSV. The maintenance could span over
                 multiple days and therefore have more than 1 start date/time and end date/time. List them all in the same row, separated by a comma.
                Include every header even if there are no associated values for it.
                                
                1) CircuitIds - Also known as ServiceID/Customer Circuit Number/IPv4/IPv6 Address/Fiber Circuit IDs affected by the maintenance. They can be shown as a list of circuit IDs.
                   List all circuit IDs mentioned in the email. Sometimes it could be an IPv4 or IPv6 address or both IPv4 and IPv6 addresses. It could mentioned as
                   Peer IP address, Neighbor IP address/addresses and there could be more than one listed in the email and mostly mentioned after the ASN number or AS number. List all of them separated by a single space.
                   Turk telekom calls it Service ID and others call it by different names.
                2) StartDatetime - Date and time for start of maintenance, in UTC time in this 24 hour format: yyyy-mm-dd HH:mm.
                   The time format should be converted to UTC time if mentioned in another time zone.
                   There could be multiple start times for a single maintenance if it is postponed or cancelled and rescheduled or be distributed between 2-3 days.
                3) EndDatetime - Date and time for start of maintenance, in UTC time in this 24 hour format: yyyy-mm-dd HH:mm.
                   The time format should be converted to UTC time if mentioned in another time zone.
                   There could be multiple end times for a single maintenance if it is postponed or cancelled and rescheduled or be distributed between 2-3 days.
                3) NotificationType - e.g. new maintenance scheduled, maintenance rescheduled, cancelled, postponed, or completed. Could be called 'Case Status' in the email.
                   If the email appears to be about a new case about an out of service circuit that needs to be isolated and repaired, with no other updates, classify this as a New Maintenance.
                4) MaintenanceReason - Reason for maintenance if applicable
                5) GeographicLocation - Geographic location of the maintenance, or coordinates would be shared and we can convert those coordinates to location.
                6) ISP - ISP name if applicable, this information is usually available in the paragraph or can be gleaned from the email id.
                7) VsoIds - Microsoft VSO work item IDs, if they are mentioned. If not, don't include a value here

                Here is an example of the format of the TSV you should return:
                CircuitId/ServiceID/Customer Circuit Number/IPv4 Address/IPv6 Address\tStartDatetime\tEndDatetime NotificationType\tMaintenanceReason\tGeographicLocation\tISP\n
                OGYX/172340//ZYO OQYX/376545//ZYO or 104.44.15.16 2a01:111:2000:1::2221 104.44.196.42 2a01:111:2000:1::2791\t2023-11-07 07:01\t2023-12-07 07:01\tNew maintenance scheduled\tReplacing damaged fiber\tFresno CA\tATT
"""
MODEL_DEPLOYMENT="auto-vso-gpt-4-32k"
TEMPERATURE=0
MAX_TOKENS=6000