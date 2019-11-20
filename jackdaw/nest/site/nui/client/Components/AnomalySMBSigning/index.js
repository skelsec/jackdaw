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

class AnomalySMBSigningComponent extends ApiClient {

    state = {
        data: []
    }

    componentDidMount = async() => {
        let result = await this.apiFetch(`/anomalies/${this.props.domain}/computer/smbsig`);
        if ([undefined, null, false].includes(result)) return null;
        this.setState({
            data: result.data
        });
    }

    renderItems = () => {
        return this.state.data.map((item, index) => {
            return (
                <TableRow
                    key={index}
                >
                    <TableCell>
                        {item.id}
                    </TableCell>
                    <TableCell>
                        {item.name}
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
                            <TableCell>Machine ID</TableCell>
                            <TableCell>Machine Name</TableCell>
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

const AnomalySMBSigning = connect(mapStateToProps, mapDispatchToProps)(withStyles(styles, { withTheme: true })(AnomalySMBSigningComponent));
export default AnomalySMBSigning;
