import React, { useEffect, useState } from 'react';
import { useTable } from 'react-table';
import '../styling/ResponseTable.css';
import { format } from 'path';

const AdditonalInfoTable = ({ additionalInfo }) => {
  const [columns, setColumns] = useState([])

  useEffect(() => {
    if (data && data.length > 0) {
      const firstItem = data[0];
      console.log(firstItem)
      setColumns(Object.keys(firstItem).map(key => ({
        Header: key,
        accessor: key,
      })))
    }
  }, [additionalInfo]);

  const data = React.useMemo(() => additionalInfo || [], [additionalInfo]);

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = useTable({
    columns,
    data,
  });

  return (
    <div className="response-table">
      <table {...getTableProps()} className="table">
        <thead>
          {headerGroups.map(headerGroup => (
            <tr {...headerGroup.getHeaderGroupProps()}>
              {headerGroup.headers.map(column => (
                <th {...column.getHeaderProps()}>{column.render('Header')}</th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody {...getTableBodyProps()}>
          {rows.map(row => {
            prepareRow(row);
            return (
              <tr {...row.getRowProps()}>
                {row.cells.map(cell => {
                  return (
                    <td {...cell.getCellProps()}>{cell.render('Cell')}</td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};


const ResponseTable = ({ response }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [data, setData] = useState()
  const [dataList, setDataList] = useState([])
  const [columns, setColumns] = useState([])

  useEffect(() => {
      if (response && response.device_records_exist) {
        if (response.circuit_details) {
          setData(response.circuit_details)
        } else {
          setData(null)
        }
      } else {
        setData(null)
      }
  }, [response]);

  useEffect(() => {
    if (data) {
      console.log(data)

      const keys = Object.keys(data).map(key => ({
        Header: key,
        accessor: key,
      }))
      if ("length" in keys && data.length > 0) {
        const listKeys = Object.keys(data[0]).map(key => ({
          Header: key,
          accessor: key,
        }))
        setColumns(listKeys)
        setDataList(data)
      } else {
        setColumns(keys)
        setDataList([data])
      }
    }
    console.log([data])
  }, [data]);

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = useTable({
    columns,
    data: dataList,  // assuming 'data' is the correct prop name
  });

  const formattedResponseTable = () => {
    if (response) {
      if (response.hasOwnProperty('device_records_exist')) {
        if (!response.device_records_exist) {
          return (
            <div>No data found</div>
          )
        }
      }
      if (response.hasOwnProperty('circuit_details')) {
        if (response.circuit_details.hasOwnProperty('device_records_exist')) {
          if (!response.circuit_details.device_records_exist) {
            return (
              <div>No data found</div>
            )
          }
        }
      }
    } else {
      return (
        <div>GET request error</div>
      )
    }
    return (
      <div className="response-table">
        {response && response.source ? <h2>{"Source: " + response.source}</h2> : <></>}

        <table {...getTableProps()} className="table">
          <thead>
            {headerGroups.map(headerGroup => (
              <tr {...headerGroup.getHeaderGroupProps()}>
                {headerGroup.headers.map(column => (
                  <th {...column.getHeaderProps()}>{column.render('Header')}</th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody {...getTableBodyProps()}>
            {rows.map(row => {
              prepareRow(row);
              return (
                <tr {...row.getRowProps()}>
                  {row.cells.map(cell => {
                    return (
                      <td {...cell.getCellProps()}>{cell.render('Cell')}</td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>

        {response && response.additional_info ? <AdditonalInfoTable
          additionalInfo={response.additional_info[1]}
        /> : <></>}
      </div>
    )
  }

  const tabs = [
    {
      label: "Formatted Data",
      content: formattedResponseTable()
    },
    {
      label: "Raw Data",
      content: JSON.stringify(response)
    },
  ]

  return (
    <div className="tabs">
      <div className="tab-header">
        {tabs.map((tab, index) => (
          <button
            key={index}
            className={`tab-button ${activeTab === index ? 'active' : ''}`}
            onClick={() => setActiveTab(index)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="tab-content">{tabs[activeTab].content}</div>
    </div>
  );
};

export default ResponseTable;
