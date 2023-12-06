import { useEffect, useState } from 'react';
import axios from 'axios';
import "../styling/Main.css"

const API_BASE = process.env.REACT_APP_API_URL
const CIRCUIT_INFO_API_URL = process.env.REACT_APP_CIRCUIT_INFO_API_URL

function Main() {
    const [ids, setIds] = useState([])
    const [emailInfo, setEmailInfo] = useState([])
    const [mainInfo, setMainInfo] = useState([])

    const [showCircuitIdInfo, setShowCircuitIdInfo] = useState(false)
    const [selectedCircuit, setSelectedCircuit] = useState()
    const [idsPerEmail, setIdsPerEmail] = useState({})
    const [idInfo, setIdInfo] = useState({})

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
            const idInfo = {}
            const idsPerEmail = []
            if (newSummaries) {
                const info = []
                for (let su of newSummaries) {
                    const parsedSummary = parseResultString(su)
                    info.push(parsedSummary)

                    const ids = parsedSummary["CircuitIds"].split("\n")
                    console.log(ids)
                    idsPerEmail.push(ids)
                    ids.forEach(async id => {
                        idInfo[id] = await getIdInfo(id)
                    })
                }
                setMainInfo(info)
                setIdsPerEmail(idsPerEmail)
                setIdInfo(idInfo)
            }
        }
        getSummaries()
    }, [ids]);

    const getIdInfo = async (id) => {
        try {
            const res = await axios.get(process.env.REACT_APP_CIRCUIT_INFO_API_URL, {
                params: {
                    vendor_circuit_id: id,
                    code: process.env.REACT_APP_CIRCUIT_INFO_API_KEY
                }
            },
                {
                    headers: {
                        'Content-Type': 'application/json',
                    }
                }
            )
            return res
        } catch(e) {
            console.log(e)
            return null
        }
    }

    // getIdInfo = () => {
    //     const idInfo = {}
    //     const idsPerEmail = []
    //     mainInfo.forEach(info => {
    //         try {
    //             const ids = info["CircuitIds"].split(",")
    //             console.log(ids)
    //             idsPerEmail.push(ids)
    //             ids.forEach(id => {
    //                 idInfo[id] = getIdInfo(id)
    //             })
    //             console.log(idInfo)
    //         } catch (e) {
    //         }
    //     })
    //     setIdsPerEmail(idsPerEmail)
    //     setIdInfo(idInfo)
    // }

    // useEffect(() => {
    //     const idInfo = {}
    //     const idsPerEmail = []
    //     mainInfo.forEach(info => {
    //         try {
    //             const ids = info["CircuitIds"].split("\n")
    //             console.log(ids)
    //             idsPerEmail.push(ids)
    //             ids.forEach(id => {
    //                 idInfo[id] = getIdInfo(id)
    //             })
    //             console.log(idInfo)
    //         } catch (e) {
    //         }
    //     })
    //     setIdsPerEmail(idsPerEmail)
    //     setIdInfo(idInfo)
    // }, [mainInfo]);

    const getIdLinks = (index) => {
        console.log(idsPerEmail);
        console.log(idInfo);
    
        if (!idsPerEmail) {
            return <></>;
        }
    
        return (
            <>
                {idsPerEmail[index].map(id => (
                    <a key={id} onClick={() => {
                        setSelectedCircuit(id);
                        setShowCircuitIdInfo(true);
                    }}>
                        {id}
                    </a>
                ))}
            </>
        );
    }
    

    return (
        <div>
            {showCircuitIdInfo && (
                <div className="modal">
                    <div className="modal-content">
                        {JSON.stringify(idInfo[selectedCircuit])}
                    </div>
                </div>
            )}

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
                                {getIdLinks(index)}
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