import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';
const moment = require('moment');
import { 
    Table, TableRow, TableBody, TableCell,
    TableHead
} from '@material-ui/core';

import ApiClient from '../ApiClient';

const styles = theme => ({
});

class AnomalyUserDescriptionsComponent extends ApiClient {

    state = {
        data: []
    }

    componentDidMount = async() => {
        let result = await this.apiFetch(`/anomalies/${this.props.domain}/users/description`);
        if ([undefined, null, false].includes(result)) return null;
        this.setState({
            data: result.data
        });
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
