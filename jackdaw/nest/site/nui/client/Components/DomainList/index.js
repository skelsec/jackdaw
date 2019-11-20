import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';
const moment = require('moment');
import { 
    Button, Table, TableRow, TableBody, TableCell,
    TableHead, Typography, TableFooter, TablePagination,
    IconButton
} from '@material-ui/core';

import { makeStyles, useTheme } from '@material-ui/core/styles';
import FirstPageIcon from '@material-ui/icons/FirstPage';
import KeyboardArrowLeft from '@material-ui/icons/KeyboardArrowLeft';
import KeyboardArrowRight from '@material-ui/icons/KeyboardArrowRight';
import LastPageIcon from '@material-ui/icons/LastPage';

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

class DomainListComponent extends ApiClient {

    state = {
        domains: [],
        selectedDomain: null,
        currentPage: 0,
        perPage: 10,
        total: 0
    }

    componentDidMount = async() => {
        await this.getDomains(this.state.currentPage);
    }

    getDomains = async(page) => {
        let domainList = await this.apiFetch(`/domain/list?page=${page + 1}&maxcnt=${this.state.perPage}`);
        if ([undefined, null, false].includes(domainList)) return null;
        this.setState({
            domains: domainList.data.res,
            total: domainList.data.page.total
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
                    className={this.isSelectedDomain(row.id)}
                    key={row.id}
                >
                    <TableCell onClick={ (e) => this.selectDomain(row.id) }>
                        {row.id}
                    </TableCell>
                    <TableCell onClick={ (e) => this.selectDomain(row.id) }>
                        {row.name}
                    </TableCell>
                    <TableCell onClick={ (e) => this.selectDomain(row.id) }>
                        {moment(row.creation).format('YYYY/MM/DD HH:mm:ss')}
                    </TableCell>
                    <TableCell align="right">
                        <Button
                            color="primary"
                            variant="contained"
                            onClick={(e) => this.generateGraph(row.id)}
                        >
                            Generate Graph
                        </Button>
                    </TableCell>
                </TableRow>
            );
        });
    }

    setCurrentPage = (event, pageNumber) => {
        this.setState({ currentPage: pageNumber });
        this.getDomains(pageNumber);
    }

    handleDomainsPerPageSelectChange = (e) => {
        this.setState({ perPage: e.target.value }, () => this.getDomains(this.state.currentPage));
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
                            onChangeRowsPerPage={this.handleDomainsPerPageSelectChange}
                            ActionsComponent={TablePaginationActions}
                        />
                    </TableRow>
                </TableFooter>
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
