import React, {forwardRef, useEffect, useState, } from 'react';

import './App.css';
import Grid from '@material-ui/core/Grid'
import MaterialTable, { Column } from "@material-table/core";
import AddBox from '@material-ui/icons/AddBox';
import ArrowDownward from '@material-ui/icons/ArrowDownward';
import Check from '@material-ui/icons/Check';
import ChevronLeft from '@material-ui/icons/ChevronLeft';
import ChevronRight from '@material-ui/icons/ChevronRight';
import Clear from '@material-ui/icons/Clear';
import DeleteOutline from '@material-ui/icons/DeleteOutline';
import Edit from '@material-ui/icons/Edit';
import FilterList from '@material-ui/icons/FilterList';
import FirstPage from '@material-ui/icons/FirstPage';
import LastPage from '@material-ui/icons/LastPage';
import Remove from '@material-ui/icons/Remove';
import SaveAlt from '@material-ui/icons/SaveAlt';
import Search from '@material-ui/icons/Search';
import ViewColumn from '@material-ui/icons/ViewColumn';
import Alert from '@material-ui/lab/Alert';
import Refresh from "@material-ui/icons/Refresh";
import VisibilityOff from '@material-ui/icons/VisibilityOff'

import axios from 'axios'
import { JsonToTable } from "react-json-to-table";


const tableIcons = {
  Add: forwardRef((props, ref) => <AddBox {...props} ref={ref} />),
  Check: forwardRef((props, ref) => <Check {...props} ref={ref} />),
  Clear: forwardRef((props, ref) => <Clear {...props} ref={ref} />),
  Delete: forwardRef((props, ref) => <DeleteOutline {...props} ref={ref} />),
  DetailPanel: forwardRef((props, ref) => <ChevronRight {...props} ref={ref} />),
  Edit: forwardRef((props, ref) => <Edit {...props} ref={ref} />),
  Export: forwardRef((props, ref) => <SaveAlt {...props} ref={ref} />),
  Filter: forwardRef((props, ref) => <FilterList {...props} ref={ref} />),
  FirstPage: forwardRef((props, ref) => <FirstPage {...props} ref={ref} />),
  LastPage: forwardRef((props, ref) => <LastPage {...props} ref={ref} />),
  NextPage: forwardRef((props, ref) => <ChevronRight {...props} ref={ref} />),
  PreviousPage: forwardRef((props, ref) => <ChevronLeft {...props} ref={ref} />),
  ResetSearch: forwardRef((props, ref) => <Clear {...props} ref={ref} />),
  Search: forwardRef((props, ref) => <Search {...props} ref={ref} />),
  SortArrow: forwardRef((props, ref) => <ArrowDownward {...props} ref={ref} />),
  ThirdStateCheck: forwardRef((props, ref) => <Remove {...props} ref={ref} />),
  ViewColumn: forwardRef((props, ref) => <ViewColumn {...props} ref={ref} />),
  Refresh: forwardRef((props, ref) => <Refresh {...props} ref={ref} />),
  VisibilityOff: forwardRef((props, ref) => <VisibilityOff {...props} ref={ref} />)

};

let api = axios.create({
    baseURL: "http://127.0.0.1:5000/api",
});
api.defaults.headers.post['Content-Type'] ='application/json';


function GetInfoTable(rowData){
    // exclude field keys
    let exclude = ['get_id', 'give_id', 'exchange_id', 'city_id', 'rate']
    // let link_field_names = ['exchange_link']
    for (let i_key in rowData['from_object']){
        // exclude all not needed data
        if (exclude.indexOf(i_key) >= 0){delete rowData['from_object'][i_key]}
        // convert url to clickable
        // if (link_field_names.indexOf(i_key) >= 0){rowData['from_object'][i_key] = <a href={"https://google.com"}>Link</a> }
    }
    for (let i_key in rowData['to_object']){
        // exclude all not needed data
        if (exclude.indexOf(i_key) >= 0){delete rowData['to_object'][i_key]}
        // convert url to clickable
        // if (link_field_names.indexOf(i_key) >= 0){rowData['to_object'][i_key] = <a href={"https://google.com"}>Link</a> }
    }

    let JsonTableFrom = <JsonToTable json={{'From': rowData['from_object']}} />
    let JsonTableTo = <JsonToTable json={{'To': rowData['to_object']}} />

    //console.log({'From': rowData['from_object']})
    //console.log({'To': rowData['to_object']})
    return(
        <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
        }}>
            <div>{JsonTableFrom}</div>
            <div>{JsonTableTo}</div>
        </div>
    )
}


function RenderCustomBrokerFieldNames(brokerName, brokerData){
    let CustomBrokerNames = ['BestChange']
    if (CustomBrokerNames.indexOf(brokerName) >= 0){
        let brokerPartName = (brokerData['exchange_name'] !== 'undefined') ? brokerData['exchange_name'] : ""
        // console.log(brokerPartName)
        brokerName = `${brokerName}-${brokerPartName}`
    }
    return brokerName
}


const App = () => {
        const [data, setData] = useState([]) //table data
        const [refreshData, setRefreshData] = React.useState(false);
        //const []
        // const [filter, setFilter] = useState([]) //table data
        //const [tableRef, setTableRef] = useState(React.createRef()) // let tableRef = React.createRef()
        const [columns, setColumns] = useState(
[
            {title: "ID", field: "index", hidden: true,
                cellStyle: { width: 150, minWidth: 150 }},
            {title: "Pair", field: "pair",
                defaultFilter: '',
            },
            {title: "From exchange", field: "from_ex",
                render:
                        rowData => <a href={rowData['from_object']['exchange_link']}
                                      target="_blank" > {RenderCustomBrokerFieldNames(rowData['from_ex'], rowData['from_object'])}
                                   </a>,
                defaultFilter: '',
                cellStyle: { width: 100, minWidth: 100 }
            },
            {title: "To exchange", field: "to_ex",
                render:
                        rowData => <a href={rowData['to_object']['exchange_link']}
                                      target="_blank" > {RenderCustomBrokerFieldNames(rowData['to_ex'], rowData['to_object'])} </a>,
                defaultFilter: '',
                cellStyle: { width: 100, minWidth: 100 }
            },
            {title: "From price", field: "from_price",
                defaultFilter: '',
            },
            {title: "To price", field: "to_price",
                defaultFilter: '',
            },
            {title: "Diff (value)", field: "diff",
                defaultFilter: '',
            },
            {title: "Diff (%)", field: "diff_percentage",
                defaultFilter: '',
            }
        ]
        )

        //for error handling
        const [iserror, setIserror] = useState(false)
        const [errorMessages, setErrorMessages] = useState([])

        useEffect(() => {
            // console.log('starting..')
            api.get("/get/table")
                .then(res => {
                    //console.log(res.data);
                    for (let i = 0; i < res.data.length; i++) { /* pre-edit data */
                    }
                    setData(res.data)
                }).catch(error => {
                    console.log("Error:", error)
                })
        }, [])

        function refreshPage() {
            window.location.reload(false);
          }

        const handleRowDelete = (oldData, resolve) => {
            const dataDelete = [...data];
                const index = oldData.tableData.id;
                dataDelete.splice(index, 1);
                setData([...dataDelete]);
                resolve()
        }

        return (
            <div className="App">
                <Grid container spacing={1}>
                    <Grid item xs={1}/>
                    <Grid item xs={10}>
                        <div>
                            {iserror &&
                            <Alert severity="error">
                                {errorMessages.map((msg, i) => {
                                    return <div key={i}>{msg}</div>
                                })}
                            </Alert>
                            }
                        </div>
                        {/*<button onClick={saveFilters(tableRef)}>Filters</button> // GET OCCURS HERE*/}
                        <MaterialTable
                            title="Crypto pairs"
                            //tableRef={tableRef}
                            columns={columns}
                            data={data}
                            icons={tableIcons}
                            // editable={{
                            //     onRowDelete: (oldData) =>
                            //         new Promise((resolve) => {
                            //             setTimeout(() => {
                            //                 handleRowDelete(oldData, resolve);
                            //             }, 1000)
                            //         }),
                            // }}
                            options={{
                                filtering: true,
                                pageSize: 10
                            }}
                            detailPanel={[
                                {
                                tooltip: 'Show info',
                                render: rowData => {
                                    return GetInfoTable(rowData.rowData)
                                }
                            },
                            ]}
                            actions={[
                                {
                                    // REFRESH TABLE REQUEST
                                    icon: () => <Refresh />,
                                    tooltip: 'Refresh Data',
                                    isFreeAction: true,
                                    disabled: refreshData,
                                    onClick: () => {
                                        // console.log(refreshData, !refreshData)
                                        if (!refreshData) {
                                            setRefreshData(true)
                                            setTimeout(() => {
                                                api.get("/get/table")
                                                    .then(res => {
                                                        //console.log(res.data);
                                                        for (let i = 0; i < res.data.length; i++) { /* pre-edit data */
                                                        }
                                                        if (data !== res.data) {
                                                            setData(res.data)
                                                            //setColumns(columns)
                                                        }
                                                    }).catch(error => {
                                                    console.log("Error:", error)
                                                })
                                            }, 1000)
                                            setRefreshData(false)
                                        }
                                    }
                                },
                                rowData => ({
                                    // HIDE EXCHANGE-BROKER RECORD REQUEST
                                    icon: () => <VisibilityOff />,
                                    tooltip: 'Hide exchange',
                                    isFreeAction: false,
                                    disabled: false,
                                    onClick: () => {
                                        console.log(rowData)
                                        return 0;
                                    }
                                })

                            ]}
                        />
                    </Grid>
                    <Grid item xs={6}/>
                </Grid>
            </div>
        );
    //}
}


// function updateColumns(tableRef) {
//   return function handler() {
//       return tableRef.current.columns
//   };
// }


export default App;
