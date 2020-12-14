'use strict';

import Graph from 'react-graph-vis';

import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';

import { 
    Paper, FormControl, FormControlLabel, FormGroup, 
    FormHelperText, Input, InputLabel, 
    Button, Select, MenuItem, TextField, Switch, Menu
} from '@material-ui/core';

import ApiClient from '../../Components/ApiClient';
import ExpansionPane from '../../Components/ExpansionPane';
import ItemDetails from '../../Components/ItemDetails';
import { ContextMenu } from './ContextMenu';
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
            avoidOverlap: 0
        },
        forceAtlas2Based: {
            gravitationalConstant: -50,
            centralGravity: 0.01,
            springConstant: 0.08,
            springLength: 100,
            damping: 0.4,
            avoidOverlap: 0
        },
        repulsion: {
            centralGravity: 0.2,
            springLength: 200,
            springConstant: 0.05,
            nodeDistance: 100,
            damping: 0.09
        },
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
        serchSrcResultsOpen: false,
        serchDstResultsOpen: false,
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
    }

    constructor(props) {
        super(props);
        this.processSelection = this.processSelection.bind(this);
        this.srcRef = React.createRef()
        this.dstRef = React.createRef()
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

        switch(d) {
            case "domainadmins":
                url = `/graph/${this.state.graph}/query/path/da/?format=vis`;
                break;
            case "src":
                url = `/graph/${this.state.graph}/query/path?src=${this.state.srcsid}&format=vis`;
                break;
            case "dst":
                url = `/graph/${this.state.graph}/query/path?dst=${this.state.srcsid}&format=vis`;
                break;
            case "path":
                url = `/graph/${this.state.graph}/query/path?dst=${this.state.dstsid}&src=${this.state.srcsid}&format=vis`;
                break;
            case "ownedtoda":
                url = `/graph/${this.state.graph}/query/path/ownedtoda`;
                break;
            case "fromowned":
                url = `/graph/${this.state.graph}/query/path/fromowned`;
                break;
            case "dcsync":
                url = `/graph/${this.state.graph}/query/path/dcsync`;
                break;
            case "kerberoasttoda":
                url = `/graph/${this.state.graph}/query/path/kerberoasttoda`;
                break;
            case "kerberoastany":
                url = `/graph/${this.state.graph}/query/path/kerberoastany`;
                break;
            case "asreproastda":
                url = `/graph/${this.state.graph}/query/path/asreproastda`;
                break;
            case "highvalue":
                url = `/graph/${this.state.graph}/query/path/tohighvalue`;
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

    handleMenuClick = (node, name) => {
        this.setState({
            nodeSelected: {
                domainid: node.adid,
                id: node.sid,
                type: node.otype,
                label: node.text,
            },
            [`${name}Selected`]: node,
            serchDstResultsOpen: false,
            serchSrcResultsOpen: false,
            [name]: node.text
        })
    }

    handleSearchPropertiesSwitch = async(obj, hvt) => {
        let result
        if (hvt) {
            result = await this.apiFetch(`/props/${this.state.graph}/${`${obj.sid}/owned/${obj.highvalue ? 'clear' : 'set'}`}`)
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
        // if (hvt) {
        //     this.setState({})
        // }
    }

    renderTextField = (name, label, description) =>  (
        <React.Fragment>
            <TextField
                ref={name === 'srcsid' ? this.srcRef : this.dstRef}
                className="margin-top"
                fullWidth={true}
                helperText={description}
                label={label}
                value={this.state[name]}
                onChange={ async(e) => {
                    this.setState({ [name]: e.target.value })
                    if(this.state[name].length >= 3) {
                        let result = await this.apiFetch(`/graph/${this.state.graph}/search/${e.target.value}`)
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
            />
            {this.state[`${name}Selected`] && (
                <FormGroup row>
                    <FormControlLabel
                        control={
                            <Switch
                        checked={this.state[`${name}Selected`].highvalue}
                        onChange={() => this.handleSearchPropertiesSwitch(this.state[`${name}Selected`], true)}
                        value="hvt"
                    />
                }
                label="HVT"
                />
                    <FormControlLabel
                        control={
                            <Switch
                        checked={this.state[`${name}Selected`].owned}
                        onChange={() => this.handleSearchPropertiesSwitch(this.state[`${name}Selected`])}
                        value="owned"
                    />
                }
                label="Owned"
                />
                </FormGroup>
            )}
        </React.Fragment>
        );

    renderSearchMenus = () => (
        <React.Fragment>
            <Menu
                anchorEl={this.srcRef.current}
                keepMounted
                open={this.state.srcsidResults.length > 0 && this.state.serchSrcResultsOpen}
                onClose={()=> this.setState({
                    serchSrcResultsOpen: false,
                    srcsidResults: [],
                })}
            >
                {this.state.srcsidResults.map((el) => (
                    <MenuItem key={el.sid} onClick={()=> this.handleMenuClick(el, 'srcsid')}>{el.text}</MenuItem>
                    ))}
            </Menu>
            <Menu
                anchorEl={this.dstRef.current}
                keepMounted
                open={this.state.dstsidResults.length > 0 && this.state.serchDstResultsOpen}
                onClose={()=> this.setState({
                    serchDstResultsOpen: false,
                    dstsidResults: []
                })}
            >
                {this.state.dstsidResults.map((el) => (
                    <MenuItem key={el.sid} onClick={()=> this.handleMenuClick(el, 'dstsid')}>{el.text}</MenuItem>
                    ))}
            </Menu>
        </React.Fragment>
    )


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

    processSelection = async(event) => {
        this.setState({contextMenu: {opened: false}})
        var { nodes } = event;
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

    renderGraphControls = () => {
        return (
            <VBox className="mbox pbox">
                <Box>
                    {this.renderGraphSelector()}
                </Box>
                <Box className="margin-top" column>
                    {this.renderTextField('srcsid', 'SRC SID', 'Source SID')}
                </Box>
                <Box className="margin-top" column>
                    {this.renderTextField('dstsid', 'DST SID', 'Destination SID')}
                </Box>
                <Box className="margin-top">
                    {this.renderModeSelector()}
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
                            {this.renderSearchMenus()}
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
