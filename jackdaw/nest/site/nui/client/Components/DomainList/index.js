import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';
const moment = require('moment');
import { 
    Button, Table, TableRow, TableBody, TableCell,
    TableHead, Typography
} from '@material-ui/core';

import ApiClient from '../ApiClient';

import * as actions from '../../Store/actions';

const styles = theme => ({
    not_selected: {
        cursor: 'pointer'
    },
    selected: {
        backgroundColor: '#212121',
        cursor: 'pointer'
    }
});

class DomainListComponent extends ApiClient {

    state = {
        domains: [],
        selectedDomain: null
    }

    componentDidMount = async() => {
        let domainList = await this.apiFetch('/domain/list');
        if ([undefined, null, false].includes(domainList)) return null;
        this.setState({
            domains: domainList.data
        });
    }

    generateGraph = async(id) => {
        const result = await this.apiCreate(`/graph?adids=${id}`);
        if ([undefined, null, false].includes(result)) return null;
        if (result.status != 200) {
            this.props.notifyUser({
                severity: 'error',
                message: 'Graph generation failed.'
            });
            return;
        }
        this.props.notifyUser({
            severity: 'success',
            message: 'Graph generated.'
        });
    }

    isSelectedDomain = (id) => {
        const { classes } = this.props;
        if (id == this.state.selectedDomain) {
            return classes.selected;
        } else {
            return classes.not_selected;
        }
    }

    selectDomain = (id) => {
        if (this.state.selectedDomain == id) {
            this.props.select(null);
            this.setState({ selectedDomain: null });
        } else {
            this.props.select(id);
            this.setState({ selectedDomain: id })
        }
    }

    renderDomains = () => {
        return this.state.domains.map(row => {
            return (
                <TableRow
                    className={this.isSelectedDomain(row[0])}
                    key={row[0]}
                >
                    <TableCell onClick={ (e) => this.selectDomain(row[0]) }>
                        {row[0]}
                    </TableCell>
                    <TableCell onClick={ (e) => this.selectDomain(row[0]) }>
                        {row[1]}
                    </TableCell>
                    <TableCell onClick={ (e) => this.selectDomain(row[0]) }>
                        {moment(row[2]).format('YYYY/MM/DD HH:mm:ss')}
                    </TableCell>
                    <TableCell align="right">
                        <Button
                            color="primary"
                            variant="contained"
                            onClick={(e) => this.generateGraph(row[0])}
                        >
                            Generate Graph
                        </Button>
                    </TableCell>
                </TableRow>
            );
        });
    }

    renderDomainList = () => {
        if (this.state.domains.length == 0) {
            return (
                <Typography>There are no domains available.</Typography>
            );
        }
        return (
            <Table className="margin-top">
                <TableHead>
                    <TableRow>
                        <TableCell>ID</TableCell>     
                        <TableCell>Name</TableCell>
                        <TableCell>Date</TableCell>
                        <TableCell></TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {this.renderDomains()}
                </TableBody>
            </Table>
        );
    }

    render() {
        return (
            <VBox>
                {this.renderDomainList()}
            </VBox>
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

const DomainList = connect(mapStateToProps, mapDispatchToProps)(withStyles(styles, { withTheme: true })(DomainListComponent));
export default DomainList;
