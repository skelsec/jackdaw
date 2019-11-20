import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';
const moment = require('moment');
import { 
    Table, TableRow, TableBody, TableCell,
    TableHead, FormControl, InputLabel,
    Select, MenuItem, Input
} from '@material-ui/core';

import ApiClient from '../ApiClient';

const styles = theme => ({
});

class AnomalyOutdatedOSComponent extends ApiClient {

    state = {
        data: [],
        versionFilter: null
    }

    componentDidMount = async() => {
        let result = await this.apiFetch(`/anomalies/${this.props.domain}/computer/outdated`);
        if ([undefined, null, false].includes(result)) return null;
        this.setState({
            data: result.data
        });
    }

    renderOsVersionList = () => {
        const versions = Object.keys(this.state.data);
        return versions.map((item, index) => {
            return (
                <MenuItem key={index} value={item}>{item}</MenuItem>
            );
        });
    }

    renderOsSelector = () => {
        if (this.state.data.length == 0) return null;
        return (
            <FormControl fullWidth={true}>
                <InputLabel>Operating System</InputLabel>
                <Select
                    fullWidth={true}
                    value={this.state.versionFilter || ''}
                    onChange={(e) => this.setState({ versionFilter: e.target.value })}
                    input={<Input value={this.state.versionFilter} fullWidth={true} />}
                >
                    <MenuItem key="os_all" value={null}>All</MenuItem>
                    {this.renderOsVersionList()}
                </Select>
            </FormControl>
        );
    }

    renderItems = () => {
        let versions = Object.keys(this.state.data);

        return versions.map((version, index) => {
            if (![undefined, null].includes(this.state.versionFilter) && version != this.state.versionFilter) {
                return null;
            }
            return this.state.data[version].map((machine, mindex) => {
                return (
                    <TableRow
                        key={`${index}-${mindex}`}
                    >
                        <TableCell>
                            {version}
                        </TableCell>
                        <TableCell>
                            {machine[0]}
                        </TableCell>
                        <TableCell>
                            {machine[1]}
                        </TableCell>
                    </TableRow>
                );
            });
        });
    }

    render() {
        return (
            <VBox>
                <Box className="mbox">
                    {this.renderOsSelector()}
                </Box>
                <Table className="margin-top">
                    <TableHead>
                        <TableRow>
                            <TableCell>OS</TableCell>     
                            <TableCell>Machine ID</TableCell>
                            <TableCell>Machine Name</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {this.renderItems()}
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

const AnomalyOutdatedOS = connect(mapStateToProps, mapDispatchToProps)(withStyles(styles, { withTheme: true })(AnomalyOutdatedOSComponent));
export default AnomalyOutdatedOS;
