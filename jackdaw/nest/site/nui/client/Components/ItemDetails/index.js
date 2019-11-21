import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';
const moment = require('moment');
import { 
    Table, TableRow, TableBody, TableCell,
    TableHead, Typography, Paper, Tooltip
} from '@material-ui/core';

import ApiClient from '../ApiClient';

const styles = theme => ({
    clipboard: {
        marginLeft: '10px',
        fontSize: '0.8em',
        cursor: 'pointer'
    },
    iconcol: {
        maxWidth: 30
    }
});

import LaunchOutlined from '@material-ui/icons/LaunchOutlined';

import * as actions from '../../Store/actions';

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

    getItemId = () => {
        // This is required as API endpoint are not standardized so they
        // return object IDs in all different ways...
        let idFieldName = 'id';
        if (![undefined, null].includes(this.props.id_field_name)) {
            idFieldName = this.props.id_field_name;
        }
        return this.props.selection[idFieldName];
    }

    getBy = () => {
        if ([undefined, null].includes(this.props.by)) {
            return 'by_id';
        }
        return `by_${this.props.by}`;
    }

    fetchData = async() => {
        const uri = `/${this.props.type}/${this.props.domain}/${this.getBy()}/${this.getItemId()}`;
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
        const { classes } = this.props;
        return Object.keys(this.state.data).map((key, index) => {
            const rid = `item-value-${key}`;
            return (
                <TableRow
                    key={index}
                >
                    <TableCell>
                        {key}
                    </TableCell>
                    <TableCell>
                        <span id={rid}>
                            {this.formatValue(this.state.data[key])}
                        </span>
                    </TableCell>
                    <TableCell className={classes.iconcol}>
                        <Tooltip
                            disableFocusListener
                            disableTouchListener
                            title="Copy Value to Clipboard"
                        >
                            <LaunchOutlined
                                className={classes.clipboard}
                                onClick={ (e) => this.copyToClipboard(rid) }
                            />
                        </Tooltip>
                    </TableCell>
                </TableRow>
            );
        })
    }

    renderData = () => {
        const { classes } = this.props;
        return (
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell>Attribute</TableCell>     
                        <TableCell>Value</TableCell>
                        <TableCell className={classes.iconcol}></TableCell>
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
    return {
        notifyUser: (payload) => { dispatch(actions.notifyUser(payload)) }
    }
}

const ItemDetails = connect(mapStateToProps, mapDispatchToProps)(withStyles(styles, { withTheme: true })(ItemDetailsComponent));
export default ItemDetails;
