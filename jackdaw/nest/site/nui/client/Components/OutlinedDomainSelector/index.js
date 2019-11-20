'use strict';

import React from 'react';
import { connect } from 'react-redux';
import { FormControl, InputLabel, MenuItem, Select } from '@material-ui/core';

class OutlinedDomainSelectorComponent extends React.Component {

    renderMenuItems = () => {
        return this.props.options.map((item, index) => {
            return (<MenuItem key={index} value={item.id}>{item.name}</MenuItem>);
        });
    }

    render() {
        return (
            <FormControl className='item-selector' fullWidth={true}>
                <Select
                    fullWidth={true}
                    disableUnderline
                    value={this.props.selection || 'none'}
                    onChange={ (e) => this.props.onChange(e) }
                    inputProps={{
                        name: 'value'
                    }}
                >
                    <MenuItem value="none" disabled>
                        <em>Select Domain...</em>
                    </MenuItem>
                    {this.renderMenuItems()}
                </Select>
            </FormControl>
        );
    }
}

const mapStateToProps = (state) => {
    return {
    }
}

const mapDispatchToProps = (dispatch) => {
    return {
    }
}

const OutlinedDomainSelector = connect(mapStateToProps, mapDispatchToProps)(OutlinedDomainSelectorComponent);
export default OutlinedDomainSelector;
