import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';
const moment = require('moment');
import { 
    Table, TableRow, TableBody, TableCell,
    TableHead, TextField, Tooltip
} from '@material-ui/core';

import ApiClient from '../ApiClient';
import ItemDetails from '../ItemDetails';

import LaunchOutlined from '@material-ui/icons/LaunchOutlined';

import * as actions from '../../Store/actions';

const styles = theme => ({
    not_selected: {
        cursor: 'pointer'
    },
    selected: {
        backgroundColor: '#212121',
        cursor: 'pointer'
    },
    clipboard: {
        marginLeft: '10px',
        fontSize: '0.8em',
        cursor: 'pointer'
    }
});

class UserListComponent extends ApiClient {

    state = {
        users: [],
        filter: '',
        selected: null
    }

    componentDidMount = async() => {
        let userList = await this.apiFetch(`/user/${this.props.domain}/list`);
        if ([undefined, null, false].includes(userList)) return null;
        this.setState({
            users: userList.data
        });
    }

    copyToClipboard = (id) => {
        const copyText = document.getElementById(id);
        const textArea = document.createElement("textarea");
        textArea.value = copyText.textContent;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand("Copy");
        textArea.remove();
        this.props.notifyUser({
            severity: 'success',
            message: 'Copied to clipboard.'
        });
    }

    isSelected = (item) => {
        const { classes } = this.props;
        if ([undefined, null].includes(this.state.selected)) {
            return classes.not_selected;
        }
        if (item[0] == this.state.selected[0]) {
            return classes.selected;
        } else {
            return classes.not_selected;
        }
    }

    selectUser = (item) => {
        if ([undefined, null].includes(this.state.selected)) {
            this.setState({ selected: item })
            return;
        }
        if (this.state.selected[0] == item[0]) {
            this.setState({ selected: null });
        } else {
            this.setState({ selected: item })
        }
    }

    renderUsers = () => {
        const { classes } = this.props;
        return this.state.users.map(row => {
            if (this.state.filter != '' && !row[2].includes(this.state.filter)) {
                return null;
            }
            const rid = `domain-user-${row[0]}`;
            return (
                <TableRow
                    className={this.isSelected(row)}
                    key={row[0]}
                >
                    <TableCell onClick={ (e) => this.selectUser(row) }>
                        {row[0]}
                    </TableCell>
                    <TableCell onClick={ (e) => this.selectUser(row) }>
                        {row[2]}
                    </TableCell>
                    <TableCell onClick={ (e) => this.selectUser(row) }>
                        <span id={rid}>{row[1]}</span>
                    </TableCell>
                    <TableCell>
                        <Tooltip
                            disableFocusListener
                            disableTouchListener
                            title="Copy SID to Clipboard"
                        >
                            <LaunchOutlined
                                className={classes.clipboard}
                                onClick={ (e) => this.copyToClipboard(rid) }
                            />
                        </Tooltip>
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
                <Box>
                    <Box flex={1}>
                        <Table className="margin-top">
                            <TableHead>
                                <TableRow>
                                    <TableCell>ID</TableCell>     
                                    <TableCell>Name</TableCell>
                                    <TableCell>SID</TableCell>
                                    <TableCell></TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {this.renderUsers()}
                            </TableBody>
                        </Table>
                    </Box>
                    {this.state.selected && <Box flex={3} className="mbox pbox">
                        <ItemDetails
                            domain={this.props.domain}
                            type="user"
                            selection={this.state.selected}
                        />
                    </Box>}
                </Box>
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

const UserList = connect(mapStateToProps, mapDispatchToProps)(withStyles(styles, { withTheme: true })(UserListComponent));
export default UserList;
