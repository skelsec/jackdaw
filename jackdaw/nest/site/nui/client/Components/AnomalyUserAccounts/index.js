import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';
const moment = require('moment');
import { 
    FormControl, InputLabel, Select, MenuItem, Input
} from '@material-ui/core';

import ApiClient from '../ApiClient';
import AnomalyUserATypeList from '../AnomalyUserATypeList';

const styles = theme => ({
});

const anomalies = [
    { type: 'asrep', name: 'No Kerberos Pr-eauthentication'},
    { type: 'desonly', name: 'Kerberos Encryption with DES'},
    { type: 'passnotreq', name: 'No Password Required'},
    { type: 'plaintext', name: 'Plaintext Passwords'},
    { type: 'pwnotexp', name: 'No Password Expiration'}
];

class AnomalyUserAccountsComponent extends ApiClient {

    state = {
        anomalyFilter: null
    }

    renderList = () => {
        return anomalies.map((item, index) => {
            return (
                <MenuItem key={index} value={item.type}>{item.name}</MenuItem>
            );
        });
    }

    renderSelector = () => {
        return (
            <FormControl fullWidth={true}>
                <InputLabel>Anomaly Type</InputLabel>
                <Select
                    fullWidth={true}
                    value={this.state.anomalyFilter || ''}
                    onChange={(e) => this.setState({ anomalyFilter: e.target.value})}
                    input={<Input value={this.state.anomalyFilter} fullWidth={true} />}
                >
                    {this.renderList()}
                </Select>
            </FormControl>
        );
    }

    render() {
        return (
            <VBox>
                <Box className="mbox">
                    {this.renderSelector()}
                </Box>
                {this.state.anomalyFilter && <AnomalyUserATypeList
                    domain={this.props.domain}
                    type={this.state.anomalyFilter}
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

const AnomalyUserAccounts = connect(mapStateToProps, mapDispatchToProps)(withStyles(styles, { withTheme: true })(AnomalyUserAccountsComponent));
export default AnomalyUserAccounts;
