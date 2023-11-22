import { useEffect, useState } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL

const Main = () => {
    const [summaries, setSummaries] = useState([])

    // set default time lookback
    useEffect(() => {
        const getSummaries = async () => {
            const response = await axios.get(`${API_BASE}/emailsummaries`, {
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
    }, []);

    return (
        <div style={{ display: 'flex', flexDirection: 'column-reverse' }}>
            {summaries.map((summary, index) => (
                <div key={index} style={{ border: '1px solid #ddd', margin: '10px', padding: '10px' }}>
                    {summary}
                </div>
            ))}
        </div>
    );
};

export default Main;