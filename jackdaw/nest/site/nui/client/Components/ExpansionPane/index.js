'use strict';

import React from 'react';
import { connect } from 'react-redux';
import { VBox } from 'react-layout-components';
import { ExpansionPanel, ExpansionPanelSummary, ExpansionPanelDetails, Typography } from '@material-ui/core';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';

class ExpansionPaneComponent extends React.Component {

    state = {
    }

    render() {
        return (
            <VBox width="100%">
                <ExpansionPanel expanded={this.props.expanded}>
                    <ExpansionPanelSummary
                        onClick={this.props.onClick}
                        expandIcon={<ExpandMoreIcon />}
                    >
                        <Typography className="exansion-title">{this.props.label}</Typography>
                    </ExpansionPanelSummary>
                    <ExpansionPanelDetails>
                        <VBox fit>
                            <Typography className="margin-bottom">
                                {this.props.description}
                            </Typography>
                            {this.props.children}
                        </VBox>
                    </ExpansionPanelDetails>
                </ExpansionPanel>
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

const ExpansionPane = connect(mapStateToProps, mapDispatchToProps)(ExpansionPaneComponent);
export default ExpansionPane;
