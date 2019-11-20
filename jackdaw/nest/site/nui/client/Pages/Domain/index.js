'use strict';

import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';

import { Tab, Tabs, Typography } from '@material-ui/core';

import GroupWork from '@material-ui/icons/GroupWork';
import SupervisedUserCircle from '@material-ui/icons/SupervisedUserCircle';
import Computer from '@material-ui/icons/Computer';

import DomainList from '../../Components/DomainList';
import UserList from '../../Components/UserList';
import MachineList from '../../Components/MachineList';

import {
    Paper
} from '@material-ui/core';

import ApiClient from '../../Components/ApiClient';

const styles = theme => ({
});

class DomainComponent extends ApiClient {

    state = {
        tab: 0,
        domain: null
    }

    handleChange = (event, newValue) => {
        this.setState({ tab: newValue });
    };
    
    updateDomain = (id) => {
        this.setState({ domain: id });
    }
    
    renderDomainList = () => {
        return (
            <VBox>
                <Typography variant="h5">Domains</Typography>
                <DomainList select={this.updateDomain} />
            </VBox>
        );
    }

    renderUserList = () => {
        if ([undefined, null].includes(this.state.domain)) {
            return (
                <VBox className="mbox pbox">
                    <Typography>
                        Select a domain above to see the list of users.
                    </Typography>
                </VBox>
            );
        }
        return (
            <VBox className="margin-top">
                <UserList domain={this.state.domain} />
            </VBox>
        );
    }

    renderMachineList = () => {
        if ([undefined, null].includes(this.state.domain)) {
            return (
                <VBox className="mbox pbox">
                    <Typography>
                        Select a domain above to see the list of computers.
                    </Typography>
                </VBox>
            );
        }
        return (
            <VBox className="margin-top">
                <MachineList domain={this.state.domain} />
            </VBox>
        );
    }

    handleTabChange = (event, newValue) => {
        this.setState({ tab: newValue });
    };

    renderTabs = () => {
        if ([undefined, null].includes(this.state.domain)) return null;
        return (
            <VBox className="margin-top">
                <Tabs
                    value={this.state.tab}
                    onChange={this.handleTabChange}
                    variant="fullWidth"
                    indicatorColor="secondary"
                    textColor="secondary"
                    aria-label="icon label tabs"
                >
                    <Tab icon={<SupervisedUserCircle />} label="Users" />
                    <Tab icon={<Computer />} label="Machines" />
                </Tabs>
                <VBox>
                    {this.state.tab == 0 && this.renderUserList()}
                    {this.state.tab == 1 && this.renderMachineList()}
                </VBox>
            </VBox>
        );
    }

    render() {
        const { classes, theme } = this.props;

        return (
            <Paper className="mbox pbox">
                <VBox>
                    {this.renderDomainList()}
                    {this.renderTabs()}
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

const Domain = connect(mapStateToProps, mapDispatchToProps)(withStyles(styles, { withTheme: true })(DomainComponent));
export default Domain;
