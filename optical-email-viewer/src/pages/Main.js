import { useEffect, useState } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL

function Main() {
    const [ids, setIds] = useState([])
    const [emailInfo, setEmailInfo] = useState([])
    const [mainInfo, setMainInfo] = useState([])

    // get last day email metadata
    useEffect(() => {
        const getEmails = async () => {
            const response = await axios.get(`${API_BASE}/lastdayemails`, {
                headers: {
                    "Content-Type": "application/json",
                }
            });
            const newInfo = response.data
            if (newInfo) {
                setEmailInfo(newInfo)
                setIds(Object.keys(newInfo))
            }
        }
        getEmails()
    }, []);

    function parseResultString(inputString) {
        const lines = inputString.trim().split('\n');
        const result = {};

        lines.forEach(line => {
            const parts = line.split(",")
            if (parts.length > 0) {
                const header = parts[0]
                if (parts.length > 1) {
                    const val = parts.splice(1).join("\n")
                    result[header] = val
                }
            }
        });

        return result;
    }

    // full email data
    useEffect(() => {
        const getSummaries = async () => {
            const response = await axios.get(`${API_BASE}/emaildata?ids=${ids.join(",")}`, {
                headers: {
                    "Content-Type": "application/json",
                }
            });
            const newSummaries = response.data
            if (newSummaries) {
                const info = []
                for (let su of newSummaries) {
                    info.push(parseResultString(su))
                }
                setMainInfo(info)
            }
        }
        getSummaries()
    }, [ids]);

    return (
        <div>
            <div>
                <h5>
                    Optical Maintenance Emails from past 24 hours from mr@zayo.com
                </h5>
            </div>

            <table style={{ borderCollapse: 'collapse', width: '100%' }}>
                <thead>
                    <tr>
                        <th style={{ border: '1px solid #ddd', padding: '10px' }}>Time Received</th>
                        <th style={{ border: '1px solid #ddd', padding: '10px' }}>From</th>
                        <th style={{ border: '1px solid #ddd', padding: '10px' }}>Notification Type</th>
                        <th style={{ border: '1px solid #ddd', padding: '10px' }}>Maintenance Reason</th>
                        <th style={{ border: '1px solid #ddd', padding: '10px' }}>Start Date/Time</th>
                        <th style={{ border: '1px solid #ddd', padding: '10px' }}>End Date/Time</th>
                        <th style={{ border: '1px solid #ddd', padding: '10px' }}>Circuit IDs Affected</th>
                        <th style={{ border: '1px solid #ddd', padding: '10px' }}>Geographic Location</th>
                        <th style={{ border: '1px solid #ddd', padding: '10px' }}>VSO</th>
                    </tr>
                </thead>
                <tbody>
                    {mainInfo.map((id, index) => (
                        <tr key={index}>
                            <td style={{ border: '1px solid #ddd', padding: '10px' }}>
                                {emailInfo[ids[index]]["TimeReceived"]}
                            </td>
                            <td style={{ border: '1px solid #ddd', padding: '10px' }}>
                                {emailInfo[ids[index]]["From"]}
                            </td>
                            <td style={{ border: '1px solid #ddd', padding: '10px' }}>
                                {mainInfo[index]["NotificationType"]}
                            </td>
                            <td style={{ border: '1px solid #ddd', padding: '10px' }}>
                                {mainInfo[index]["MaintenanceReason"]}
                            </td>
                            <td style={{ border: '1px solid #ddd', padding: '10px' }}>
                                {mainInfo[index]["StartDatetime"]}
                            </td>
                            <td style={{ border: '1px solid #ddd', padding: '10px' }}>
                                {mainInfo[index]["EndDatetime"]}
                            </td>
                            <td style={{ border: '1px solid #ddd', padding: '10px' }}>
                                {mainInfo[index]["CircuitIds"]}
                            </td>
                            <td style={{ border: '1px solid #ddd', padding: '10px' }}>
                                {mainInfo[index]["GeographicLocation"]}
                            </td>
                            <td style={{ border: '1px solid #ddd', padding: '10px' }}>
                                {mainInfo[index]["VsoId"]}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}

export default Main