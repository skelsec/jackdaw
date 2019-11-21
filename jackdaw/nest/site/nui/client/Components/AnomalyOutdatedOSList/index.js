import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';
const moment = require('moment');
import { 
    Table, TableRow, TableBody, TableCell,
    TableHead, IconButton, 
    TableFooter, TablePagination
} from '@material-ui/core';

import ItemDetails from '../ItemDetails';

import { makeStyles, useTheme } from '@material-ui/core/styles';
import FirstPageIcon from '@material-ui/icons/FirstPage';
import KeyboardArrowLeft from '@material-ui/icons/KeyboardArrowLeft';
import KeyboardArrowRight from '@material-ui/icons/KeyboardArrowRight';
import LastPageIcon from '@material-ui/icons/LastPage';

import ApiClient from '../ApiClient';

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

class AnomalyOutdatedOSListComponent extends ApiClient {

    state = {
        data: [],
        versions: [],
        versionFilter: null,
        currentPage: 0,
        perPage: 50,
        total: 0,
        selected: null
    }

    componentDidMount = async() => {
        if ([undefined, null].includes(this.props.domain)) return null;
        if ([undefined, null].includes(this.props.version)) return null;
        await this.fetch(this.state.currentPage);
    }

    fetch = async(page) => {
        const version = encodeURI(btoa(this.props.version));
        let result = await this.apiFetch(`/anomalies/${this.props.domain}/computer/outdated?version=${version}&page=${page + 1}&maxcnt=${this.state.perPage}`);
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

    isSelected = (item) => {
        const { classes } = this.props;
        if ([undefined, null].includes(this.state.selected)) {
            return classes.not_selected;
        }
        if (item.machineid == this.state.selected.machineid) {
            return classes.selected;
        } else {
            return classes.not_selected;
        }
    }

    select = (item) => {
        if ([undefined, null].includes(this.state.selected)) {
            this.setState({ selected: item })
            return;
        }
        if (this.state.selected.machineid == item.machineid) {
            this.setState({ selected: null });
        } else {
            this.setState({ selected: item })
        }
    }

    renderItems = () => {
        if ([undefined, null].includes(this.state.data)) return null;
        return this.state.data.map((machine, index) => {
            return (
                <TableRow
                    className={this.isSelected(machine)}
                    onClick={ (e) => this.select(machine) }
                    key={index}
                >
                    <TableCell>
                        {machine.machineid}
                    </TableCell>
                    <TableCell>
                        {machine.machinename}
                    </TableCell>
                    <TableCell>
                        {machine.machinesid}
                    </TableCell>
                </TableRow>
            );
        });
    }

    render() {
        if ([undefined, null].includes(this.props.domain)) return null;
        if ([undefined, null].includes(this.props.version)) return null;
        return (
            <Box>
                <Box flex={1}>
                    <Table className="margin-top">
                        <TableHead>
                            <TableRow>
                                <TableCell>Machine ID</TableCell>     
                                <TableCell>Machine Name</TableCell>
                                <TableCell>Machine SID</TableCell>
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
                </Box>
                {this.state.selected && <Box flex={2} className="mbox pbox">
                    <ItemDetails
                        domain={this.props.domain}
                        type="machine"
                        selection={this.state.selected}
                        id_field_name="machineid"
                    />
                </Box>}
            </Box>
        );
    }
}

const mapStateToProps = (state) => {
    return {}
}

const mapDispatchToProps = (dispatch) => {
    return {}
}

const AnomalyOutdatedOSList = connect(mapStateToProps, mapDispatchToProps)(withStyles(styles, { withTheme: true })(AnomalyOutdatedOSListComponent));
export default AnomalyOutdatedOSList;
