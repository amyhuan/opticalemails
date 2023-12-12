import { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import "../styling/Main.css"
import ResponseTable from './ResponseTable';


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

    const modalContentRef = useRef(null)

    const closeModal = (e) => {
        // Close the modal if the click is outside of the modal content
        if (!modalContentRef.current.contains(e.target)) {
            setShowCircuitIdInfo(false);
        }
    }

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
            if (res) {
                return res.data
            }
        } catch (e) {
            console.log(e)
            return null
        }
        return null
    }

    const getIdLinks = (index) => {
        console.log(idsPerEmail);
        console.log(idInfo);

        if (!idsPerEmail) {
            return <></>;
        }

        idsPerEmail[index].forEach(id => {
            console.log(id, idInfo[id])
            if (idInfo[id]) {
                console.log(idInfo[id].circuit_details.device_records_exist)
            }
        })

        return (
            <>
                {idsPerEmail[index].map(id => (
                    <a key={id}
                        className={idInfo[id] && (idInfo[id].circuit_details.device_records_exist || idInfo[id].device_records_exist) ? "link" : "invalid-id"}
                        onClick={() => {
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
                <div className="modal" onClick={closeModal}>
                    <div className="modal-content" ref={modalContentRef}>
                            <ResponseTable
                                response={idInfo[selectedCircuit]}
                            />
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