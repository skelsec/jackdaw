'use strict';

import Graph from 'react-graph-vis';

import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';

import { 
    Paper, FormControl, FormControlLabel, FormGroup, 
    FormHelperText, Input, InputLabel, 
    Button, Select, MenuItem, Switch, TextField
} from '@material-ui/core';
import Autocomplete from '@material-ui/lab/Autocomplete';

import ApiClient from '../../Components/ApiClient';
import ExpansionPane from '../../Components/ExpansionPane';
import ItemDetails from '../../Components/ItemDetails';
import { ContextMenu } from './ContextMenu';
import { RequestModifier } from './RequestModifier';
import _ from 'lodash';

const styles = () => ({
    graphBox: {
        backgroundColor: '#f2f2f2',
        '& > div > div': {
            height: '100%',
            '& canvas': {
            height: '100vh !important',
            maxHeight: '100% !important',
            }
        }
    }
});

const graphOptions = {
    autoResize: true,
    layout: {
        hierarchical: false
    },
    edges: {
        arrowStrikethrough: true,
        chosen: true,
        dashes: false,
        smooth: {
            enabled: false,
        },
        arrows: {
            to: {enabled: true, scaleFactor:0.75, type:'arrow'},
            middle: {enabled: false, scaleFactor:1, type:'arrow'},
            from: {enabled: true, scaleFactor:0.3, type:'arrow'}
        },
        color: {
            // color:'#848484',
            color:'#3F51B5',
            highlight:'#848484',
            hover: '#848484',
            inherit: 'from',
            opacity:1.0
        },
        font: {
            color: '#343434',
            size: 14, // px
            face: 'arial',
            background: 'none',
            strokeWidth: 2, // px
            strokeColor: '#ffffff',
            align: 'horizontal',
            multi: false,
            vadjust: 0,
            bold: {
                color: '#343434',
                size: 14, // px
                face: 'arial',
                vadjust: 0,
                mod: 'bold'
            },
            ital: {
                color: '#343434',
                size: 14, // px
                face: 'arial',
                vadjust: 0,
                mod: 'italic'
            },
            boldital: {
                color: '#343434',
                size: 14, // px
                face: 'arial',
                vadjust: 0,
                mod: 'bold italic'
            },
            mono: {
                color: '#343434',
                size: 15, // px
                face: 'courier new',
                vadjust: 2,
                mod: ''
            }
        }
    },
    interaction: {
        hover: false,
    },
    // http://visjs.org/docs/network/physics.html#
    physics: {
        enabled: true,
        barnesHut: {
            gravitationalConstant: -2000,
            centralGravity: 0.3,
            // springLength: 95,
            springLength: 175,
            springConstant: 0.04,
            damping: 0.09,
            avoidOverlap: 0.2
        },
        //forceAtlas2Based: {
        //    gravitationalConstant: -50,
        //    centralGravity: 0.01,
        //    springConstant: 0.08,
        //    springLength: 100,
        //    damping: 0.4,
        //    avoidOverlap: 0
        //},
        //repulsion: {
        //    centralGravity: 0.2,
        //    springLength: 200,
        //    springConstant: 0.05,
        //    nodeDistance: 100,
        //    damping: 0.09
        //},
        hierarchicalRepulsion: {
            centralGravity: 0.0,
            springLength: 100,
            springConstant: 0.01,
            nodeDistance: 120,
            damping: 0.09
        },
        maxVelocity: 50,
        minVelocity: 0.1,
        solver: 'barnesHut',
        stabilization: {
            enabled: true,
            iterations: 1000,
            updateInterval: 100,
            onlyDynamicEdges: false,
            fit: true
        },
        timestep: 0.5,
        adaptiveTimestep: true
    }
};

class GraphPageComponent extends ApiClient {

    state = {
        graphs: [],
        srcsid: '',
        dstsid: '',
        srcsidResults: [],
        dstsidResults: [],
        srcsidSelected: null,
        dstsidSelected: null,
        graph: null,
        graphData: null,
        graphOptions: { ...graphOptions },
        url: null,
        altmode: false,
        udOpen: true,
        nodeSelected: null,
        network: null,
        contextMenu: {
            opened: false,
            top: null,
            left: null,
        },
        selectedContextNode: null,
        requestModifiers: [],
        clustering: true,
        maxHops: '',
    }

    constructor(props) {
        super(props);
        this.processSelection = this.processSelection.bind(this);
    }

    componentDidMount = async() => {
        let graphList = await this.apiFetch('/graph');
        if ([undefined, null, false].includes(graphList)) {
            graphList = {
                data: {
                    edges: [],
                    nodes: []
                }
            }
        }
        this.setState({
            graphs: graphList.data
        });
    }

    componentDidUpdate(prevProps, prevState) {
        if (this.state.network !== prevState.network) {
            if (this.state.clustering) {

                // TODO: Change hardcoded nodeID below
                //this.state.network.clusterByConnection('S-1-5-32-544')
                this.state.network.clusterByHubsize(50, undefined)
                //this.state.network.clusterOutliers()
                //this.state.network.clusterByEdgeCount(20)
                //this.state.network.clusterByHubsize(undefined, undefined)
                //
                //const hubsize = 50;
                //const nodesToCluster = [];
                //for (let node in this.state.network.nodes) {
                //    console.log(node.options)
                //    if(node.options.md == 1 || node.options.md == 0 ||node.options.md == 2 || node.options.md == null){
                //        if (node.edges.length >= hubsize) {
                //            nodesToCluster.push(node.id);
                //        }
                //    }
                //}
                //
                //for (let i = 0; i < nodesToCluster.length - 1; i++) {
                //    this.state.network.clusterByConnection(nodesToCluster[i], undefined, false);
                //}
                //
                //this.state.network.clusterByConnection(nodesToCluster[nodesToCluster.length], undefined, true);
                //
            }
        }

        if (this.state.clustering !== prevState.clustering) {
            if (this.state.network) {
                if (this.state.clustering) {
                    //const hubsize = 50;
                    //const nodesToCluster = [];
                    //for (let node in this.state.network.nodes) {
                    //    console.log(node.options)
                    //    if(node.options.md == 1 || node.options.md == 0 ||node.options.md == 2 || node.options.md == null){
                    //        if (node.edges.length >= hubsize) {
                    //            nodesToCluster.push(node.id);
                    //        }
                    //    }
                    //}
                    //
                    //for (let i = 0; i < nodesToCluster.length - 1; i++) {
                    //    this.state.network.clusterByConnection(nodesToCluster[i], undefined, false);
                    //}
                    //
                    //this.state.network.clusterByConnection(nodesToCluster[nodesToCluster.length], undefined, true);
                    
                    
                    
                    //this.state.network.clusterByConnection('S-1-5-32-544')
                    this.state.network.clusterByHubsize(50, undefined)
                    //this.state.network.clusterOutliers()
                    //this.state.network.clusterByEdgeCount(20)
                    //this.state.network.clusterByHubsize(undefined, undefined)
                } else {
                    for(let i in this.state.network.clustering.clusteredNodes) {
                        try{
                            this.state.network.openCluster(this.state.network.clustering.clusteredNodes[i].clusterId)
                        }
                        catch (error) {
                            console.log('openCluster Error! ' + error)
                        }

                    }
                }
            }
        }
    }

    applySmoothToEdges = array => {
        const newArray = [...array]
        newArray.forEach((el, index) => {
            newArray.forEach((compEl, compIndex) => {
                if(!_.isEqual(el, compEl) && el.from === compEl.from) {
                    if(!el.smooth){
                        newArray[index] = {
                            ...el,
                            smooth: {
                                enabled: true,
                                type: "curvedCW",
                                roundness: 0.1
                            }
                        }
                    }
                    if(!compEl.smooth){
                        newArray[compIndex] = {
                            ...compEl,
                            smooth: {
                                enabled: true,
                                type: "curvedCCW",
                                roundness: 0.1
                            }
                        }
                    }
                }
            })
        })
        return newArray
    }

    handleAltModeChange = (e) => {
        this.setState({altmode: e.target.checked });
    }

    renderModeSelector = () => {
        return (
            <FormGroup row>
                <FormControlLabel
                control={
                    <Switch
                        checked={this.state.altmode}
                        onChange={this.handleAltModeChange}
                        value="altmode"
                    />
                }
                label="Hierarchial Layout"
                />
            </FormGroup>
        );
    }

    renderClusteringSwitch = () => (
        <FormGroup row>
            <FormControlLabel
                control={
                    <Switch
                        checked={this.state.clustering}
                        onChange={e => {
                            this.setState({clustering: e.target.checked})
                        }}
                        value="clustering"
                    />
                }
                label="Clustering"
                />
        </FormGroup>
    )

    getNodeTitle = (node) => {
        return `<table class="node-label-wrapper"><tr class="node-label-name"><td class="node-label-name-key">Name:</td><td class="node-label-name-value">${node.label}</td></tr><tr class="node-label-type"><td class="node-label-type-key">Type:</td><td class="node-label-type-value">${node.type}</td></tr><tr class="node-label-id"><td class="node-label-id-key">ID:</td><td class="node-label-id-value">${node.id}</td></tr></table>`;
    }

    getNodeImage = (node) => {
        let imgData = {
            selected: null,
            unselected: null
        }
        switch(node.type) {
            case 'group':
                imgData.selected = '/nest/group.png';
                imgData.unselected = '/nest/group.png';
                break;
            case 'user':
                imgData.selected = '/nest/user.png';
                imgData.unselected = '/nest/user.png';
                break;
            case 'machine':
                imgData.selected = '/nest/computer.png';
                imgData.unselected = '/nest/computer.png';
                break;
            default:
                imgData.selected = '/nest/unknown.png';
                imgData.unselected = '/nest/unknown.png';
                break;
        }
        return imgData;
    }

    preProcessNodes = (nodes) => {
        return nodes.map(node => {
            node['image'] = this.getNodeImage(node);
            node['title'] = this.getNodeTitle(node);
            node['shape'] = 'circularImage';
            return node;
        });
    }

    fetchGraph = async(d) => {
        let url = "";
        const excludeParameter = this.state.requestModifiers.length > 0 ? `/?exclude=${this.state.requestModifiers.join()}` : ''
        const excludeAddParameter = this.state.requestModifiers.length > 0 ? `&exclude=${this.state.requestModifiers.join()}` : ''

        switch(d) {
            case "domainadmins":
                url = `/graph/${this.state.graph}/query/path/da/?format=vis${excludeAddParameter}`;
                break;
            case "src":
                url = `/graph/${this.state.graph}/query/path?src=${this.state.srcsid}&format=vis${excludeAddParameter}`;
                break;
            case "dst":
                url = `/graph/${this.state.graph}/query/path?dst=${this.state.srcsid}&format=vis${excludeAddParameter}`;
                break;
            case "path":
                if(this.state.dstsidSelected != null && this.state.srcsidSelected != null){
                    url = `/graph/${this.state.graph}/query/path?dst=${this.state.dstsidSelected.sid}&src=${this.state.srcsidSelected.sid}&format=vis${excludeAddParameter}&maxhops=${this.state.maxHops}`;
                }
                if(this.state.dstsidSelected == null && this.state.srcsidSelected != null){
                    url = `/graph/${this.state.graph}/query/path?src=${this.state.srcsidSelected.sid}&format=vis${excludeAddParameter}&maxhops=${this.state.maxHops}`;
                }
                if(this.state.dstsidSelected != null && this.state.srcsidSelected == null){
                    url = `/graph/${this.state.graph}/query/path?dst=${this.state.dstsidSelected.sid}&format=vis${excludeAddParameter}&maxhops=${this.state.maxHops}`;
                }
                if(this.state.dstsidSelected == null && this.state.srcsidSelected == null){
                    console.log("At least SRC or DST must be set!");
                }
                break;
            case "ownedtoda":
                url = `/graph/${this.state.graph}/query/path/ownedtoda${excludeParameter}`;
                break;
            case "fromowned":
                url = `/graph/${this.state.graph}/query/path/fromowned${excludeParameter}`;
                break;
            case "dcsync":
                url = `/graph/${this.state.graph}/query/path/dcsync${excludeParameter}`;
                break;
            case "kerberoasttoda":
                url = `/graph/${this.state.graph}/query/path/kerberoasttoda${excludeParameter}`;
                break;
            case "kerberoastany":
                url = `/graph/${this.state.graph}/query/path/kerberoastany${excludeParameter}`;
                break;
            case "asreproastda":
                url = `/graph/${this.state.graph}/query/path/asreproastda${excludeParameter}`;
                break;
            case "highvalue":
                url = `/graph/${this.state.graph}/query/path/tohighvalue${excludeParameter}`;
                break;
			case "fromownedtohighvalue":
				url = `/graph/${this.state.graph}/query/path/fromownedtohighvalue${excludeParameter}`;
				break;
			case "members":
				url = `/graph/${this.state.graph}/members/${this.state.srcsidSelected.sid}`;
				break;
            default:
                return;
        }
        let gd = await this.apiFetch(url);
        gd.data.nodes = this.preProcessNodes(gd.data.nodes);
        gd.data.edges = this.applySmoothToEdges(gd.data.edges)
        this.setState({ graphData: gd.data });
    }

    renderGraphItems = () => {
        return this.state.graphs.map((item, index) => {
            return (
                <MenuItem key={index} value={item}>{item}</MenuItem>
            );
        });
    }

    handleSearchPropertiesSwitch = async(obj, name, hvt) => {
        let result
        if (hvt) {
            result = await this.apiFetch(`/props/${this.state.graph}/${`${obj.sid}/hvt/${obj.highvalue ? 'clear' : 'set'}`}`)
        } else {
            result = await this.apiFetch(`/props/${this.state.graph}/${`${obj.sid}/owned/${obj.owned ? 'clear' : 'set'}`}`)
        }
        if (result.status != 204) {
            this.notifyUser({
                severity: 'error',
                message: `User ${hvt ? 'HVT' : 'Owned'} set Failed`
            });
            return;
        }
        this.notifyUser({
            severity: 'success',
            message: `User ${hvt ? 'HVT' : 'Owned'} set OK`
        });
        if (hvt) {
            this.setState(prevState => {
                return {[name]: {
                ...prevState[name],
                highvalue: !prevState[name].highvalue,
            }}})
        } else {
            this.setState(prevState => {
                return {[name]: {
                ...prevState[name],
                owned: !prevState[name].owned,
            }}})
        }
    }

    renderTextField = (name, label, description) =>  (
        <React.Fragment>
            <Autocomplete
                value={this.state[`${name}Selected`] && this.state[`${name}Selected`].text}
                options={this.state[`${name}Results`].map(el => el.text)}
                onChange={(e, newValue) => {
                        const node = this.state[`${name}Results`].find(el => el.text === newValue)
                        this.setState({
                            [`${name}Selected`]: node,
                            nodeSelected: {
                                domainid: node.adid,
                                id: node.sid,
                                type: node.otype,
                                label: node.text,
                            },
                        })
                }}
                onInputChange={async(e, value) => {
                    if(value.length >= 3) {
                        let result = await this.apiFetch(`/graph/${this.state.graph}/search/${value}`)
                        if (result.status != 200) {
                            this.notifyUser({
                                severity: 'error',
                                message: `Search results Error`
                            })
                            return
                        }
                        this.setState({[`${name}Results`]: result.data.slice(0,5)})
                        name === 'srcsid' ? this.setState({serchSrcResultsOpen: true}) : this.setState({serchDstResultsOpen: true})
                    }
                }}
                renderInput={(params) => (
                    <TextField 
                        {...params} 
                        label={label} 
                        helperText={description}
                        className="margin-top"
                        fullWidth={true} 
                    />
                  )}
            />
            {this.state[`${name}Selected`] && (
                <FormGroup row>
                    <FormControlLabel
                        control={
                            <Switch
                        checked={this.state[`${name}Selected`].highvalue}
                        onChange={() => this.handleSearchPropertiesSwitch(this.state[`${name}Selected`], `${name}Selected`, true)}
                        value="hvt"
                    />
                }
                label="HVT"
                />
                    <FormControlLabel
                        control={
                            <Switch
                        checked={this.state[`${name}Selected`].owned}
                        onChange={() => this.handleSearchPropertiesSwitch(this.state[`${name}Selected`], `${name}Selected`)}
                        value="owned"
                    />
                }
                label="Owned"
                />
                </FormGroup>
            )}
        </React.Fragment>
        );

    renderGraphSelector = () => {
        return (
            <FormControl fullWidth={true}>
                <InputLabel>Graphs</InputLabel>
                <Select
                    fullWidth={true}
                    value={this.state.graph || ''}
                    onChange={ (e) => this.setState({ graph: e.target.value }) }
                    input={<Input value={this.state.graph} fullWidth={true} />}
                >
                    <MenuItem value={null}>None</MenuItem>
                    {this.renderGraphItems()}
                </Select>
                <FormHelperText>Select Graph ID to render.</FormHelperText>
            </FormControl>
        );
    }

    renderMaxDisplayHops = () => {
        return (
            <FormControl>
                <InputLabel htmlFor="maxhopsInput">Max Display Distance</InputLabel>
                <Input id="maxhops" aria-describedby="maxHopsInputHelperText" onChange={ (e) => this.setState({ maxHops: e.target.value }) }/>
                <FormHelperText id="maxHopsInputHelperText">Reduces the distance for each path returned, capping it to this size</FormHelperText>
            </FormControl>
        );
    }

    processSelection = async(event) => {
        this.setState({contextMenu: {opened: false}})
        const { nodes } = event;

        if (this.state.network.isCluster(nodes[0])) {
            this.state.network.openCluster(nodes[0]);
        }

        const node = this.state.graphData.nodes.filter(item => item.id == nodes[0]);
        if (node.length == 0) return;
        const targetNode = node[0];
        this.setState({ nodeSelected: targetNode });
    }

    handleContext = event => {
        event.event.preventDefault()
        this.setState({contextMenu: {opened: false}})
        const nodeId = this.state.network.getNodeAt(event.pointer.DOM)
        if (!nodeId) return;
        this.setState({
            selectedContextNode: this.state.graphData.nodes.filter(item => item.id == nodeId)
        })
        this.setState(prevState => {
            return {
                contextMenu: {
                    opened: !prevState.contextMenu.opened,
                    top: event.pointer.DOM.y,
                    left: event.pointer.DOM.x,
            }}
        })
    }

    handleClick = () => {
        this.setState({contextMenu: {opened: false}})
    }

    handleContextMenuClick =  async(url, hvt) =>{
        let result = await this.apiFetch(`/props/${this.state.graph}/${url}`)
        if (result.status != 204) {
            this.notifyUser({
                severity: 'error',
                message: `User ${hvt ? 'HVT' : 'Owned'} set Failed`
            });
            return;
        }
        this.setState({contextMenu: {opened: false}})
        this.notifyUser({
            severity: 'success',
            message: `User ${hvt ? 'HVT' : 'Owned'} set OK`
        });
    }

    events = {
        click: this.handleClick,
        select: this.processSelection,
        oncontext: this.handleContext
    };

    renderGraph = () => {
        if ([undefined, null].includes(this.state.graphData)) return null;

        const { classes } = this.props;

        let newGraphOptions = { ...graphOptions };
        if(this.state.altmode) {
            newGraphOptions['edges'] = {
                ...graphOptions.edges,
                arrows: {
                to: {enabled: false, scaleFactor:0.5, type:'bar'},
                middle: {enabled: false, scaleFactor:1, type:'arrow'},
                from: {enabled: false, scaleFactor:0.5, type:'arrow'}
                }
            }
            newGraphOptions['layout'] = {
                hierarchical: {
                    direction: "LR",
                    sortMethod: "directed",
                    levelSeparation: 400,
                    nodeSpacing: 100,
                }
            };
            newGraphOptions['interaction'] = {
                hover: true
            }
        }
        
        return (
            <Box className={classes.graphBox} fit>
                <Graph
                    graph={this.state.graphData}
                    options={newGraphOptions}
                    events={this.events}
                    getNetwork={(network) => {this.setState({ network });}}
                />
                {this.state.contextMenu.opened && (
                    <ContextMenu
                        menu={this.state.contextMenu}
                        node={this.state.selectedContextNode[0]}
                        handleContextMenuClick={this.handleContextMenuClick}
                    />
                )}
            </Box>
        );
    }
    
    renderNodeDetails = () => {
        if ([undefined, null].includes(this.state.nodeSelected)) return null;
        return (
            <ExpansionPane
                className="margin-top"
                label="Details"
                expanded={this.state.udOpen}
                onClick={() => this.setState({ udOpen: !this.state.udOpen })}
            >
                <ItemDetails
                    domain={this.state.nodeSelected.domainid}
                    type={this.state.nodeSelected.type}
                    selection={this.state.nodeSelected}
                    id={this.state.nodeSelected.id}
                    by="sid"
                />
            </ExpansionPane>
        );
    }

    setModifiers = array => this.setState({requestModifiers: array})

    renderGraphControls = () => {
        return (
            <VBox className="mbox pbox">
                <Box>
                    {this.renderGraphSelector()}
                </Box>
                <Box className="margin-top" column>
                    {this.renderTextField('srcsid', 'SRC', 'Source Node')}
                </Box>
                <Box className="margin-top" column>
                    {this.renderTextField('dstsid', 'DST', 'Destination Node')}
                </Box>
                <Box className="margin-top" column>
                    {this.renderMaxDisplayHops()}
                </Box>
                <Box className="margin-top">
                    {this.renderModeSelector()}
                </Box>
                <Box className="margin-top">
                    {this.renderClusteringSwitch()}
                </Box>
                <Box className="margin-top">
                    <RequestModifier onChange={this.setModifiers}/>
                </Box>
                <VBox className="margin-top">
                    <Box className="margin-top margin-bottom">
                        <Button
                            color="primary"
                            variant="contained"
                            onClick={() => this.fetchGraph('domainadmins')}
                        >
                            Draw Domain Admins
                        </Button>
                    </Box>
                    <Box className="margin-top">
                        <Button
                            color="primary"
                            variant="contained"
                            onClick={() => this.fetchGraph('path')}
                        >
                            Draw Path
                        </Button>
                    </Box>
                    <Box className="margin-top">
                        <Button
                            color="primary"
                            variant="contained"
                            onClick={() => this.fetchGraph('ownedtoda')}
                        >
                            Draw Path from Owned users to DA
                        </Button>
                    </Box>
                    <Box className="margin-top">
                        <Button
                            color="primary"
                            variant="contained"
                            onClick={() => this.fetchGraph('fromowned')}
                        >
                            Draw Path from Owned users to anywhere
                        </Button>
                    </Box>
                    <Box className="margin-top">
                        <Button
                            color="primary"
                            variant="contained"
                            onClick={() => this.fetchGraph('dcsync')}
                        >
                            List users with DCSYNC rights
                        </Button>
                    </Box>
                    <Box className="margin-top">
                        <Button
                            color="primary"
                            variant="contained"
                            onClick={() => this.fetchGraph('kerberoasttoda')}
                        >
                            Drwaw Path from Kerberoastable users to DA
                        </Button>
                    </Box>
                    <Box className="margin-top">
                        <Button
                            color="primary"
                            variant="contained"
                            onClick={() => this.fetchGraph('kerberoastany')}
                        >
                            Drwaw Path from Kerberoastable users to anywhere
                        </Button>
                    </Box>
                    <Box className="margin-top">
                        <Button
                            color="primary"
                            variant="contained"
                            onClick={() => this.fetchGraph('asreproastda')}
                        >
                            Drwaw Path from ASREProastable users to DA
                        </Button>
                    </Box>
                    <Box className="margin-top">
                        <Button
                            color="primary"
                            variant="contained"
                            onClick={() => this.fetchGraph('asreproast')}
                        >
                            Drwaw Path from ASREProastable users to DA
                        </Button>
                    </Box>
                    <Box className="margin-top">
                        <Button
                            color="primary"
                            variant="contained"
                            onClick={() => this.fetchGraph('highvalue')}
                        >
                            Draw user paths to High Value targets
                        </Button>
                    </Box>
					<Box className="margin-top">
                        <Button
                            color="primary"
                            variant="contained"
                            onClick={() => this.fetchGraph('fromownedtohighvalue')}
                        >
                            Draw paths from owned users to high value targets
                        </Button>
                    </Box>
					<Box className="margin-top">
                        <Button
                            color="primary"
                            variant="contained"
                            onClick={() => this.fetchGraph('members')}
                        >
                            List group members. Group should be in SRC
                        </Button>
                    </Box>
                </VBox>
            </VBox>
        );
    }

    render() {
        const { classes, theme } = this.props;
        
        return (
            <Paper className="mbox pbox" height="100%" >
                <VBox fit>
                    <Box fit>
                        <VBox flex={3}>
                            {this.renderGraph()}
                            {this.renderNodeDetails()}
                        </VBox>
                        <VBox flex={1}>
                            {this.renderGraphControls()}
                        </VBox>
                    </Box>
                </VBox>
            </Paper>
        );
    }
}

const mapStateToProps = (state) => {
    return {}
}

const mapDispatchToProps = (dispatch) => {
    return {}
}

const GraphPage = connect(mapStateToProps, mapDispatchToProps)(withStyles(styles, { withTheme: true })(GraphPageComponent));
export default GraphPage;
