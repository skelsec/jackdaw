import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';
const moment = require('moment');
import { 
    Table, TableRow, TableBody, TableCell,
    TableHead, TextField, Tooltip, IconButton,
    TableFooter, TablePagination
} from '@material-ui/core';

import ApiClient from '../ApiClient';
import ItemDetails from '../ItemDetails';

import { makeStyles, useTheme } from '@material-ui/core/styles';
import FirstPageIcon from '@material-ui/icons/FirstPage';
import KeyboardArrowLeft from '@material-ui/icons/KeyboardArrowLeft';
import KeyboardArrowRight from '@material-ui/icons/KeyboardArrowRight';
import LastPageIcon from '@material-ui/icons/LastPage';
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

const useStyles1 = makeStyles(theme => ({
    root: {
      flexShrink: 0,
      marginLeft: theme.spacing(2.5),
    },
}));

function TablePaginationActions(props) {
    const classes = useStyles1();
    const theme = useTheme();
    const { count, page, rowsPerPage, onChangePage } = props;
  
    const handleFirstPageButtonClick = event => {
      onChangePage(event, 0);
    };
  
    const handleBackButtonClick = event => {
      onChangePage(event, page - 1);
    };
  
    const handleNextButtonClick = event => {
      onChangePage(event, page + 1);
    };
  
    const handleLastPageButtonClick = event => {
      onChangePage(event, Math.max(0, Math.ceil(count / rowsPerPage) - 1));
    };
  
    return (
        <div className={classes.root}>
            <IconButton
                onClick={handleFirstPageButtonClick}
                disabled={page === 0}
                aria-label="first page"
            >
                {theme.direction === 'rtl' ? <LastPageIcon /> : <FirstPageIcon />}
            </IconButton>
            <IconButton onClick={handleBackButtonClick} disabled={page === 0} aria-label="previous page">
                {theme.direction === 'rtl' ? <KeyboardArrowRight /> : <KeyboardArrowLeft />}
            </IconButton>
            <IconButton
                onClick={handleNextButtonClick}
                disabled={page >= Math.ceil(count / rowsPerPage) - 1}
                aria-label="next page"
            >
                {theme.direction === 'rtl' ? <KeyboardArrowLeft /> : <KeyboardArrowRight />}
            </IconButton>
            <IconButton
                onClick={handleLastPageButtonClick}
                disabled={page >= Math.ceil(count / rowsPerPage) - 1}
                aria-label="last page"
            >
                {theme.direction === 'rtl' ? <FirstPageIcon /> : <LastPageIcon />}
            </IconButton>
        </div>
    );
}

class UserListComponent extends ApiClient {

    state = {
        users: [],
        filter: '',
        selected: null,
        currentPage: 0,
        perPage: 50,
        total: 0
    }

    componentDidMount = async() => {
        await this.fetch(this.state.currentPage);
    }

    fetch = async(page) => {
        let userList = await this.apiFetch(`/user/${this.props.domain}/list?page=${page + 1}&maxcnt=${this.state.perPage}`);
        if ([undefined, null, false].includes(userList)) return null;
        this.setState({
            users: userList.data.res,
            total: userList.data.page.total
        });
    }

    setCurrentPage = (event, pageNumber) => {
        this.setState({ currentPage: pageNumber });
        this.fetch(pageNumber);
    }

    handlePerPageSelectChange = (e) => {
        this.setState({ perPage: e.target.value }, () => this.fetch(this.state.currentPage));
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
        if (item.id == this.state.selected.id) {
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
        if (this.state.selected.id == item.id) {
            this.setState({ selected: null });
        } else {
            this.setState({ selected: item })
        }
    }

    renderUsers = () => {
        const { classes } = this.props;
        return this.state.users.map(row => {
            if (this.state.filter != '' && !row.name.includes(this.state.filter)) {
                return null;
            }
            const rid = `domain-user-${row.id}`;
            return (
                <TableRow
                    className={this.isSelected(row)}
                    key={row.id}
                >
                    <TableCell onClick={ (e) => this.selectUser(row) }>
                        {row.id}
                    </TableCell>
                    <TableCell onClick={ (e) => this.selectUser(row) }>
                        {row.name}
                    </TableCell>
                    <TableCell onClick={ (e) => this.selectUser(row) }>
                        <span id={rid}>{row.sid}</span>
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
                            <TableFooter>
                                <TableRow>
                                    <TablePagination
                                        rowsPerPageOptions={[10, 20, 50, 100]}
                                        colSpan={4}
                                        count={this.state.total}
                                        rowsPerPage={this.state.perPage}
                                        page={this.state.currentPage}
                                        SelectProps={{
                                            inputProps: { 'aria-label': 'rows per page' },
                                            native: true,
                                        }}
                                        onChangePage={this.setCurrentPage}
                                        onChangeRowsPerPage={this.handlePerPageSelectChange}
                                        ActionsComponent={TablePaginationActions}
                                    />
                                </TableRow>
                            </TableFooter>
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
