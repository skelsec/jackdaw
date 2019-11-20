'use strict';

import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';

import {
    Paper, FormControl, Input, InputLabel, 
    Select, MenuItem
} from '@material-ui/core';


import ApiClient from '../../Components/ApiClient';
import AnomalyDomainMismatch from '../../Components/AnomalyDomainMismatch';
import AnomalyUserDescriptions from '../../Components/AnomalyUserDescriptions';
import AnomalyOutdatedOS from '../../Components/AnomalyOutdatedOS';
import AnomalySMBSigning from '../../Components/AnomalySMBSigning';
import AnomalyUserAccounts from '../../Components/AnomalyUserAccounts';

import * as actions from '../../Store/actions';

const styles = theme => ({
});

const anomalies = [
    { key: null, name: 'Select...' },
    { key: 'machines_description', name: 'Machine Descriptions' },
    { key: 'users_description', name: 'User Account Descriptions' },
    { key: 'machines_domainmismatch', name: 'SMB Domain Mismatches' },
    { key: 'machines_outdatedos', name: 'Outdated Operating Systems' },
    { key: 'machines_smbsign', name: 'SMB Signing Issues' },
    { key: 'machines_users', name: 'User Account Issues' }
];

class AnomaliesComponent extends ApiClient {

    state = {
        domains: [],
        domainSelected: null,
        show: null
    }
    
    componentDidMount = async() => {
        // We have to ignore pagination here so we get a million entries.
        // Maybe someday we figure out a better way.
        const result = await this.apiFetch('/domain/list?page=1&maxcnt=1000000');
        if ([undefined, null, false].includes(result)) return;
        if (result.status != 200) {
            this.props.notifyUser({
                severity: 'error',
                message: 'Failed to load domains.'
            });
            return;
        }
        this.setState({ domains: result.data.res });
    }

    selectAnomaly = (type) => {
        this.setState({ show: type });
    }

    renderDomainItems = () => {
        return this.state.domains.map((item, index) => {
            return (
                <MenuItem key={index} value={item.id}>{item.name}</MenuItem>
            );
        });
    }

    renderDomainSelector = () => {
        return (
            <FormControl fullWidth={true}>
                <InputLabel>Domain</InputLabel>
                <Select
                    fullWidth={true}
                    value={this.state.domainSelected || ''}
                    onChange={(e) => this.setState({ domainSelected: e.target.value })}
                    input={<Input value={this.state.domainSelected} fullWidth={true} />}
                >
                    {this.renderDomainItems()}
                </Select>
            </FormControl>
        );
    }

    renderComponent = () => {
        if ([undefined, null].includes(this.state.domainSelected) ||
            [undefined, null].includes(this.state.show)) {
                return null;
        }
        switch (this.state.show) {
            case 'machines_description':
                // TODO: Was no data available...
                return null;
            case 'users_description':
                return (
                    <AnomalyUserDescriptions domain={this.state.domainSelected} />
                );
            case 'machines_domainmismatch':
                return (
                    <AnomalyDomainMismatch domain={this.state.domainSelected} />
                );
            case 'machines_outdatedos':
                return (
                    <AnomalyOutdatedOS domain={this.state.domainSelected} />
                );
            case 'machines_smbsign':
                return (
                    <AnomalySMBSigning domain={this.state.domainSelected} />
                );
            case 'machines_users':
                return (
                    <AnomalyUserAccounts domain={this.state.domainSelected} />
                );
            default:
                return null;
        }
    }

    renderAnomalyItems = () => {
        return anomalies.map((item, index) => {
            return (
                <MenuItem key={index} value={item.key}>{item.name}</MenuItem>
            );
        });
    }

    renderAnomalySelector = () => {
        return (
            <FormControl fullWidth={true}>
                <InputLabel>Anomaly</InputLabel>
                <Select
                    fullWidth={true}
                    value={this.state.show || ''}
                    onChange={ (e) => this.selectAnomaly(e.target.value) }
                    input={<Input value={this.state.show} fullWidth={true} />}
                >
                    {this.renderAnomalyItems()}
                </Select>
            </FormControl>
        );
    }

    render() {
        const { classes, theme } = this.props;

        return (
            <Paper className="mbox pbox">
                <VBox>
                    <Box className="margin-bottom" justifyContent="flex-start" alignContent="center" alignItems="center">
                        <Box flex={1} className="mbox">{this.renderAnomalySelector()}</Box>
                        <Box flex={1} className="mbox">{this.renderDomainSelector()}</Box>
                    </Box>
                    <VBox>
                        {this.renderComponent()}
                    </VBox>
                </VBox>
            </Paper>
        );
    }
}

const mapStateToProps = (state) => {
    return {}
}

const mapDispatchToProps = (dispatch) => {
    return {
        notifyUser: (payload) => { dispatch(actions.notifyUser(payload)) }
    }
}

const Anomalies = connect(mapStateToProps, mapDispatchToProps)(withStyles(styles, { withTheme: true })(AnomaliesComponent));
export default Anomalies;
