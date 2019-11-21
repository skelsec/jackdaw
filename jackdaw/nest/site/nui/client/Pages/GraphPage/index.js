'use strict';

import Graph from 'react-graph-vis';

import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';

import { 
    Paper, FormControl, FormControlLabel, FormGroup, 
    FormHelperText, Input, InputLabel, 
    Button, Select, MenuItem, TextField, Switch
} from '@material-ui/core';

import ApiClient from '../../Components/ApiClient';
import ExpansionPane from '../../Components/ExpansionPane';
import ItemDetails from '../../Components/ItemDetails';

const styles = theme => ({
    graphBox: {
        backgroundColor: '#f2f2f2'
    }
});

const graphOptions = {
    height: '100%',
    width: '100%',
    autoResize: true,
    edges: {
        arrowStrikethrough: true,
        chosen: true,
        dashes: false,
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
        graph: null,
        graphData: null,
        graphOptions: JSON.parse(JSON.stringify(graphOptions)),
        url: null,
        altmode: false,
        udOpen: true,
        nodeSelected: null
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

    handleAltModeChange = (e) => {
        let newGraphOptions = JSON.parse(JSON.stringify(graphOptions));
        if (e.target.checked == true) {
            newGraphOptions['edges']['arrows'] = {
                to: {enabled: false, scaleFactor:0.5, type:'bar'},
                middle: {enabled: false, scaleFactor:1, type:'arrow'},
                from: {enabled: false, scaleFactor:0.5, type:'arrow'}
            }
            newGraphOptions['layout'] = {
                hierarchical: {
                    direction: "LR",
                    sortMethod: "directed",
                    levelSeparation: 400,
                    nodeSpacing: 100, 
                    //randomSeed: 6
                }
            };
            newGraphOptions['interaction'] = {
                hover: true
            }
        }
        this.setState({
            altmode: e.target.checked,
            graphOptions: newGraphOptions
        });
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
            default:
                return;
        }
        let gd = await this.apiFetch(url);
        gd.data.nodes = this.preProcessNodes(gd.data.nodes);
        this.setState({ graphData: gd.data });
    }

    renderGraphItems = () => {
        return this.state.graphs.map((item, index) => {
            return (
                <MenuItem key={index} value={item}>{item}</MenuItem>
            );
        });
    }

    renderTextField = (name, label, description) => {
        return (
            <TextField
                className="margin-top"
                fullWidth={true}
                helperText={description}
                label={label}
                value={this.state[name]}
                onChange={ (e) => this.setState({ [name]: e.target.value }) }
            />
        );
    }

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
        var { nodes, edges } = event;
        const node = this.state.graphData.nodes.filter(item => item.id == nodes[0]);
        if (node.length == 0) return;
        const targetNode = node[0];
        this.setState({ nodeSelected: targetNode });
    }

    events = {
        select: this.processSelection
    };

    renderGraph = () => {
        if ([undefined, null].includes(this.state.graphData)) return null;

        const { classes } = this.props;

        return (
            <Box className={classes.graphBox} fit>
                <Graph
                    graph={this.state.graphData}
                    options={this.state.graphOptions}
                    events={this.events}
                    style={{
                        width: '100%',
                        height: '100%'
                    }}
                />
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
                onClick={(e) => this.setState({ udOpen: !this.state.udOpen })}
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
                <Box className="margin-top">
                    {this.renderTextField('srcsid', 'SRC SID', 'Source SID')}
                </Box>
                <Box className="margin-top">
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
                            onClick={(e) => this.fetchGraph('domainadmins')}
                        >
                            Draw Domain Admins
                        </Button>
                    </Box>
                    <Box className="margin-top">
                        <Button
                            color="primary"
                            variant="contained"
                            onClick={(e) => this.fetchGraph('path')}
                        >
                            Draw Path
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
