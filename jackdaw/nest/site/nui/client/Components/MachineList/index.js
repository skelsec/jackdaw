import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';
const moment = require('moment');
import { 
    Table, TableRow, TableBody, TableCell,
    TableHead, TextField
} from '@material-ui/core';

import FirstPageIcon from '@material-ui/icons/FirstPage';
import KeyboardArrowLeft from '@material-ui/icons/KeyboardArrowLeft';
import KeyboardArrowRight from '@material-ui/icons/KeyboardArrowRight';
import LastPageIcon from '@material-ui/icons/LastPage';

import ApiClient from '../ApiClient';

const styles = theme => ({
});

class MachineListComponent extends ApiClient {

    state = {
        filter: '',
        machines: []
    }

    componentDidMount = async() => {
        let machineList = await this.apiFetch(`/machine/${this.props.domain}/list`);
        if ([undefined, null, false].includes(machineList)) return null;
        this.setState({
            machines: machineList.data
        });
    }

    renderMachines = () => {
        return this.state.machines.map(row => {
            if (this.state.filter != '' && !row[2].includes(this.state.filter)) {
                return null;
            }
            return (
                <TableRow
                    key={row[0]}
                >
                    <TableCell>
                        {row[0]}
                    </TableCell>
                    <TableCell>
                        {row[2]}
                    </TableCell>
                    <TableCell>
                        {row[1]}
                    </TableCell>
                </TableRow>
            );
        });
    }

    render() {
        return (
            <VBox>
                <Box>
                    <TextField
                        fullWidth={true}
                        label="Filter by Name"
                        skeleton={this.props.skeleton}
                        value={this.state.filter}
                        onChange={ (e) => this.setState({ filter: e.target.value }) }
                    />
                </Box>
                <Table className="margin-top">
                <TableHead>
                    <TableRow>
                        <TableCell>ID</TableCell>     
                        <TableCell>Name</TableCell>
                        <TableCell>SID</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {this.renderMachines()}
                </TableBody>
                </Table>
            </VBox>
        );
    }
}

const mapStateToProps = (state) => {
    return {}
}

const mapDispatchToProps = (dispatch) => {
    return {}
}

const MachineList = connect(mapStateToProps, mapDispatchToProps)(withStyles(styles, { withTheme: true })(MachineListComponent));
export default MachineList;
