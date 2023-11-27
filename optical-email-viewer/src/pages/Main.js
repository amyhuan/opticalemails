import { useEffect, useState } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL

const Main = () => {
    const [summaries, setSummaries] = useState([])
    const [ids, setIds] = useState([])
    const [emailInfo, setEmailInfo] = useState([])

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

    // get summaries
    useEffect(() => {
        const getSummaries = async () => {
            const response = await axios.get(`${API_BASE}/emailsummaries?ids=${ids.join(",")}`, {
                headers: {
                    "Content-Type": "application/json",
                }
            });
            const newSummaries = response.data
            if (newSummaries) {
                setSummaries(newSummaries)
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
                        <th style={{ border: '1px solid #ddd', padding: '10px' }}>Subject</th>
                        <th style={{ border: '1px solid #ddd', padding: '10px' }}>Circuit IDs Affected</th>
                    </tr>
                </thead>
                <tbody>
                    {ids.map((id, index) => (
                        <tr key={index}>
                            <td style={{ border: '1px solid #ddd', padding: '10px' }}>
                                {emailInfo[id]["TimeReceived"]}
                            </td>
                            <td style={{ border: '1px solid #ddd', padding: '10px' }}>
                                {emailInfo[id]["From"]}
                            </td>
                            <td style={{ border: '1px solid #ddd', padding: '10px' }}>
                                {emailInfo[id]["Subject"]}
                            </td>
                            <td style={{ border: '1px solid #ddd', padding: '10px' }}>
                                {summaries[index]}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}

export default Main