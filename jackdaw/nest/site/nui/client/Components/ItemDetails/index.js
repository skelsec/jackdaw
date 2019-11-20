import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';
const moment = require('moment');
import { 
    Table, TableRow, TableBody, TableCell,
    TableHead, Typography, Paper
} from '@material-ui/core';

import ApiClient from '../ApiClient';

const styles = theme => ({
});

// this.props.domain
// this.props.type
// this.props.selection

class ItemDetailsComponent extends ApiClient {

    state = {
        data: null
    }

    componentDidMount = async() => {
        await this.fetchData();
    }

    fetchData = async() => {
        const uri = `/${this.props.type}/${this.props.domain}/by_id/${this.props.selection[0]}`;
        let result = await this.apiFetch(uri);
        if ([undefined, null, false].includes(result)) return null;
        if (result.status != 200) {
            return;
        }
        this.setState({
            data: result.data
        });
    }

    componentDidUpdate = async(prevProps) => {
        let refetch = 0;
        if (this.props.domain !== prevProps.domain) {
            refetch++;
        }
        if (this.props.type !== prevProps.type) {
            refetch++;
        }
        if (this.props.selection !== prevProps.selection) {
            refetch++;
        }
        if (refetch > 0) {
            await this.fetchData();
        }
    }

    formatValue = (value) => {
        switch (value) {
            case undefined:
            case null:
                return 'N/A'
                break;
            case false:
                return 'False';
            case true:
                return 'True';
            default:
                return value.toString();
        }
    }

    renderDataItems = () => {
        return Object.keys(this.state.data).map((key, index) => {
            return (
                <TableRow
                    key={index}
                >
                    <TableCell>
                        {key}
                    </TableCell>
                    <TableCell>
                        {this.formatValue(this.state.data[key])}
                    </TableCell>
                </TableRow>
            );
        })
    }

    renderData = () => {
        return (
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell>Attribute</TableCell>     
                        <TableCell>Value</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {this.renderDataItems()}
                </TableBody>
            </Table>
        );
    }

    render() {
        if ([undefined, null].includes(this.state.data)) {
            return (
                <VBox>
                    <Typography>
                        No data available.
                    </Typography>
                </VBox>
            );
        }
        return (
            <Paper style={{ backgroundColor: '#2a2a2a' }}>
                <VBox>
                    {this.renderData()}
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

const ItemDetails = connect(mapStateToProps, mapDispatchToProps)(withStyles(styles, { withTheme: true })(ItemDetailsComponent));
export default ItemDetails;
