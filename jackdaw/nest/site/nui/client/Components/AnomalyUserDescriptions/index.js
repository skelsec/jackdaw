import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';
const moment = require('moment');
import { 
    Table, TableRow, TableBody, TableCell,
    TableHead, IconButton, TableFooter, TablePagination
} from '@material-ui/core';

import { makeStyles, useTheme } from '@material-ui/core/styles';
import FirstPageIcon from '@material-ui/icons/FirstPage';
import KeyboardArrowLeft from '@material-ui/icons/KeyboardArrowLeft';
import KeyboardArrowRight from '@material-ui/icons/KeyboardArrowRight';
import LastPageIcon from '@material-ui/icons/LastPage';

import ApiClient from '../ApiClient';

const styles = theme => ({
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

class AnomalyUserDescriptionsComponent extends ApiClient {

    state = {
        data: [],
        currentPage: 0,
        perPage: 50,
        total: 0
    }

    componentDidMount = async() => {
        await this.fetch(this.state.currentPage);
    }

    fetch = async(page) => {
        let result = await this.apiFetch(`/anomalies/${this.props.domain}/users/description?page=${page + 1}&maxcnt=${this.state.perPage}`);
        if ([undefined, null, false].includes(result)) return null;
        this.setState({
            data: result.data.res,
            total: result.data.page.total
        });
    }

    setCurrentPage = (event, pageNumber) => {
        this.setState({ currentPage: pageNumber });
        this.fetch(pageNumber);
    }

    handlePerPageSelectChange = (e) => {
        this.setState({ perPage: e.target.value }, () => this.fetch(this.state.currentPage));
    }

    renderItems = () => {
        return this.state.data.map((row, index) => {
            return (
                <TableRow
                    key={index}
                >
                    <TableCell>
                        {row.userid}
                    </TableCell>
                    <TableCell>
                        {row.username}
                    </TableCell>
                    <TableCell>
                        {row.description}
                    </TableCell>
                </TableRow>
            );
        });
    }

    render() {
        return (
            <VBox>
                <Table className="margin-top">
                    <TableHead>
                        <TableRow>
                            <TableCell>User ID</TableCell>     
                            <TableCell>User Name</TableCell>
                            <TableCell>Description</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {this.renderItems()}
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

const AnomalyUserDescriptions = connect(mapStateToProps, mapDispatchToProps)(withStyles(styles, { withTheme: true })(AnomalyUserDescriptionsComponent));
export default AnomalyUserDescriptions;
