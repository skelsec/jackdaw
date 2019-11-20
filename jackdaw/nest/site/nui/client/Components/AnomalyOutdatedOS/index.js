import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';
const moment = require('moment');
import { 
    FormControl, InputLabel, Select, MenuItem, Input
} from '@material-ui/core';

import ApiClient from '../ApiClient';
import AnomalyOutdatedOSList from '../AnomalyOutdatedOSList';

const styles = theme => ({
});


class AnomalyOutdatedOSComponent extends ApiClient {

    state = {
        versions: [],
        versionFilter: null
    }

    componentDidMount = async() => {
        await this.fetchVersions();
    }

    fetchVersions = async() => {
        let result = await this.apiFetch(`/machine/${this.props.domain}/versions`);
        if ([undefined, null, false].includes(result)) return null;
        this.setState({
            versions: result.data
        });        
    }

    renderOsVersionList = () => {
        return this.state.versions.map((item, index) => {
            return (
                <MenuItem key={index} value={item}>{item}</MenuItem>
            );
        });
    }

    renderOsSelector = () => {
        if (this.state.versions.length == 0) return null;
        return (
            <FormControl fullWidth={true}>
                <InputLabel>Operating System</InputLabel>
                <Select
                    fullWidth={true}
                    value={this.state.versionFilter || ''}
                    onChange={(e) => this.setState({ versionFilter: e.target.value })}
                    input={<Input value={this.state.versionFilter} fullWidth={true} />}
                >
                    {this.renderOsVersionList()}
                </Select>
            </FormControl>
        );
    }

    render() {
        return (
            <VBox>
                <Box className="mbox">
                    {this.renderOsSelector()}
                </Box>
                {this.state.versionFilter && <AnomalyOutdatedOSList
                    domain={this.props.domain}
                    version={this.state.versionFilter}
                />}
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
