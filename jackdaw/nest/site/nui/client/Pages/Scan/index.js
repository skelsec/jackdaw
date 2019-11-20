'use strict';

import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';

import { 
    Paper, Button, Select, TextField
} from '@material-ui/core';

import ApiClient from '../../Components/ApiClient';

import * as actions from '../../Store/actions';

const styles = theme => ({
});

class ScanComponent extends ApiClient {

    state = {
        ldap_url: '',
        ldap_workers: 1,
        smb_url: '',
        smb_workers: 1
    }

    renderTextField = (type, label, description, name) => {
        return (
            <Box className="mbox">
                <TextField
                    type={type}
                    fullWidth={true}
                    helperText={description}
                    label={label}
                    value={this.state[name]}
                    onChange={ (e) => this.setState({ [name]: e.target.value }) }
                />
            </Box>
        );
    }

    startScan = async() => {
        const result = await this.apiCreate('/scans/enum/create', this.state);
        if (result.status == 200) {
            this.props.notifyUser({
                severity: 'success',
                message: 'Scan started.'
            });
        } else {
            this.props.notifyUser({
                severity: 'error',
                message: 'Failed to start scan.'
            });
        }
    }

    render() {
        const { classes, theme } = this.props;

        return (
            <Paper className="mbox pbox">
                <VBox>
                    <VBox className="margin-bottom">
                    {this.renderTextField('text', 'LDAP URL', 'The URL of the LDAP server.', 'ldap_url')}
                    {this.renderTextField('number', 'LDAP Workers', 'The number of LDAP workers.', 'ldap_workers')}
                    {this.renderTextField('text', 'SMB URL', 'The URL of the SMB server.', 'smb_url')}
                    {this.renderTextField('number', 'SMB Workers', 'The number of SMB workers.', 'smb_workers')}
                    </VBox>
                    <Box className="mbox">
                        <Button
                            color="primary"
                            variant="contained"
                            onClick={(e) => this.startScan()}
                        >
                            Scan
                        </Button>
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
    return {
        notifyUser: (payload) => { dispatch(actions.notifyUser(payload)) }
    }
}

const Scan = connect(mapStateToProps, mapDispatchToProps)(withStyles(styles, { withTheme: true })(ScanComponent));
export default Scan;
