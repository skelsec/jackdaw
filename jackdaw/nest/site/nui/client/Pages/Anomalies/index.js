'use strict';

import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';

import {
    Paper, FormControl, FormHelperText, Input, InputLabel, 
    Select, MenuItem
} from '@material-ui/core';


import ApiClient from '../../Components/ApiClient';
import SplitButton from '../../Components/SplitButton';
import OutlinedDomainSelector from '../../Components/OutlinedDomainSelector';

import * as actions from '../../Store/actions';

const styles = theme => ({
});

class AnomaliesComponent extends ApiClient {

    state = {
        domains: [],
        domainSelected: null,
        show: null
    }
    
    componentDidMount = async() => {
        const result = await this.apiFetch('/domain/list');
        if ([undefined, null, false].includes(result)) return;
        if (result.status != 200) {
            this.props.notifyUser({
                severity: 'error',
                message: 'Failed to load domains.'
            });
            return;
        }
        const objectDomains = result.data.map(item => {
            return {
                id: item[0],
                name: item[1],
                date: item[2]
            }
        });
        this.setState({ domains: objectDomains });
    }

    selectAnomaly = (type) => {
        this.setState({ show: type });
    }


    renderDomainSelector = () => {
        if ([undefined, null].includes(this.state.show)) return null;
        return (
            <Box style={{ minWidth: 300 }} className="margin-left">
                <OutlinedDomainSelector
                    label="Domain"
                    options={this.state.domains}
                    selection={this.state.domainSelected}
                    onChange={(e) => this.setState({ domainSelected: e.target.value })}
                />
            </Box>
        );
    }

    render() {
        const { classes, theme } = this.props;

        return (
            <Paper className="mbox pbox">
                <VBox>
                    <Box className="margin-bottom" justifyContent="flex-start" alignContents="center" alignItems="center">
                        <SplitButton
                            update={this.selectAnomaly}
                        />
                        {this.renderDomainSelector()}
                    </Box>
                    <VBox>
                        
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
