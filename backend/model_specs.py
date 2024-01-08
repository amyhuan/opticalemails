OPENAI_INSTANCE="https://amyhuan-openai.openai.azure.com"
OPENAI_API_VERSION="2023-07-01-preview"
SYSTEM_PROMPT="""Each message you will get contains the contents of a fiber provider maintenance email update. 
                Return a TSV summarizing the maintenances mentioned with the following header column names. Each distinct maintenance should have exactly
                one start time and end time, and have its own row in the TSV. Include every header even if there are no associated values for it.
                1) CircuitIds - Fiber circuit IDs affected. Separate multiple IDs with newlines.
                2) StartDatetime - Date and time for start of maintenance, in UTC time in this 24 hour format: yyyy-mm-dd HH:mm 
                3) EndDatetime - Date and time for start of maintenance, in UTC time in this 24 hour format: yyyy-mm-dd HH:mm 
                3) NotificationType - e.g. new maintenance scheduled, maintenance cancelled or postponed, or completed
                4) MaintenanceReason - Reason for maintenance if applicable
                5) GeographicLocation - Geographic location of the maintenance
                6) VsoId - If applicable, the Microsoft VSO ID that this maintenance is associated with
                
                Here is an example:
                CircuitIds\tStartDatetime\tEndDatetime NotificationType\tMaintenanceReason\tGeographicLocation\tVsoId\n
                OGYX/172340//ZYO,OQYX/376545//ZYO\t2023-11-07 07:01\t2023-12-07 07:01\tNew maintenance scheduled\tReplacing damaged fiber\tFresno CA\t15438446
                """
MODEL_DEPLOYMENT="vscode-gpt"
TEMPERATURE=0
MAX_TOKENS=256